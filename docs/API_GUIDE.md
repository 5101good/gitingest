# Gitingest REST API 使用指南

本指南详细介绍如何使用 Gitingest 的 REST API 端点来程序化地摄入 Git 仓库。

## 🚀 快速开始

### 启动服务

```bash
# 在项目根目录
cd src
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

### 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

## 📡 API 端点

### 1. POST /api/v1/ingest

**功能**: 摄入 Git 仓库并返回完整的结构化结果

**请求体**:
```json
{
  "source": "https://github.com/user/repo",
  "max_file_size": 10485760,
  "include_patterns": ["*.py", "*.md"],
  "exclude_patterns": ["*.log", "temp/**"],
  "branch": "main"
}
```

**参数说明**:
- `source` (必需): Git 仓库 URL 或本地路径
- `max_file_size` (可选): 最大文件大小，范围 1KB-100MB，默认 10MB
- `include_patterns` (可选): 包含模式数组，Unix shell 风格通配符
- `exclude_patterns` (可选): 排除模式数组，Unix shell 风格通配符  
- `branch` (可选): 指定分支名称

**响应示例**:
```json
{
  "success": true,
  "data": {
    "summary": "Repository: user/repo\nFiles analyzed: 25\nEstimated tokens: 1.2k",
    "tree": "repo/\n├── src/\n│   ├── main.py\n│   └── utils.py\n└── README.md",
    "content": "FILE: src/main.py\n...\n\nFILE: README.md\n..."
  },
  "metadata": {
    "source_type": "remote",
    "repository": "user/repo", 
    "branch": "main",
    "subpath": "/"
  }
}
```

**cURL 示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "https://github.com/cyclotruc/gitingest",
    "max_file_size": 5242880,
    "include_patterns": ["*.py", "*.md"]
  }'
```

### 2. GET /api/v1/ingest

**功能**: 使用 URL 参数进行仓库摄入

**请求示例**:
```
GET /api/v1/ingest?source=https://github.com/user/repo&branch=main&include_patterns=*.py,*.md&max_file_size=5242880
```

**参数说明**:
- `source` (必需): Git 仓库 URL 或本地路径
- `max_file_size` (可选): 最大文件大小(字节)
- `include_patterns` (可选): 逗号分隔的包含模式
- `exclude_patterns` (可选): 逗号分隔的排除模式
- `branch` (可选): 指定分支

**cURL 示例**:
```bash
curl "http://localhost:8000/api/v1/ingest?source=https://github.com/octocat/Hello-World&include_patterns=*.md"
```

### 3. GET /api/v1/ingest/summary

**功能**: 获取轻量级摘要信息(不包含完整内容)

**请求示例**:
```
GET /api/v1/ingest/summary?source=https://github.com/user/repo&branch=main
```

**响应示例**:
```json
{
  "source": "https://github.com/user/repo",
  "summary": "Repository: user/repo\nFiles analyzed: 25\nEstimated tokens: 1.2k",
  "repository": "user/repo",
  "branch": "main"
}
```

**cURL 示例**:
```bash
curl "http://localhost:8000/api/v1/ingest/summary?source=https://github.com/cyclotruc/gitingest"
```

### 4. GET /api/v1/health

**功能**: API 健康检查

**响应**:
```json
{
  "status": "healthy",
  "service": "gitingest-api"
}
```

## 🛡️ 速率限制

- `POST/GET /api/v1/ingest`: 5 次/分钟
- `GET /api/v1/ingest/summary`: 10 次/分钟

## 📝 使用示例

### Python 客户端

```python
import requests

# 基础使用
response = requests.post("http://localhost:8000/api/v1/ingest", json={
    "source": "https://github.com/octocat/Hello-World",
    "include_patterns": ["*.md"],
    "max_file_size": 1048576  # 1MB
})

data = response.json()
if data["success"]:
    print("摘要:", data["data"]["summary"])
    print("目录结构:", data["data"]["tree"])
else:
    print("错误:", data["error"])
```

### JavaScript/Node.js

```javascript
const response = await fetch('http://localhost:8000/api/v1/ingest', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    source: 'https://github.com/octocat/Hello-World',
    include_patterns: ['*.md'],
    max_file_size: 1048576
  })
});

const data = await response.json();
if (data.success) {
  console.log('摘要:', data.data.summary);
  console.log('目录结构:', data.data.tree);
} else {
  console.log('错误:', data.error);
}
```

## 🧪 运行测试

### 单元测试

```bash
# 在项目根目录
pytest tests/test_api_endpoints.py -v
```

### 集成测试(需要网络访问)

```bash
pytest tests/test_api_endpoints.py::TestAPIIntegration -v -m integration
```

### 运行示例

```bash
cd examples
python api_usage_examples.py
```

## 🔧 错误处理

### 常见错误码

- `400`: 请求参数无效
- `422`: 请求验证失败  
- `429`: 超出速率限制
- `500`: 服务器内部错误

### 错误响应格式

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

或者标准 FastAPI 错误格式:

```json
{
  "detail": "错误详情"
}
```

## 🎯 最佳实践

### 1. 选择合适的端点

- **完整摄入**: 使用 `POST /api/v1/ingest` 获取完整结果
- **快速概览**: 使用 `GET /api/v1/ingest/summary` 获取摘要
- **简单测试**: 使用 `GET /api/v1/ingest` 进行快速测试

### 2. 优化性能

```python
# 限制文件大小以提高速度
"max_file_size": 1048576  # 1MB

# 使用模式过滤减少处理量
"include_patterns": ["*.py", "*.md", "*.toml"]
"exclude_patterns": ["**/tests/**", "**/__pycache__/**"]
```

## 📚 相关资源

- [交互式 API 文档](http://localhost:8000/docs) - 启动服务后访问
- [API 端点列表](http://localhost:8000/api) - Web 版本文档
- [GitHub 仓库](https://github.com/cyclotruc/gitingest)
- [使用示例脚本](../examples/api_usage_examples.py) 