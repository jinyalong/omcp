import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import yaml
from .config_manager import ConfigManager
from .env_manager import EnvManager
from .runtime_utils import check_runtime_requirements
from .analytics import Analytics
from .app_manager import AppManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Package:
    def __init__(self, data: Dict):
        self.package_name = data.get("package_name")
        self.server_name = data.get("server_name")
        self.description = data.get("description")
        self.vendor = data.get("vendor")
        self.source_url = data.get("sourceUrl")
        self.homepage = data.get("homepage")
        self.license = data.get("license")
        self.runtime = data.get("runtime")
        self.environment_variables = data.get("environmentVariables", {})

    @classmethod
    def from_file(cls, file_path: str) -> "Package":
        with open(file_path, "r") as f:
            return cls(json.load(f))

class PackageManager:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.env_manager = EnvManager()
        self.env_manager.set_config_manager(self.config_manager)
        self.analytics = Analytics(self.config_manager)
        self.app_manager = AppManager()
        self.registry_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "registry")
        self.packages_dir = self.config_manager.packages_dir
        os.makedirs(self.packages_dir, exist_ok=True)

    def list_packages(self) -> List[Dict[str, Any]]:
        """List all available packages from the registry"""
        packages = []
        if not os.path.exists(self.registry_dir):
            logger.warning(f"Registry directory not found: {self.registry_dir}")
            return packages

        for filename in os.listdir(self.registry_dir):
            if not (filename.endswith('.yaml') or filename.endswith('.json')):
                continue
            file_path = os.path.join(self.registry_dir, filename)
            try:
                with open(file_path, 'r') as f:
                    if filename.endswith('.yaml'):
                        package_info = yaml.safe_load(f)
                    else:  # JSON file
                        package_info = json.load(f)
                    if 'server_name' in package_info and 'package_name' in package_info:
                        packages.append(package_info)
            except Exception as e:
                logger.error(f"Error reading package file {filename}: {e}")
        return packages

    def _find_package_file(self, server_name: str) -> Optional[Path]:
        """Find package file in registry by server_name"""
        for file in Path(self.registry_dir).glob("*.json"):
            try:
                with open(file, "r") as f:
                    info = json.load(f)
                    if info.get("server_name") == server_name:
                        return file
            except Exception:
                continue
        for file in Path(self.registry_dir).glob("*.yaml"):
            try:
                with open(file, "r") as f:
                    info = yaml.safe_load(f)
                    if info.get("server_name") == server_name:
                        return file
            except Exception:
                continue
        return None

    def install_package(self, server_name: str) -> None:
        """Install a package from the registry by server_name"""
        package_info = None
        for filename in os.listdir(self.registry_dir):
            if not (filename.endswith('.yaml') or filename.endswith('.json')):
                continue
            file_path = os.path.join(self.registry_dir, filename)
            try:
                with open(file_path, 'r') as f:
                    if filename.endswith('.yaml'):
                        info = yaml.safe_load(f)
                    else:
                        info = json.load(f)
                    if info.get('server_name') == server_name:
                        package_info = info
                        break
            except Exception as e:
                logger.error(f"Error reading package file {filename}: {e}")
                continue
        if not package_info:
            raise ValueError(f"Package {server_name} not found in registry")
        if not check_runtime_requirements(package_info):
            raise RuntimeError("Runtime requirements not met")
        env_vars = self.env_manager.prompt_for_env_vars(server_name, package_info)
        self.config_manager.install_package(package_info, env_vars)
        if self.analytics.check_consent():
            self.analytics.track_installation(server_name, package_info)
        self.app_manager.prompt_for_restart("claude")

    def uninstall_package(self, server_name: str) -> None:
        """Uninstall a package by server_name"""
        try:
            self.config_manager.uninstall_package(server_name)
            if self.analytics.check_consent():
                self.analytics.track_uninstallation(server_name)
            self.app_manager.prompt_for_restart("claude")
        except Exception as e:
            logger.error(f"Error uninstalling package {server_name}: {e}")
            raise

    def get_installed_packages(self) -> List[Dict[str, Any]]:
        """Get a list of installed packages with their metadata (using server_name)"""
        packages = []
        installed = self.config_manager.get_installed_packages()
        for server_name, package_info in installed.items():
            package_dir = os.path.join(self.packages_dir, server_name)
            package_json_path = os.path.join(package_dir, "package.json")
            if not os.path.exists(package_json_path):
                continue
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    package_data['server_name'] = server_name
                    package_data.update({
                        'runtime': package_info.get('runtime', 'node'),
                        'command': package_info.get('command', 'npx'),
                        'args': package_info.get('args', [])
                    })
                    packages.append(package_data)
            except json.JSONDecodeError:
                logger.error(f"Error reading package.json for {server_name}")
            except Exception as e:
                logger.error(f"Error reading package {server_name}: {e}")
        return packages 