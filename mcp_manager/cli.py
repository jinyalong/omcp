import typer
import logging
from rich.console import Console
from rich.table import Table
from .package import PackageManager
from .config_manager import ConfigManager
from .analytics import Analytics

console = Console()
logger = logging.getLogger(__name__)
app = typer.Typer()

@app.callback()
def main():
    """OMCP Manager - A package manager for MCP Servers

    For more information, visit: https://mcpservers.cn
    """
    pass

@app.command()
def list():
    """List available MCP server packages"""
    manager = PackageManager()
    packages = sorted(manager.list_packages(), key=lambda p: p["server_name"])
    
    if not packages:
        console.print("[yellow]No packages available in the registry[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Server Name")
    table.add_column("Description")
    table.add_column("Vendor")
    table.add_column("Runtime")

    for package in packages:
        table.add_row(
            package["server_name"],
            package.get("description", "N/A"),
            package.get("vendor", "N/A"),
            package.get("runtime", "N/A")
        )

    console.print(table)

@app.command()
def install(server_name: str):
    """Install an MCP server package

    For more information about available packages, visit: https://mcpservers.cn
    """
    manager = PackageManager()
    try:
        manager.install_package(server_name)
        console.print(f"[green]Successfully installed {server_name}[/green]")
    except Exception as e:
        console.print(f"[red]Error installing package: {str(e)}[/red]")

@app.command()
def uninstall(server_name: str):
    """Uninstall an MCP server package"""
    manager = PackageManager()
    try:
        manager.uninstall_package(server_name)
        console.print(f"[green]Successfully uninstalled {server_name}[/green]")
    except Exception as e:
        console.print(f"[red]Error uninstalling package: {str(e)}[/red]")

@app.command()
def update():
    """Update the MCP manager itself

    For more information about updates, visit: https://mcpservers.cn
    """
    # TODO: Implement self-update functionality
    console.print("[yellow]Self-update functionality coming soon![/yellow]")

@app.command()
def installed():
    """List installed packages"""
    manager = PackageManager()
    packages = manager.get_installed_packages()
    if not packages:
        console.print("[yellow]No packages installed[/yellow]")
        return
        
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Server Name")
    table.add_column("Version")
    table.add_column("Description")
    table.add_column("Runtime")
    table.add_column("Vendor")

    for package in packages:
        table.add_row(
            package["server_name"],
            package.get("version", "N/A"),
            package.get("description", "N/A"),
            package.get("runtime", "N/A"),
            package.get("vendor", "N/A")
        )

    console.print(table)

@app.command()
def clients():
    """List detected MCP clients"""
    config_manager = ConfigManager()
    clients = config_manager.get_detected_clients()
    
    if not clients:
        console.print("[yellow]No MCP clients detected[/yellow]")
        return
        
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Client Name")
    table.add_column("Status")
    
    for client in clients:
        # Remove 'Integration' suffix from client name
        display_name = client.replace('Integration', '')
        table.add_row(
            display_name,
            "[green]Detected[/green]"
        )
    
    console.print(table)

if __name__ == "__main__":
    app() 