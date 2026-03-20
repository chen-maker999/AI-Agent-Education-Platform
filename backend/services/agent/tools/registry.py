"""Agent 工具注册表 - 统一管理所有工具定义和执行"""

import json
import httpx
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path


# 工具定义 - 符合 OpenAI function calling 格式
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "reading",
            "description": "对文件进行检索和查看",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要读取的文件路径（相对于项目根目录）"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "搜索文件内容的关键词（可选）"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "editing",
            "description": "对文件进行增删和编辑",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要编辑的文件路径"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["create", "edit", "delete"],
                        "description": "操作类型"
                    },
                    "content": {
                        "type": "string",
                        "description": "文件内容（用于创建或编辑）"
                    },
                    "old_string": {
                        "type": "string",
                        "description": "要替换的旧内容（用于编辑）"
                    },
                    "new_string": {
                        "type": "string",
                        "description": "替换后的新内容（用于编辑）"
                    }
                },
                "required": ["path", "action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "terminal",
            "description": "在终端运行命令并获取状态和结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的终端命令"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "命令执行的工作目录（可选）"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "preview",
            "description": "在生成前端结果后提供预览入口",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "预览标题"
                    },
                    "url": {
                        "type": "string",
                        "description": "预览链接"
                    },
                    "description": {
                        "type": "string",
                        "description": "预览描述"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索和用户任务相关的网页内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大返回结果数",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "download_to_knowledge",
            "description": "从网上下载资料（PDF、网页等）并保存到知识库。使用course_id='default'表示保存到默认知识库。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要下载的 URL（支持 PDF、网页、文档链接）"
                    },
                    "filename": {
                        "type": "string",
                        "description": "保存到知识库的文件名（不含扩展名）"
                    },
                    "course_id": {
                        "type": "string",
                        "description": "知识库课程 ID，用于分类存储。默认使用 'default' 保存到默认知识库。",
                        "default": "default"
                    }
                },
                "required": ["url", "filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "knowledge_search",
            "description": "搜索知识库中的相关资料。当用户询问需要查找资料、解释概念、回答与已上传文档相关的问题时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询词，尽量使用与用户问题相关的关键词"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回的最相关结果数量，默认5条",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# 工具 ID 到函数名的映射
TOOL_ID_TO_NAME = {
    "reading": "reading",
    "editing": "editing",
    "terminal": "terminal",
    "preview": "preview",
    "web_search": "web_search",
    "download_to_knowledge": "download_to_knowledge",
    "knowledge_search": "knowledge_search"
}


def get_tools_for_agent(enabled_tool_ids: List[str]) -> List[Dict[str, Any]]:
    """获取 Agent 启用的工具定义列表"""
    enabled_names = set(TOOL_ID_TO_NAME.get(tid, tid) for tid in enabled_tool_ids)
    return [t for t in TOOL_DEFINITIONS if t["function"]["name"] in enabled_names]


async def execute_tool(tool_name: str, arguments: Dict[str, Any], base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    执行工具调用

    Args:
        tool_name: 工具名称
        arguments: 工具参数
        base_url: 后端服务地址

    Returns:
        工具执行结果
    """
    from common.core.config import settings

    api_prefix = settings.API_PREFIX

    # 工具名称到 API 端点的映射
    tool_endpoints = {
        "reading": f"{base_url}{api_prefix}/agent/tools/read",
        "editing": f"{base_url}{api_prefix}/agent/tools/edit",
        "terminal": f"{base_url}{api_prefix}/agent/tools/terminal",
        "preview": f"{base_url}{api_prefix}/agent/tools/preview",
        "web_search": f"{base_url}{api_prefix}/agent/tools/web_search",
        "download_to_knowledge": f"{base_url}{api_prefix}/agent/tools/download_to_knowledge",
        "knowledge_search": f"{base_url}{api_prefix}/agent/tools/knowledge_search",
    }

    if tool_name not in tool_endpoints:
        return {"error": f"未知工具: {tool_name}"}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                tool_endpoints[tool_name],
                json=arguments,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    return result.get("data", {})
                else:
                    return {"error": result.get("message", "Unknown error")}
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
    except httpx.RequestError as e:
        return {"error": f"请求失败: {str(e)}"}
    except Exception as e:
        return {"error": f"执行失败: {str(e)}"}
