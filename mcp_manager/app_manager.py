import os
import subprocess
import logging
import time
import platform
from typing import Optional
from rich.prompt import Confirm
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()

class AppManager:
    def __init__(self):
        system = platform.system().lower()
        self.platform = 'darwin' if system == 'darwin' else ('nt' if system == 'windows' else 'linux')
        self.supported_apps = {
            "claude": {
                "windows": "Claude.exe",
                "darwin": "Claude",
                "linux": "claude"
            }
        }

    def is_app_running(self, app_name: str) -> bool:
        """Check if an application is running"""
        if app_name not in self.supported_apps:
            logger.warning(f"App {app_name} is not supported")
            return False
        
        app_info = self.supported_apps[app_name]
        app_process = app_info.get(self.platform)
        
        if not app_process:
            logger.warning(f"App {app_name} is not supported on this platform")
            return False
        
        try:
            if self.platform == "nt":  # Windows
                result = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {app_process}", "/NH"],
                    capture_output=True,
                    text=True
                )
                return app_process in result.stdout
            else:  # Unix-like systems
                result = subprocess.run(
                    ["pgrep", "-x", app_process],
                    capture_output=True,
                    text=True
                )
                return bool(result.stdout.strip())
        except Exception as e:
            logger.error(f"Error checking if {app_name} is running: {str(e)}")
            return False

    def restart_app(self, app_name: str) -> bool:
        """Restart an application"""
        if app_name not in self.supported_apps:
            logger.warning(f"App {app_name} is not supported")
            return False
        
        app_info = self.supported_apps[app_name]
        app_process = app_info.get(self.platform)
        
        if not app_process:
            logger.warning(f"App {app_name} is not supported on this platform")
            return False
        
        try:
            # Kill the existing process
            if self.platform == "nt":  # Windows
                subprocess.run(["taskkill", "/F", "/IM", app_process], check=True)
            else:  # Unix-like systems
                subprocess.run(["pkill", "-x", app_process], check=True)
            
            # Wait a moment for the process to fully terminate
            time.sleep(2)
            
            # Start the application
            if self.platform == "nt":  # Windows
                subprocess.Popen(["start", "", app_process], shell=True)
            elif self.platform == "darwin":  # macOS
                subprocess.Popen(["open", "-a", app_process])
            else:  # Linux
                subprocess.Popen([app_process])
            
            return True
        except Exception as e:
            logger.error(f"Error restarting {app_name}: {str(e)}")
            return False

    def prompt_for_restart(self, app_name: str) -> bool:
        """Prompt user to restart an application"""
        # Check if running in CI environment
        is_ci = os.environ.get("CI") == "true"
        
        # Check if restart is explicitly requested
        restart_requested = "--restart" in os.sys.argv
        
        # Skip prompts in CI mode unless restart is requested
        if is_ci and not restart_requested:
            return False
        
        # Check if app is running
        if not self.is_app_running(app_name):
            return False
        
        # Restart without prompting if --restart flag is used
        if restart_requested:
            return self.restart_app(app_name)
        
        # Prompt user
        should_restart = Confirm.ask(
            f"Would you like to restart {app_name} to apply changes?",
            default=True
        )
        
        if should_restart:
            return self.restart_app(app_name)
        
        return False 