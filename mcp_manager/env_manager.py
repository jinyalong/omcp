import os
import logging
from typing import Dict, Optional, List
from rich.prompt import Confirm, Prompt
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()

class EnvManager:
    def __init__(self):
        self.config_manager = None  # Will be set by the package manager

    def set_config_manager(self, config_manager) -> None:
        """Set the config manager instance"""
        self.config_manager = config_manager

    def check_required_env_vars(self, package_name: str, package_info: Dict) -> Dict[str, str]:
        """Check if required environment variables are set"""
        env_vars = {}
        required_vars = package_info.get("environmentVariables", {})
        
        for var_name, var_info in required_vars.items():
            if var_info.get("required", False):
                value = os.environ.get(var_name)
                if value:
                    env_vars[var_name] = value
        
        return env_vars

    def prompt_for_env_vars(self, package_name: str, package_info: Dict) -> Optional[Dict[str, str]]:
        """Prompt user for environment variables"""
        # Check if running in CI environment
        is_ci = os.environ.get("CI") == "true"
        
        # Get required environment variables
        required_vars = package_info.get("environmentVariables", {})
        if not required_vars:
            return None
        
        # Check existing environment variables
        existing_vars = {}
        has_all_required = True
        
        for var_name, var_info in required_vars.items():
            value = os.environ.get(var_name)
            if value:
                existing_vars[var_name] = value
            elif var_info.get("required", False):
                has_all_required = False
        
        # In CI environment, use existing vars or fail
        if is_ci:
            if not has_all_required:
                console.print("\n[red]Error: Required environment variables are missing in CI mode.[/red]")
                console.print("Make sure all required environment variables are set in your CI environment.")
                raise ValueError("Missing required environment variables in CI mode")
            return existing_vars
        
        # If all required vars exist, ask if user wants to use them
        if has_all_required and existing_vars:
            use_auto = Confirm.ask(
                "Found all required environment variables. Would you like to use them automatically?",
                default=True
            )
            if use_auto:
                return existing_vars
        
        # Ask if user wants to configure environment variables
        configure = Confirm.ask(
            "Would you like to configure environment variables for this package?",
            default=not has_all_required
        )
        
        if not configure:
            if not has_all_required:
                config_path = self.config_manager.get_config_path()
                console.print("\n[yellow]Note: Some required environment variables are not configured.[/yellow]")
                console.print(f"You can set them later by editing the config file at:")
                console.print(config_path)
            return None
        
        # Prompt for each environment variable
        env_vars = {}
        for var_name, var_info in required_vars.items():
            existing_value = os.environ.get(var_name)
            
            if existing_value:
                reuse = Confirm.ask(
                    f"Found {var_name} in your environment variables. Would you like to use it?",
                    default=True
                )
                if reuse:
                    env_vars[var_name] = existing_value
                    continue
            
            value = Prompt.ask(
                f"Please enter {var_info.get('description', var_name)}",
                default=None if var_info.get("required", False) else ""
            )
            
            if value or var_info.get("required", False):
                env_vars[var_name] = value
        
        if not env_vars:
            config_path = self.config_manager.get_config_path()
            console.print("\n[yellow]No environment variables were configured.[/yellow]")
            console.print(f"You can set them later by editing the config file at:")
            console.print(config_path)
            return None
        
        return env_vars 