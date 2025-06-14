# Gitingest-X

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/cyclotruc/gitingest/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)

**Gitingest-X** 是基于 [Gitingest](https://github.com/cyclotruc/gitingest) 项目的增强版本，专为 LLM 智能体提供完整的 REST API 接口。

将任何 Git 仓库转换为适合 LLM 处理的文本格式，支持程序化访问和 Docker 容器化部署。

## ✨ 主要特性

- 🚀 **完整的 REST API** - 支持程序化访问所有功能
- 🐳 **Docker 容器化** - 一键部署，开箱即用
- 🎯 **智能过滤** - 支持文件模式匹配和大小限制
- 📊 **结构化输出** - 返回摘要、目录树和文件内容
- ⚡ **速率限制** - 内置请求频率控制
- 🔍 **多种接口** - 支持 POST/GET 请求和轻量级摘要

## 🚀 快速开始

### Docker 部署（推荐）

```bash
# 1. 构建镜像
docker build -t gitingest-x .

# 2. 运行容器
docker run -d --name gitingest-x -p 8000:8000 gitingest-x

# 3. 验证服务
curl http://localhost:8000/api/v1/health
```

### 本地开发

```bash
# 1. 克隆仓库
git clone <your-repo-url>
cd gitingest-x

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
cd src
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

## 📡 API 接口文档

### 基础信息

- **基础 URL**: `http://localhost:8000/api/v1`
- **内容类型**: `application/json`
- **交互式文档**: `http://localhost:8000/docs`

### 主要端点

#### 1. 完整仓库摄入

**POST /api/v1/ingest**

```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "https://github.com/octocat/Hello-World",
    "max_file_size": 1048576,
    "include_patterns": ["*.md", "*.py"],
    "exclude_patterns": ["*.log"],
    "branch": "main"
  }'
```

**GET /api/v1/ingest**

```bash
curl "http://localhost:8000/api/v1/ingest?source=https://github.com/octocat/Hello-World&include_patterns=*.md"
```

#### 2. 轻量级摘要

**GET /api/v1/ingest/summary**

```bash
curl "http://localhost:8000/api/v1/ingest/summary?source=https://github.com/octocat/Hello-World"
```

#### 3. 健康检查

**GET /api/v1/health**

```bash
curl "http://localhost:8000/api/v1/health"
```

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `source` | string | ✅ | Git 仓库 URL 或本地路径 |
| `max_file_size` | integer | ❌ | 最大文件大小（字节），默认 10MB |
| `include_patterns` | array | ❌ | 包含文件模式（Unix 通配符） |
| `exclude_patterns` | array | ❌ | 排除文件模式（Unix 通配符） |
| `branch` | string | ❌ | 指定分支名称 |

### 响应格式

```json
{
  "success": true,
  "data": {
    "summary": "Repository: octocat/Hello-World\nFiles analyzed: 2\nEstimated tokens: 150",
    "tree": "Hello-World/\n└── README",
    "content": "FILE: README\nHello World!\n\nThis is my first repository on GitHub!"
  },
  "metadata": {
    "source_type": "remote",
    "repository": "octocat/Hello-World",
    "branch": "master",
    "subpath": "/"
  }
}
```

### 速率限制

- **完整摄入**: 5 次/分钟
- **摘要接口**: 10 次/分钟

## 🐳 Docker 部署详解

### 环境变量

```bash
# 允许的主机名（可选）
ALLOWED_HOSTS="example.com,localhost,127.0.0.1"
```

### Docker Compose

```yaml
version: '3.8'
services:
  gitingest-x:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 生产部署

```bash
# 使用 Docker Compose
docker-compose up -d

# 或直接运行
docker run -d \
  --name gitingest-x \
  -p 8000:8000 \
  -e ALLOWED_HOSTS="your-domain.com,localhost" \
  --restart unless-stopped \
  gitingest-x
```

## 💻 使用示例

### Python 客户端

```python
import requests

# 基础使用
response = requests.post("http://localhost:8000/api/v1/ingest", json={
    "source": "https://github.com/octocat/Hello-World",
    "include_patterns": ["*.md"],
    "max_file_size": 1048576
})

data = response.json()
if data["success"]:
    print("摘要:", data["data"]["summary"])
    print("目录结构:", data["data"]["tree"])
    print("文件内容:", data["data"]["content"])
else:
    print("错误:", data["error"])
```

### JavaScript/Node.js

```javascript
const response = await fetch('http://localhost:8000/api/v1/ingest', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    source: 'https://github.com/octocat/Hello-World',
    include_patterns: ['*.md']
  })
});

const data = await response.json();
console.log(data.success ? data.data.summary : data.error);
```

## 🛠️ 技术栈

- **后端框架**: [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Web 框架
- **数据验证**: [Pydantic](https://pydantic.dev/) - 数据模型和验证
- **速率限制**: [SlowAPI](https://github.com/laurentS/slowapi) - 请求频率控制
- **模板引擎**: [Jinja2](https://jinja.palletsprojects.com/) - HTML 模板
- **Token 计算**: [tiktoken](https://github.com/openai/tiktoken) - OpenAI 的分词器
- **容器化**: Docker - 应用容器化部署

## 📚 相关资源

- 📖 [完整 API 文档](docs/API_GUIDE.md)
- 🔗 [交互式 API 文档](http://localhost:8000/docs)
- 💻 [使用示例代码](examples/api_usage_examples.py)
- 🧪 [快速测试脚本](scripts/test_api_quick.py)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目基于 [Gitingest](https://github.com/cyclotruc/gitingest) 开发，采用 MIT 许可证。

## 🙏 致谢

感谢 [Gitingest](https://github.com/cyclotruc/gitingest) 项目提供的优秀基础。
