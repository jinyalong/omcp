import os
import json
import logging
import requests
import time
import hmac
import hashlib
import platform
import subprocess
import uuid
from typing import Dict, Any, Optional
from rich.prompt import Confirm
from rich.console import Console
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)
console = Console()

class Analytics:
    _instance = None

    def __new__(cls, config_manager):
        if cls._instance is None:
            cls._instance = super(Analytics, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, config_manager):
        if not self.initialized:
            self.config_manager = config_manager
            # Use production URL by default, fallback to localhost for development
            self.analytics_url = os.environ.get('MCP_ANALYTICS_URL', 'https://mcpservers.cn/api/analytics')
            if os.environ.get('MCP_DEV_MODE') == 'true':
                self.analytics_url = 'http://localhost:8000/api/analytics'
            self.secret_key: Optional[str] = None
            self.secret_key_expiry: Optional[int] = None
            self.initialized = True
            self._load_cached_key()
            self._ensure_device_info()

    def _load_cached_key(self) -> None:
        """Load cached key from preferences"""
        prefs = self.config_manager.read_preferences()
        cached_key = prefs.get('secret_key', {})
        if cached_key and isinstance(cached_key, dict) and cached_key.get('key') and cached_key.get('expiry'):
            # If the key is stored as a JSON string, parse it
            if isinstance(cached_key['key'], str) and cached_key['key'].startswith('{'):
                try:
                    key_data = json.loads(cached_key['key'])
                    self.secret_key = key_data['key']
                except json.JSONDecodeError:
                    self.secret_key = cached_key['key']
            else:
                self.secret_key = cached_key['key']
            self.secret_key_expiry = cached_key['expiry']

    def _is_key_valid(self) -> bool:
        """Check if the current key is valid"""
        if not self.secret_key or not self.secret_key_expiry:
            return False
        current_time = int(time.time() * 1000)
        return current_time < self.secret_key_expiry

    def _get_secret_key(self) -> str:
        """Get the current secret key, fetching from server only if needed"""
        if self._is_key_valid():
            return self.secret_key
            
        # Fetch new key from server
        try:
            response = requests.get(
                f"{self.analytics_url}/key",
                timeout=10
            )
            response.raise_for_status()
            
            # Parse the JSON response
            key_data = response.json()
            
            if not key_data.get('key') or not key_data.get('expiresAt'):
                raise ValueError("Invalid key response format")
                
            # Set the key and expiry
            self.secret_key = key_data['key']  # Store only the key value
            self.secret_key_expiry = key_data['expiresAt']
            
            # Cache the key in preferences
            prefs = self.config_manager.read_preferences()
            prefs['secret_key'] = {
                'key': self.secret_key,  # Store only the key value
                'expiry': self.secret_key_expiry
            }
            self.config_manager.write_preferences(prefs)
            
            return self.secret_key
            
        except Exception as e:
            logger.error(f"Failed to fetch secret key: {str(e)}")
            if self.secret_key:  # Use cached key as fallback
                return self.secret_key
            raise

    def _get_device_info(self) -> Dict[str, str]:
        """Get device information"""
        prefs = self.config_manager.read_preferences()
        
        # Check if we already have device info
        if 'device_info' in prefs:
            device_info = prefs['device_info']
            # Ensure device_version is included
            if 'device_version' not in device_info:
                device_info['device_version'] = platform.version()
                # Update preferences with the new field
                prefs['device_info'] = device_info
                self.config_manager.write_preferences(prefs)
            return device_info
            
        # Collect system information
        system_info = {
            'platform': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'hostname': platform.node(),
            'device_version': platform.version()
        }
        
        # Try to get MAC address
        try:
            if platform.system() == 'Darwin':  # macOS
                mac = subprocess.check_output(['ifconfig', 'en0']).decode()
                mac = mac.split('ether')[1].split()[0] if 'ether' in mac else ''
            elif platform.system() == 'Linux':
                mac = subprocess.check_output(['cat', '/sys/class/net/eth0/address']).decode().strip()
            else:  # Windows
                mac = subprocess.check_output(['getmac']).decode().split('\n')[0].strip()
            system_info['mac'] = mac
        except:
            system_info['mac'] = 'unknown'
            
        # Save the device info
        prefs['device_info'] = system_info
        self.config_manager.write_preferences(prefs)
        
        return system_info

    def _ensure_device_info(self) -> None:
        """Ensure device information is available"""
        self._get_device_info()

    def _generate_signature(self, timestamp: str, nonce: str) -> str:
        """Generate signature for authentication"""
        device_info = self._get_device_info()
    
        # 只对 device_info 的键进行排序
        sorted_device_info = dict(sorted(device_info.items()))
    
        # 构建消息对象
        message = {
            'device_info': sorted_device_info,
            'timestamp': timestamp,
            'nonce': nonce
        }
    
        # 直接使用 json.dumps 序列化整个消息，并移除所有空格
        message_str = json.dumps(message, separators=(',', ':'))
    
        # Get current secret key
        try:
            secret_key = self._get_secret_key()
        except Exception as e:
            logger.error(f"Failed to get secret key: {str(e)}")
            if self.secret_key:  # Use cached key as fallback
                secret_key = self.secret_key
            else:
                raise
            
        # 将密钥从十六进制字符串转换为字节
        key_bytes = bytes.fromhex(secret_key)
        
        # Generate signature using HMAC-SHA256
        signature = hmac.new(
            key_bytes,  # 使用转换后的字节作为密钥
            message_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature

    def _generate_auth_headers(self) -> Dict[str, str]:
        """Generate authentication headers for API requests"""
        timestamp = str(int(time.time() * 1000))
        nonce = str(uuid.uuid4())  # Use UUID for better randomness
        
        # Generate signature
        device_info = self._get_device_info()
        signature = self._generate_signature(timestamp, nonce)
        
        headers = {
            "x-device-info": json.dumps(device_info),
            "x-timestamp": timestamp,
            "x-nonce": nonce,
            "x-signature": signature
        }
        
        return headers

    def check_consent(self) -> bool:
        """Check if user has given consent for analytics"""
        prefs = self.config_manager.read_preferences()
        
        if isinstance(prefs.get("allow_analytics"), bool):
            return prefs["allow_analytics"]
        
        if os.environ.get("CI") == "true":
            self.config_manager.write_preferences({
                **prefs,
                "allow_analytics": False
            })
            return False
        
        allow = Confirm.ask(
            "Would you like to help improve omcp by sharing anonymous installation analytics?",
            default=True
        )
        
        self.config_manager.write_preferences({
            **prefs,
            "allow_analytics": allow
        })
        
        return allow

    def track_installation(self, package_name: str, package_info: Dict[str, Any]) -> None:
        """Track package installation"""
        if not self.check_consent():
            return
            
        try:
            device_info = self._get_device_info()
            
            analytics_data = {
                "packageName": package_name,
                "version": package_info.get("version", "1.0.0"),
                "runtime": package_info.get("runtime", "python"),
                "os": os.name,
                "architecture": os.uname().machine if hasattr(os, "uname") else "unknown",
                "device_info": device_info
            }
            
            headers = self._generate_auth_headers()
            response = requests.post(
                f"{self.analytics_url}/install",
                json=analytics_data,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            
        except requests.exceptions.Timeout:
            logger.error("Analytics request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send analytics: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while tracking installation: {str(e)}")

    def track_uninstallation(self, package_name: str) -> None:
        """Track package uninstallation"""
        if not self.check_consent():
            return
            
        try:
            prefs = self.config_manager.read_preferences()
            installed_packages = prefs.get("installed_packages", {})
            package_info = installed_packages.get(package_name, {})
            device_info = self._get_device_info()
            
            analytics_data = {
                "packageName": package_name,
                "version": package_info.get("version", "1.0.0"),
                "runtime": package_info.get("runtime", "python"),
                "os": os.name,
                "architecture": os.uname().machine if hasattr(os, "uname") else "unknown",
                "device_info": device_info
            }
            
            headers = self._generate_auth_headers()
            response = requests.post(
                f"{self.analytics_url}/uninstall",
                json=analytics_data,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            
        except requests.exceptions.Timeout:
            logger.error("Analytics request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send analytics: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while tracking uninstallation: {str(e)}")

    def initialize(self) -> None:
        """Initialize analytics if not already initialized"""
        if not self.secret_key:
            self._ensure_device_info()
            self._get_secret_key() 