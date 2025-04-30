import os
import shutil
import tempfile
from pathlib import Path
import pytest
from mcp_manager.package import Package, PackageManager

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def package_data():
    return {
        "name": "test-package",
        "description": "Test package",
        "vendor": "Test Vendor",
        "sourceUrl": "https://test.com",
        "homepage": "https://test.com",
        "license": "MIT",
        "runtime": "python",
        "environmentVariables": {
            "TEST_KEY": {
                "description": "Test key",
                "required": True
            }
        }
    }

def test_package_creation(package_data):
    package = Package(package_data)
    assert package.name == "test-package"
    assert package.runtime == "python"
    assert "TEST_KEY" in package.environment_variables

def test_package_manager_install_uninstall(temp_dir, package_data):
    # Create registry directory
    registry_dir = Path(temp_dir) / "registry"
    registry_dir.mkdir()
    
    # Create package file
    package_file = registry_dir / "test-package.json"
    with open(package_file, "w") as f:
        import json
        json.dump(package_data, f)
    
    # Initialize package manager with temp directory
    manager = PackageManager()
    manager.registry_dir = registry_dir
    manager.install_dir = Path(temp_dir) / "packages"
    manager._ensure_directories()
    
    # Test installation
    assert manager.install_package("test-package")
    assert (manager.install_dir / "test-package" / "package.json").exists()
    
    # Test uninstallation
    assert manager.uninstall_package("test-package")
    assert not (manager.install_dir / "test-package").exists() 