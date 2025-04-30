from setuptools import setup, find_packages

setup(
    name="mcp-manager",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "rich",
        "typer",
    ],
    entry_points={
        "console_scripts": [
            "omcp=mcp_manager.cli:app",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A package manager for MCP Servers",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mcp-manager",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
) 