import os
import subprocess
import logging
from typing import Tuple, Optional
from rich.prompt import Confirm
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()

def check_python_runtime() -> Tuple[bool, Optional[str]]:
    """Check if Python runtime is available"""
    try:
        result = subprocess.run(
            ["python", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
    except FileNotFoundError:
        pass
    
    try:
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
    except FileNotFoundError:
        pass
    
    return False, None

def check_node_runtime() -> Tuple[bool, Optional[str]]:
    """Check if Node.js runtime is available"""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
    except FileNotFoundError:
        pass
    
    return False, None

def check_uv_installed() -> bool:
    """Check if uv (Python package manager) is installed"""
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

def prompt_for_uv_install() -> bool:
    """Prompt user to install uv"""
    console.print("\n[yellow]uv (Python package manager) is not installed.[/yellow]")
    console.print("uv is recommended for better performance and reliability.")
    
    install = Confirm.ask(
        "Would you like to install uv?",
        default=True
    )
    
    if not install:
        return False
    
    try:
        # Try to install uv using pip
        subprocess.run(
            ["pip", "install", "uv"],
            check=True
        )
        console.print("[green]Successfully installed uv![/green]")
        return True
    except subprocess.CalledProcessError:
        console.print("[red]Failed to install uv.[/red]")
        console.print("You can install it manually by running:")
        console.print("pip install uv")
        return False

def check_runtime_requirements(package_info: dict) -> bool:
    """Check if all runtime requirements are met"""
    runtime = package_info.get("runtime", "python")
    requirements_met = True
    
    if runtime == "python":
        has_python, version = check_python_runtime()
        if not has_python:
            console.print("[red]Error: Python runtime is required but not found.[/red]")
            requirements_met = False
        else:
            console.print(f"[green]Found Python: {version}[/green]")
            
            # Check for uv if it's a Python package
            if not check_uv_installed():
                if prompt_for_uv_install():
                    console.print("[green]uv is now installed and ready to use.[/green]")
                else:
                    console.print("[yellow]Warning: uv is not installed. Some features may not work optimally.[/yellow]")
    
    elif runtime == "node":
        has_node, version = check_node_runtime()
        if not has_node:
            console.print("[red]Error: Node.js runtime is required but not found.[/red]")
            requirements_met = False
        else:
            console.print(f"[green]Found Node.js: {version}[/green]")
    
    return requirements_met 