from setuptools import setup, find_packages

setup(
    name="omcp-manager",
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
    author="金亚龙",
    author_email="jinyalong.jyl@antgroup.com",
    description="OMCP 管理器：用于管理模型上下文协议（MCP）服务器的包管理器",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jinyalong/omcp",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
) 