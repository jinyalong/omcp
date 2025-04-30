# OMCP Manager

OMCP Manager is a package manager for Model Context Protocol (MCP) servers. It provides a simple command-line interface to manage MCP server packages, including installation, uninstallation, and configuration.

## ⚠️ Security Warning

**Important Security Notice**: MCP tools may pose potential poisoning risks. Please be aware of the following security considerations:

1. Always verify the source and integrity of MCP packages before installation
2. Run MCP tools in isolated environments or containers
3. Regularly update packages to the latest secure versions
4. Monitor system resources and network activity
5. Use strong authentication and access controls
6. Keep your system and dependencies up to date

### Features

- List available MCP server packages
- Install and uninstall MCP server packages
- Manage package configurations
- Support for multiple runtimes (Node.js, Python)
- Client integration support (Claude, Cursor, etc.)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/omcp-manager.git
cd omcp-manager

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Usage

```bash
# List available packages
omcp list

# Install a package
omcp install modelcontextprotocol@filesystem

# List installed packages
omcp installed

# Uninstall a package
omcp uninstall modelcontextprotocol@filesystem
```

### Development

To contribute to the project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 探索更多

想要了解更多 MCP 服务器信息？请访问 [MCP服务器](https://mcpservers.cn) 获取更多资讯。
