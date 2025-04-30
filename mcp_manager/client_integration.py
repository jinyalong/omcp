import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
import platform

logger = logging.getLogger(__name__)

class MCPClientIntegration(ABC):
    """Abstract base class for MCP client integrations"""
    
    @abstractmethod
    def detect_client(self) -> bool:
        """Detect if this MCP client is installed"""
        pass
        
    @abstractmethod
    def get_config_path(self) -> Optional[str]:
        """Get the path to the client's configuration file"""
        pass
        
    @abstractmethod
    def update_client_config(self, mcp_servers: Dict[str, Any]) -> None:
        """Update the client's configuration with MCP server information"""
        pass

class ClaudeIntegration(MCPClientIntegration):
    """Integration for Claude Desktop client"""
    
    def __init__(self):
        if os.name == 'nt':  # Windows
            app_data = os.getenv('APPDATA') or os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming')
            self.config_dir = os.path.join(app_data, 'Claude')
        elif os.name == 'posix':  # macOS or Linux
            if platform.system() == 'Darwin':  # macOS
                self.config_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Claude')
            else:  # Linux
                config_dir = os.getenv('XDG_CONFIG_HOME') or os.path.join(os.path.expanduser('~'), '.config')
                self.config_dir = os.path.join(config_dir, 'Claude')
        
        self.config_file = os.path.join(self.config_dir, 'claude_desktop_config.json')
    
    def detect_client(self) -> bool:
        """Detect if Claude Desktop is installed"""
        return os.path.exists(self.config_dir)
    
    def get_config_path(self) -> Optional[str]:
        """Get the path to Claude's configuration file"""
        return self.config_file if os.path.exists(self.config_file) else None
    
    def update_client_config(self, mcp_servers: Dict[str, Any]) -> None:
        """Update Claude's configuration with MCP server information"""
        if not self.detect_client():
            logger.info("Claude Desktop not detected, skipping configuration update")
            return
            
        try:
            # Read existing Claude config
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            
            # Initialize mcpServers if it doesn't exist
            if 'mcpServers' not in config:
                config['mcpServers'] = {}
            
            # Get current MCP package names from the servers list
            current_mcp_packages = set(mcp_servers.keys())
            
            # Remove MCP packages that are no longer in the servers list
            for name in list(config['mcpServers'].keys()):
                if name not in current_mcp_packages:
                    del config['mcpServers'][name]
            
            # Update or add MCP package servers
            for name, server in mcp_servers.items():
                config['mcpServers'][name] = {
                    'runtime': server['runtime'],
                    'command': server['command'],
                    'args': server['args'],
                    **({'env': server['env']} if server.get('env') else {})  # Only add env if it exists and not empty
                }
            
            # Ensure preferences exist
            if 'preferences' not in config:
                config['preferences'] = {
                    'allow_analytics': None,
                    'theme': 'light'
                }
            
            # Write updated config
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info("Successfully updated Claude Desktop configuration")
            
        except Exception as e:
            logger.error(f"Failed to update Claude Desktop configuration: {e}")

class CursorIntegration(MCPClientIntegration):
    """Integration for Cursor client"""
    
    def __init__(self):
        home = os.path.expanduser('~')
        self.config_dir = os.path.join(home, '.cursor')
        self.config_file = os.path.join(self.config_dir, 'mcp.json')
    
    def detect_client(self) -> bool:
        """Detect if Cursor is installed"""
        return os.path.exists(self.config_dir)
    
    def get_config_path(self) -> Optional[str]:
        """Get the path to Cursor's MCP configuration file"""
        return self.config_file if os.path.exists(self.config_file) else None
    
    def update_client_config(self, mcp_servers: Dict[str, Any]) -> None:
        """Update Cursor's MCP configuration"""
        if not self.detect_client():
            logger.info("Cursor not detected, skipping configuration update")
            return
            
        try:
            # Read existing Cursor MCP config
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            
            # Initialize mcpServers if it doesn't exist
            if 'mcpServers' not in config:
                config['mcpServers'] = {}
            
            # Get current MCP package names from the servers list
            current_mcp_packages = set(mcp_servers.keys())
            
            # Remove MCP packages that are no longer in the servers list
            for name in list(config['mcpServers'].keys()):
                if name not in current_mcp_packages and not name.startswith('amap-'):
                    del config['mcpServers'][name]
            
            # Update or add MCP package servers
            for name, server in mcp_servers.items():
                config['mcpServers'][name] = {
                    'runtime': server['runtime'],
                    'command': server['command'],
                    'args': server['args'],
                    **({'env': server['env']} if server.get('env') else {})  # Only add env if it exists and not empty
                }
            
            # Write updated config
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info("Successfully updated Cursor MCP configuration")
            
        except Exception as e:
            logger.error(f"Failed to update Cursor MCP configuration: {e}")

class ClientIntegrationManager:
    """Manager for handling different MCP client integrations"""
    
    def __init__(self):
        self.integrations: List[MCPClientIntegration] = [
            ClaudeIntegration(),
            CursorIntegration()
        ]
    
    def detect_clients(self) -> List[MCPClientIntegration]:
        """Detect all installed MCP clients"""
        return [integration for integration in self.integrations if integration.detect_client()]
    
    def update_client_configs(self, mcp_servers: Dict[str, Any]) -> None:
        """Update configurations for all detected clients"""
        detected_clients = self.detect_clients()
        if not detected_clients:
            logger.info("No MCP clients detected")
            return
            
        for client in detected_clients:
            client.update_client_config(mcp_servers) 