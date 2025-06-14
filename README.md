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

### Dockerfile 特性

当前 Dockerfile 采用多阶段构建，具有以下特性：

- **多阶段构建**: 分离构建和运行环境，减小镜像体积
- **Python 3.12**: 基于官方 Python 3.12 slim 镜像
- **安全性**: 使用非 root 用户 (appuser) 运行应用
- **依赖优化**: 利用 Docker 缓存层优化构建速度
- **必要工具**: 预装 Git 和 curl 用于仓库克隆和健康检查

### 环境变量

```bash
# 允许的主机名（可选）
ALLOWED_HOSTS="example.com,localhost,127.0.0.1"

# Python 环境变量（已在 Dockerfile 中设置）
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### Docker Compose 配置

项目已包含 `docker-compose.yml` 文件，提供完整的容器化部署方案：

```yaml
version: '3.8'
services:
  gitingest-x:
    build: .
    container_name: gitingest-x
    ports:
      - "8000:8000"
    environment:
      - ALLOWED_HOSTS=localhost,127.0.0.1,gitingest-x.local
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    volumes:
      - gitingest_tmp:/tmp
    networks:
      - gitingest-network

volumes:
  gitingest_tmp:
    driver: local

networks:
  gitingest-network:
    driver: bridge
```

### 持久化存储配置

#### 1. 默认卷挂载

默认配置包含临时文件持久化，用于存储克隆的仓库和处理过程中的临时文件：

```yaml
volumes:
  - gitingest_tmp:/tmp  # 容器内 /tmp 目录持久化
```

**优势**：
- 提高重复访问相同仓库的性能
- 避免重复克隆已处理的仓库
- 容器重启后保留临时数据

#### 2. 扩展持久化配置

如需更多持久化选项，可以修改 `docker-compose.yml`：

```yaml
services:
  gitingest-x:
    # ... 其他配置 ...
    volumes:
      # 临时文件持久化（推荐）
      - gitingest_tmp:/tmp
      
      # 可选：日志持久化
      - ./logs:/app/logs
      
      # 可选：缓存持久化（提高重复访问性能）
      - gitingest_cache:/app/cache
      
      # 可选：配置文件挂载（只读）
      - ./config:/app/config:ro

volumes:
  gitingest_tmp:
    driver: local
  gitingest_cache:
    driver: local
```

#### 3. 主机目录挂载

如果希望直接挂载主机目录进行数据管理：

```yaml
services:
  gitingest-x:
    volumes:
      # 挂载主机目录到容器
      - /host/data/tmp:/tmp
      - /host/data/logs:/app/logs
      - /host/data/cache:/app/cache
```

**注意事项**：
- 确保主机目录存在且有适当权限
- 容器使用 UID 1000 运行，确保目录权限正确

#### 4. 数据卷管理

```bash
# 查看所有卷
docker volume ls

# 查看特定卷详情
docker volume inspect gitingest_gitingest_tmp

# 清理未使用的卷
docker volume prune

# 备份卷数据
docker run --rm \
  -v gitingest_gitingest_tmp:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/gitingest_tmp_backup.tar.gz -C /data .

# 恢复卷数据
docker run --rm \
  -v gitingest_gitingest_tmp:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/gitingest_tmp_backup.tar.gz -C /data
```

#### 5. 性能优化配置

对于高频使用场景，可以配置更大的临时存储：

```yaml
services:
  gitingest-x:
    volumes:
      - gitingest_tmp:/tmp
    tmpfs:
      # 使用内存文件系统加速小文件操作
      - /app/temp:size=512M,uid=1000,gid=1000
```

### 生产部署

#### Docker Compose 部署（推荐）

```bash
# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f gitingest-x

# 查看最近日志
docker-compose logs --tail=100 gitingest-x

# 重启服务
docker-compose restart gitingest-x

# 更新服务（重新构建镜像）
docker-compose up -d --build

# 停止服务
docker-compose down

# 停止服务并删除卷（谨慎使用）
docker-compose down -v
```

#### 服务监控和维护

```bash
# 查看容器资源使用情况
docker stats gitingest-x

# 进入容器进行调试
docker-compose exec gitingest-x /bin/bash

# 查看容器详细信息
docker inspect gitingest-x

# 检查健康状态
docker-compose exec gitingest-x curl -f http://localhost:8000/api/v1/health
```

#### 直接 Docker 运行

```bash
# 方法1: 基础运行
docker run -d \
  --name gitingest-x \
  -p 8000:8000 \
  -e ALLOWED_HOSTS="your-domain.com,localhost" \
  --restart unless-stopped \
  --user 1000:1000 \
  gitingest-x

# 方法2: 带持久化存储
docker run -d \
  --name gitingest-x \
  -p 8000:8000 \
  -e ALLOWED_HOSTS="your-domain.com,localhost" \
  -v gitingest_data:/tmp \
  --restart unless-stopped \
  gitingest-x

# 方法3: 带自定义网络
docker network create gitingest-network
docker run -d \
  --name gitingest-x \
  -p 8000:8000 \
  -e ALLOWED_HOSTS="your-domain.com,localhost" \
  --network gitingest-network \
  --restart unless-stopped \
  gitingest-x
```

### 构建优化

```bash
# 构建时指定平台（适用于多架构部署）
docker build --platform linux/amd64 -t gitingest-x .

# 使用 BuildKit 加速构建
DOCKER_BUILDKIT=1 docker build -t gitingest-x .

# 清理构建缓存
docker builder prune
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

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目基于 [Gitingest](https://github.com/cyclotruc/gitingest) 开发，采用 MIT 许可证。

## 🙏 致谢

感谢 [Gitingest](https://github.com/cyclotruc/gitingest) 项目提供的优秀基础。
