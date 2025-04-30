import os
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
import platform
from rich.prompt import Prompt, Confirm
from rich.console import Console
from .configuration_handler import ConfigurationHandler
from .client_integration import ClientIntegrationManager

logger = logging.getLogger(__name__)
console = Console()

@dataclass
class PackageConfig:
    """Configuration handler for a specific package"""
    name: str
    description: str
    handler: Callable[[str], Dict[str, Any]]

@dataclass
class MCPServer:
    runtime: str  # 'node' or 'python'
    command: Optional[str] = None
    args: Optional[list] = None
    env: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, omitting None values and empty env"""
        result = {
            'runtime': self.runtime
        }
        if self.command is not None:
            result['command'] = self.command
        if self.args is not None:
            result['args'] = self.args
        if self.env is not None and self.env:  # Only add env if it's not None and not empty
            result['env'] = self.env
        return result

@dataclass
class MCPConfig:
    """Main configuration for MCP Server Manager"""
    servers: Dict[str, MCPServer]
    preferences: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'servers': {
                name: server.to_dict()
                for name, server in self.servers.items()
            }
        }
        if self.preferences is not None:
            result['preferences'] = self.preferences
        return result

class ConfigManager:
    def __init__(self):
        # Set up MCP manager's own config directory
        home = os.path.expanduser('~')
        self.config_dir = os.path.join(home, '.omcp')
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self.packages_dir = os.path.join(self.config_dir, "packages")
        self.clients_dir = os.path.join(self.config_dir, "clients")
        self.client_manager = ClientIntegrationManager()
        self._ensure_directories()

    def _get_package_config(self, package_name: str, package_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get package-specific configuration if available"""
        if "configuration" in package_info:
            handler = ConfigurationHandler(package_info)
            return handler.configure()
        return None

    def _ensure_directories(self) -> None:
        """Ensure all necessary directories exist"""
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.packages_dir, exist_ok=True)
        os.makedirs(self.clients_dir, exist_ok=True)
        if not os.path.exists(self.config_file):
            self._create_default_config()

    def _create_default_config(self) -> None:
        """Create default configuration file"""
        default_config = MCPConfig(
            servers={},
            preferences={
                'allow_analytics': None,
                'theme': 'light',
                'api_key': None,
                'secret_key': None
            }
        )
        self.write_config(default_config)

    def read_config(self) -> MCPConfig:
        """Read the configuration file"""
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
                return MCPConfig(
                    servers={
                        name: MCPServer(**server_data)
                        for name, server_data in config_data.get('servers', {}).items()
                    },
                    preferences=config_data.get('preferences', {
                        'allow_analytics': None,
                        'theme': 'light'
                    })
                )
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("Config file is invalid or not found, creating default config")
            self._create_default_config()
            return self.read_config()

    def read_preferences(self) -> Dict[str, Any]:
        """Read user preferences"""
        config = self.read_config()
        return config.preferences or {}

    def write_preferences(self, prefs: Dict[str, Any]) -> None:
        """Write user preferences"""
        config = self.read_config()
        config.preferences = prefs
        self.write_config(config)

    def write_config(self, config: MCPConfig) -> None:
        """Write configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)

    def install_package(self, package: Dict[str, Any], env_vars: Optional[Dict[str, str]] = None) -> None:
        """Install a package and update MCP configuration"""
        config = self.read_config()
        server_name = package['server_name']
        
        # 自动生成env map（变量名: 描述）
        env_map = {}
        for env_name, env_info in package.get("environmentVariables", {}).items():
            env_map[env_name] = env_info.get("description", "")
        # 如果用户没有传入env_vars，则用env_map
        final_env = env_vars if env_vars else env_map
        
        # Create server configuration
        server_config = MCPServer(
            runtime=package.get('runtime', 'node'),
            env=final_env
        )
        
        # Set command and args based on runtime
        if server_config.runtime == 'node':
            server_config.args = ['-y', package['package_name']]
            server_config.command = 'npx'
        elif server_config.runtime == 'python':
            server_config.args = [package['package_name']]
            server_config.command = 'uvx'
        
        # Get package-specific configuration
        pkg_config = self._get_package_config(package['package_name'], package)
        if pkg_config:
            if 'directories' in pkg_config:  # Handle filesystem server directories
                server_config.args.extend(pkg_config['directories'])
            elif 'args' in pkg_config:  # Handle other args
                server_config.args.extend(pkg_config['args'])
            if 'env' in pkg_config:
                server_config.env = {**(server_config.env or {}), **pkg_config['env']}
        
        # Update configuration
        config.servers[server_name] = server_config
        self.write_config(config)
        
        # Create package directory and copy package files
        package_dir = os.path.join(self.packages_dir, server_name)
        os.makedirs(package_dir, exist_ok=True)
        
        # Create package.json
        package_json = {
            'name': package['package_name'],
            'version': package.get('version', '1.0.0'),
            'description': package.get('description', ''),
            'runtime': server_config.runtime
        }
        
        with open(os.path.join(package_dir, 'package.json'), 'w') as f:
            json.dump(package_json, f, indent=2)
            
        # Update MCP client configurations
        self._update_client_configs()

    def uninstall_package(self, package_name: str) -> None:
        """Uninstall a package and update MCP configuration"""
        config = self.read_config()
        server_name = package_name.replace('/', '-')
        
        # Remove from configuration
        if server_name in config.servers:
            del config.servers[server_name]
            self.write_config(config)
        
        # Remove package directory
        package_dir = os.path.join(self.packages_dir, server_name)
        if os.path.exists(package_dir):
            import shutil
            shutil.rmtree(package_dir)
            
        # Update MCP client configurations
        self._update_client_configs()

    def _update_client_configs(self) -> None:
        """Update all detected MCP client configurations"""
        installed_packages = self.get_installed_packages()
        detected_clients = self.client_manager.detect_clients()
        
        # Create client directories and configs
        for client in detected_clients:
            client_name = client.__class__.__name__.lower().replace('integration', '')
            client_dir = os.path.join(self.clients_dir, client_name)
            os.makedirs(client_dir, exist_ok=True)
            
            # Create or update client config.json
            config_path = os.path.join(client_dir, 'config.json')
            if not os.path.exists(config_path):
                client_config = {
                    "name": client_name,
                    "display_name": client_name.capitalize(),
                    "config_dir": client.config_dir,
                    "config_file": client.config_file,
                    "preferences": {
                        "auto_update": True,
                        "notifications": True
                    }
                }
                with open(config_path, 'w') as f:
                    json.dump(client_config, f, indent=2)
            
        # Update client configurations
        self.client_manager.update_client_configs(installed_packages)

    def get_detected_clients(self) -> List[str]:
        """Get a list of detected MCP clients"""
        return [client.__class__.__name__ for client in self.client_manager.detect_clients()]

    def get_installed_packages(self) -> Dict[str, Any]:
        """Get a list of installed packages"""
        config = self.read_config()
        return {
            name: {
                'name': name,
                'runtime': server.runtime,
                'command': server.command,
                'args': server.args,
                'env': server.env
            }
            for name, server in config.servers.items()
        }

    def get_config_path(self) -> str:
        """Get the path to the configuration file"""
        return self.config_file 