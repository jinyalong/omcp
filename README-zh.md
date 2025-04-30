# OMCP 管理器

OMCP 管理器是一个用于管理模型上下文协议（MCP）服务器的包管理器。它提供了一个简单的命令行界面来管理 MCP 服务器包，包括安装、卸载和配置。

## ⚠️ 安全警告

**重要安全提示**：MCP 工具可能存在投毒风险，请注意以下安全事项：

1. 安装前请务必验证 MCP 包的来源和完整性
2. 在隔离环境或容器中运行 MCP 工具
3. 定期更新包到最新的安全版本
4. 监控系统资源和网络活动
5. 使用强身份验证和访问控制
6. 保持系统和依赖项的最新状态

### 功能特点

- 列出可用的 MCP 服务器包
- 安装和卸载 MCP 服务器包
- 管理包配置
- 支持多种运行时环境（Node.js、Python）
- 支持客户端集成（Claude、Cursor 等）

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/omcp-manager.git
cd omcp-manager

# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装包
pip install -e .
```

### 使用方法

```bash
# 列出可用包
omcp list

# 安装包
omcp install modelcontextprotocol@filesystem

# 列出已安装的包
omcp installed

# 卸载包
omcp uninstall modelcontextprotocol@filesystem
```

### 开发

参与项目开发：

1. Fork 仓库
2. 创建特性分支
3. 提交更改
4. 发起 Pull Request

### 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 探索更多

想要了解更多 MCP 服务器信息？请访问 [MCP服务器](https://mcpservers.cn) 获取更多资讯。 