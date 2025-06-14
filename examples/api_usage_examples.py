#!/usr/bin/env python3
"""
Gitingest API使用示例

本脚本演示如何使用Gitingest的REST API接口来摄入Git仓库。
运行前请确保Gitingest服务器正在运行。
"""

import json
import requests
import time
from typing import Dict, Any, Optional


class GitingestAPIClient:
    """Gitingest API客户端智能体"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化API客户端
        
        Args:
            base_url: Gitingest服务器的基础URL
        """
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api/v1"
    
    def health_check(self) -> Dict[str, Any]:
        """检查API服务健康状态"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e), "status": "unhealthy"}
    
    def ingest_repository(
        self,
        source: str,
        max_file_size: Optional[int] = None,
        include_patterns: Optional[list] = None,
        exclude_patterns: Optional[list] = None,
        branch: Optional[str] = None,
        method: str = "POST"
    ) -> Dict[str, Any]:
        """
        摄入Git仓库
        
        Args:
            source: Git仓库URL或本地路径
            max_file_size: 最大文件大小(字节)
            include_patterns: 包含模式列表
            exclude_patterns: 排除模式列表 
            branch: 指定分支
            method: HTTP方法 ("POST" 或 "GET")
            
        Returns:
            API响应的字典
        """
        if method.upper() == "POST":
            return self._ingest_post(source, max_file_size, include_patterns, exclude_patterns, branch)
        else:
            return self._ingest_get(source, max_file_size, include_patterns, exclude_patterns, branch)
    
    def _ingest_post(self, source: str, max_file_size: Optional[int], 
                     include_patterns: Optional[list], exclude_patterns: Optional[list],
                     branch: Optional[str]) -> Dict[str, Any]:
        """使用POST方法摄入仓库"""
        data = {"source": source}
        
        if max_file_size is not None:
            data["max_file_size"] = max_file_size
        if include_patterns:
            data["include_patterns"] = include_patterns
        if exclude_patterns:
            data["exclude_patterns"] = exclude_patterns
        if branch:
            data["branch"] = branch
            
        try:
            response = requests.post(
                f"{self.api_base}/ingest",
                json=data,
                timeout=120  # 2分钟超时
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def _ingest_get(self, source: str, max_file_size: Optional[int],
                    include_patterns: Optional[list], exclude_patterns: Optional[list],
                    branch: Optional[str]) -> Dict[str, Any]:
        """使用GET方法摄入仓库"""
        params = {"source": source}
        
        if max_file_size is not None:
            params["max_file_size"] = max_file_size
        if include_patterns:
            params["include_patterns"] = ",".join(include_patterns)
        if exclude_patterns:
            params["exclude_patterns"] = ",".join(exclude_patterns)
        if branch:
            params["branch"] = branch
            
        try:
            response = requests.get(
                f"{self.api_base}/ingest",
                params=params,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def get_summary(self, source: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """
        获取仓库摘要信息(轻量级)
        
        Args:
            source: Git仓库URL或本地路径
            branch: 指定分支
            
        Returns:
            包含摘要信息的字典
        """
        params = {"source": source}
        if branch:
            params["branch"] = branch
            
        try:
            response = requests.get(
                f"{self.api_base}/ingest/summary",
                params=params,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}


def example_basic_usage():
    """基础使用示例"""
    print("=== 基础使用示例 ===")
    
    client = GitingestAPIClient()
    
    # 健康检查
    health = client.health_check()
    print(f"健康状态: {health}")
    
    if health.get("status") != "healthy":
        print("❌ API服务不可用，请检查服务器是否启动")
        return
    
    # 摄入一个小型示例仓库
    print("\n正在摄入示例仓库...")
    result = client.ingest_repository(
        source="https://github.com/octocat/Hello-World",
        include_patterns=["*.md", "*.txt"],
        max_file_size=1024 * 1024  # 1MB
    )
    
    if result.get("success"):
        print("✅ 摄入成功！")
        print(f"📊 摘要:\n{result['data']['summary']}")
        print(f"\n🌳 目录结构:\n{result['data']['tree']}")
        print(f"\n📄 内容长度: {len(result['data']['content'])} 字符")
    else:
        print(f"❌ 摄入失败: {result.get('error')}")


def example_advanced_usage():
    """高级使用示例"""
    print("\n=== 高级使用示例 ===")
    
    client = GitingestAPIClient()
    
    # 使用复杂的过滤模式
    print("正在摄入Python项目的特定文件...")
    result = client.ingest_repository(
        source="https://github.com/tiangolo/fastapi",
        include_patterns=["*.py", "*.md", "*.toml"],
        exclude_patterns=["**/tests/**", "**/test_*", "**/__pycache__/**"],
        max_file_size=100 * 1024,  # 100KB
        branch="master"
    )
    
    if result.get("success"):
        print("✅ 高级摄入成功！")
        print(f"📊 摘要:\n{result['data']['summary']}")
        
        # 分析结果
        metadata = result.get("metadata", {})
        print(f"\n📋 元数据:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
    else:
        print(f"❌ 摄入失败: {result.get('error')}")


def example_summary_only():
    """仅获取摘要的示例"""
    print("\n=== 轻量级摘要示例 ===")
    
    client = GitingestAPIClient()
    
    print("获取仓库摘要信息...")
    summary = client.get_summary(
        source="https://github.com/cyclotruc/gitingest",
        branch="main"
    )
    
    if "error" not in summary:
        print("✅ 摘要获取成功！")
        print(f"📊 仓库: {summary.get('repository')}")
        print(f"🌿 分支: {summary.get('branch')}")
        print(f"📄 摘要:\n{summary.get('summary')}")
    else:
        print(f"❌ 获取摘要失败: {summary.get('error')}")


def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    client = GitingestAPIClient()
    
    # 测试无效URL
    print("测试无效仓库URL...")
    result = client.ingest_repository(source="invalid-url")
    
    if not result.get("success"):
        print(f"✅ 正确捕获错误: {result.get('error')}")
    
    # 测试不存在的仓库
    print("\n测试不存在的仓库...")
    result = client.ingest_repository(source="https://github.com/nonexistent/repo")
    
    if not result.get("success"):
        print(f"✅ 正确处理不存在的仓库: {result.get('error')}")


def example_get_vs_post():
    """对比GET和POST方法"""
    print("\n=== GET vs POST方法对比 ===")
    
    client = GitingestAPIClient()
    
    source = "https://github.com/octocat/Hello-World"
    
    # 使用POST方法
    print("使用POST方法...")
    start_time = time.time()
    post_result = client.ingest_repository(source=source, method="POST")
    post_time = time.time() - start_time
    
    # 使用GET方法  
    print("使用GET方法...")
    start_time = time.time()
    get_result = client.ingest_repository(source=source, method="GET")
    get_time = time.time() - start_time
    
    print(f"POST方法耗时: {post_time:.2f}秒")
    print(f"GET方法耗时: {get_time:.2f}秒")
    
    if post_result.get("success") and get_result.get("success"):
        print("✅ 两种方法都成功返回结果")
    else:
        print("❌ 某种方法失败")


def main():
    """主函数"""
    print("🚀 Gitingest API 使用示例")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_advanced_usage()
        example_summary_only()
        example_error_handling()
        example_get_vs_post()
        
        print("\n" + "=" * 50)
        print("✅ 所有示例执行完成！")
        
    except KeyboardInterrupt:
        print("\n❌ 用户中断执行")
    except Exception as e:
        print(f"\n❌ 执行过程中出现错误: {e}")


if __name__ == "__main__":
    main() 