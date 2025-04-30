import os
from typing import Dict, Any, List, Optional
from rich.prompt import Prompt, Confirm
from rich.console import Console

console = Console()

class ConfigurationHandler:
    """Generic configuration handler for MCP packages"""
    
    def __init__(self, package_info: Dict[str, Any]):
        self.package_info = package_info
        self.config_schema = package_info.get("configuration", {})
        
    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate configuration against schema"""
        for field, schema in self.config_schema.items():
            if schema.get("required", False) and field not in config:
                return False
                
            if field in config:
                value = config[field]
                if schema.get("type") == "array":
                    if not isinstance(value, list):
                        return False
                    if "items" in schema:
                        item_schema = schema["items"]
                        if not all(self._validate_item(item, item_schema) for item in value):
                            return False
                elif schema.get("type") == "string":
                    if not isinstance(value, str):
                        return False
                    if schema.get("format") == "directory-path":
                        if not os.path.isdir(os.path.expanduser(value)):
                            return False
        return True
        
    def _validate_item(self, item: Any, schema: Dict[str, Any]) -> bool:
        """Validate a single item against its schema"""
        if schema.get("type") == "string":
            if not isinstance(item, str):
                return False
            if schema.get("format") == "directory-path":
                return os.path.isdir(os.path.expanduser(item))
        return True
        
    def configure(self) -> Dict[str, Any]:
        """Generate configuration based on schema"""
        config = {}
        for field, schema in self.config_schema.items():
            if schema.get("type") == "array":
                config[field] = self._configure_array(schema)
            elif schema.get("type") == "string":
                config[field] = self._configure_string(schema)
        return config
        
    def _configure_array(self, schema: Dict[str, Any]) -> List[Any]:
        """Configure array type field"""
        items = []
        description = schema.get("description", "Enter items (press Enter to finish)")
        default = schema.get("default", [])
        
        console.print(f"\n[bold]{description}[/bold]")
        
        # Don't add default items immediately, save them for later if needed
        while True:
            item = self._configure_item(schema["items"])
            if item is None:  # User pressed Enter to finish
                break
            # For directory paths, expand them to absolute paths
            if schema.get("items", {}).get("format") == "directory-path":
                expanded_path = os.path.abspath(os.path.expanduser(item))
                items.append(expanded_path)
            else:
                items.append(item)
        
        # If no items were added and there are defaults, use them
        if not items and default:
            for item in default:
                if schema.get("items", {}).get("format") == "directory-path":
                    expanded_path = os.path.abspath(os.path.expanduser(item))
                    items.append(expanded_path)
                else:
                    items.append(item)
            console.print("[yellow]No directories specified. Using default values.[/yellow]")
            
        return items
        
    def _configure_string(self, schema: Dict[str, Any]) -> Optional[str]:
        """Configure string type field"""
        description = schema.get("description", "Enter value")
        default = schema.get("default", "")
        required = schema.get("required", False)
        
        while True:
            value = Prompt.ask(description, default=default)
            if not value:  # Empty input
                if not required:
                    return None  # Allow empty input for non-required fields
                console.print("[red]This field is required. Please enter a value.[/red]")
                continue
                
            if schema.get("format") == "directory-path":
                expanded_path = os.path.expanduser(value)
                if os.path.isdir(expanded_path):
                    return value
                console.print(f"[red]Warning: {value} is not a valid directory. Please try again.[/red]")
            else:
                return value
                
    def _configure_item(self, schema: Dict[str, Any]) -> Optional[str]:
        """Configure a single item"""
        if schema.get("type") == "string":
            return self._configure_string(schema)
        return None 