"""Agent 内置工具 - 阅读、编辑、终端、预览、联网搜索"""

import os
import subprocess
import asyncio
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from common.models.response import ResponseModel
import httpx

router = APIRouter(prefix="/agent/tools", tags=["Agent Tools"])

# 允许读写的工作区根目录（限制在项目内）
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]  # backend/services/agent/tools -> backend
AGENT_WORKSPACE = WORKSPACE_ROOT / "data" / "agent_workspace"
AGENT_WORKSPACE.mkdir(parents=True, exist_ok=True)


def _resolve_path(relative_path: str) -> Path:
    """解析为绝对路径并确保在工作区内"""
    p = (AGENT_WORKSPACE / relative_path).resolve()
    try:
        p.relative_to(AGENT_WORKSPACE)
    except ValueError:
        raise HTTPException(status_code=403, detail="路径超出允许范围")
    return p


# ---------- 1. 阅读 ----------
class ReadRequest(BaseModel):
    path: str = Field(..., description="相对工作区的文件路径")
    encoding: str = Field("utf-8", description="文件编码")


@router.post("/read", response_model=ResponseModel)
async def tool_read(req: ReadRequest):
    """对文件进行检索和查看"""
    try:
        fp = _resolve_path(req.path)
        if not fp.exists():
            return ResponseModel(code=404, message="文件不存在", data={"path": req.path})
        if not fp.is_file():
            return ResponseModel(code=400, message="路径不是文件", data={"path": req.path})
        content = fp.read_text(encoding=req.encoding, errors="replace")
        lines = content.splitlines()
        return ResponseModel(
            code=200,
            message="success",
            data={
                "path": req.path,
                "content": content,
                "lines": len(lines),
                "preview": content[:2000] + ("..." if len(content) > 2000 else ""),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- 2. 编辑 ----------
class EditReplaceRequest(BaseModel):
    path: str = Field(..., description="相对工作区的文件路径")
    old_string: str = Field(..., description="要替换的原文")
    new_string: str = Field(..., description="新内容")


class EditWriteRequest(BaseModel):
    path: str = Field(..., description="相对工作区的文件路径")
    content: str = Field(..., description="写入的完整内容")


@router.post("/edit", response_model=ResponseModel)
async def tool_edit_replace(req: EditReplaceRequest):
    """对文件进行替换编辑"""
    try:
        fp = _resolve_path(req.path)
        if not fp.exists():
            return ResponseModel(code=404, message="文件不存在", data={"path": req.path})
        text = fp.read_text(encoding="utf-8", errors="replace")
        if req.old_string not in text:
            return ResponseModel(code=400, message="未找到要替换的内容", data={"path": req.path})
        new_text = text.replace(req.old_string, req.new_string, 1)
        fp.write_text(new_text, encoding="utf-8")
        return ResponseModel(code=200, message="编辑成功", data={"path": req.path})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edit/write", response_model=ResponseModel)
async def tool_edit_write(req: EditWriteRequest):
    """对文件进行整篇写入（覆盖）"""
    try:
        fp = _resolve_path(req.path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(req.content, encoding="utf-8")
        return ResponseModel(code=200, message="写入成功", data={"path": req.path})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- 3. 终端 ----------
class TerminalRequest(BaseModel):
    command: str = Field(..., description="要执行的命令")
    timeout_seconds: int = Field(30, ge=1, le=120, description="超时秒数")


@router.post("/terminal", response_model=ResponseModel)
async def tool_terminal(req: TerminalRequest):
    """在终端运行命令并获取状态和结果"""
    try:
        proc = await asyncio.create_subprocess_shell(
            req.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(AGENT_WORKSPACE),
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=req.timeout_seconds
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return ResponseModel(
                code=408,
                message="命令执行超时",
                data={"command": req.command},
            )
        out = (stdout or b"").decode("utf-8", errors="replace")
        err = (stderr or b"").decode("utf-8", errors="replace")
        return ResponseModel(
            code=200,
            message="success",
            data={
                "command": req.command,
                "stdout": out,
                "stderr": err,
                "returncode": proc.returncode,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- 4. 预览 ----------
class PreviewRequest(BaseModel):
    url: Optional[str] = Field(None, description="要预览的 URL")
    html: Optional[str] = Field(None, description="要预览的 HTML 片段（与 url 二选一）")
    title: Optional[str] = Field("预览", description="预览标题")


@router.post("/preview", response_model=ResponseModel)
async def tool_preview(req: PreviewRequest):
    """在生成前端结果后提供预览入口"""
    if req.url:
        return ResponseModel(
            code=200,
            message="success",
            data={
                "type": "url",
                "url": req.url,
                "title": req.title or "预览",
            },
        )
    if req.html:
        # 返回 HTML 片段，前端可放入 iframe 或新窗口
        return ResponseModel(
            code=200,
            message="success",
            data={
                "type": "html",
                "html": req.html[:500000],  # 限制长度
                "title": req.title or "预览",
            },
        )
    raise HTTPException(status_code=400, detail="请提供 url 或 html")


# ---------- 5. 联网搜索 ----------
class WebSearchRequest(BaseModel):
    query: str = Field(..., description="搜索关键词")
    max_results: int = Field(10, ge=1, le=20, description="最多返回条数")


@router.post("/web_search", response_model=ResponseModel)
async def tool_web_search(req: WebSearchRequest):
    """搜索和用户任务相关的网页内容"""
    try:
        results = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        # 优先尝试 DuckDuckGo
        try:
            url = "https://api.duckduckgo.com/"
            params = {"q": req.query, "format": "json", "no_html": 1}
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(url, params=params, headers=headers)
                r.raise_for_status()
                data = r.json()

            # 即时答案
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", "摘要"),
                    "link": data.get("AbstractURL", ""),
                    "snippet": data.get("AbstractText", ""),
                })

            # 相关主题
            for topic in (data.get("RelatedTopics") or [])[: req.max_results - len(results)]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "")[:80],
                        "link": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                    })
                elif isinstance(topic, dict) and topic.get("Topics"):
                    for t in topic["Topics"][:2]:
                        if t.get("Text"):
                            results.append({
                                "title": t.get("Text", "")[:80],
                                "link": t.get("FirstURL", ""),
                                "snippet": t.get("Text", ""),
                            })
                            if len(results) >= req.max_results:
                                break
                if len(results) >= req.max_results:
                    break

        except Exception:
            # DuckDuckGo 不可用，尝试 Bing
            try:
                from bs4 import BeautifulSoup
                from urllib.parse import quote

                search_url = f"https://cn.bing.com/search?q={quote(req.query)}"
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    r = await client.get(search_url, headers=headers)
                    r.raise_for_status()

                soup = BeautifulSoup(r.text, 'html.parser')

                # 提取搜索结果
                for item in soup.select('.b_algo')[:req.max_results]:
                    title_elem = item.select_one('h2 a')
                    snippet_elem = item.select_one('.b_caption p')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '')
                        snippet = ""
                        if snippet_elem:
                            snippet = snippet_elem.get_text(strip=True)
                        results.append({
                            "title": title,
                            "link": link,
                            "snippet": snippet[:200] if snippet else "",
                        })

            except Exception:
                pass

        if not results:
            results.append({
                "title": "未找到结果",
                "link": "",
                "snippet": f"对「{req.query}」的搜索暂无结果。",
            })

        return ResponseModel(
            code=200,
            message="success",
            data={"query": req.query, "results": results[: req.max_results]},
        )

    except Exception as e:
        # 降级：返回提示信息
        return ResponseModel(
            code=200,
            message="success",
            data={
                "query": req.query,
                "results": [
                    {
                        "title": "联网搜索暂时不可用",
                        "link": "",
                        "snippet": f"请求外部搜索时出错: {str(e)}。请检查网络或稍后重试。",
                    }
                ],
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- 6. 下载资料到知识库 ----------
class DownloadToKnowledgeRequest(BaseModel):
    url: str = Field(..., description="要下载的 URL（支持 PDF、网页、文档链接）")
    filename: str = Field(..., description="保存到知识库的文件名（不含扩展名）")
    course_id: str = Field("default", description="知识库课程 ID")


@router.post("/download_to_knowledge", response_model=ResponseModel)
async def tool_download_to_knowledge(req: DownloadToKnowledgeRequest):
    """
    下载网上资料（PDF、网页等）并保存到知识库
    
    支持的 URL 类型：
    - PDF 文件：自动解析并保存
    - arXiv 论文：自动下载 PDF
    - 网页：提取正文内容并保存
    - GitHub 文件：下载源码文件
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    
    from services.knowledge.rag.main import process_file_upload
    
    print(f"[DEBUG download_to_knowledge] url={req.url}, filename={req.filename}, course_id={req.course_id}", flush=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.get(req.url, headers=headers)
            response.raise_for_status()
            
            raw_content = response.content
            content_type = response.headers.get("content-type", "").lower()
            
            print(f"[DEBUG download_to_knowledge] status={response.status_code}, content-type={content_type}, size={len(raw_content)}", flush=True)
            
            # 根据内容类型处理
            filename = req.filename
            
            # PDF 文件
            if "pdf" in content_type or req.url.lower().endswith(".pdf"):
                filename = f"{filename}.pdf"
                # 直接上传 PDF 到知识库
                result = await process_file_upload(raw_content, filename, req.course_id)
                
                return ResponseModel(
                    code=200,
                    message="success",
                    data={
                        "type": "pdf",
                        "filename": filename,
                        "doc_count": result.get("total_chunks", 1),
                        "doc_ids": result.get("doc_ids", []),
                        "size": len(raw_content),
                        "url": req.url,
                    }
                )
            
            # HTML 网页
            elif "text/html" in content_type:
                # 尝试解析 HTML 内容
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(raw_content, 'html.parser')
                    
                    # 移除脚本和样式
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # 获取正文
                    text = soup.get_text(separator="\n", strip=True)
                    
                    # 清理空白
                    lines = [line for line in text.splitlines() if line.strip()]
                    text = "\n".join(lines)
                    
                    filename = f"{filename}.txt"
                    
                    # 保存为文本文件
                    result = await process_file_upload(text.encode("utf-8"), filename, req.course_id)
                    
                    return ResponseModel(
                        code=200,
                        message="success",
                        data={
                            "type": "webpage",
                            "filename": filename,
                            "doc_count": result.get("total_chunks", 1),
                            "doc_ids": result.get("doc_ids", []),
                            "size": len(raw_content),
                            "url": req.url,
                            "preview": text[:500] if text else "",
                        }
                    )
                except ImportError:
                    # 如果没有 BeautifulSoup，保存原始内容
                    text = raw_content.decode("utf-8", errors="replace")
                    filename = f"{filename}.html"
                    result = await process_file_upload(raw_content, filename, req.course_id)
                    
                    return ResponseModel(
                        code=200,
                        message="success",
                        data={
                            "type": "html_raw",
                            "filename": filename,
                            "doc_count": result.get("total_chunks", 1),
                            "doc_ids": result.get("doc_ids", []),
                            "size": len(raw_content),
                            "url": req.url,
                        }
                    )
            
            # 其他类型（如纯文本）
            else:
                filename = f"{filename}.txt"
                text = raw_content.decode("utf-8", errors="replace")
                result = await process_file_upload(text.encode("utf-8"), filename, req.course_id)
                
                return ResponseModel(
                    code=200,
                    message="success",
                    data={
                        "type": "text",
                        "filename": filename,
                        "doc_count": result.get("total_chunks", 1),
                        "doc_ids": result.get("doc_ids", []),
                        "size": len(raw_content),
                        "url": req.url,
                    }
                )
                
    except httpx.TimeoutException:
        return ResponseModel(
            code=408,
            message="下载超时，请检查URL是否可访问",
            data={"url": req.url}
        )
    except httpx.HTTPStatusError as e:
        return ResponseModel(
            code=502,
            message=f"下载失败: HTTP {e.response.status_code}",
            data={"url": req.url, "status_code": e.response.status_code}
        )
    except ImportError as e:
        return ResponseModel(
            code=500,
            message=f"缺少必要的依赖: {str(e)}",
            data={}
        )
    except Exception as e:
        import traceback
        print(f"[ERROR download_to_knowledge] {traceback.format_exc()}", flush=True)
        return ResponseModel(
            code=500,
            message=f"下载失败: {str(e)}",
            data={"url": req.url}
        )


# ---------- 7. 知识库检索 ----------
class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询词")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数量")


@router.post("/knowledge_search", response_model=ResponseModel)
async def tool_knowledge_search(req: KnowledgeSearchRequest):
    """
    搜索知识库中的相关资料

    这个工具允许 Agent 在需要时查询知识库，获取与用户问题相关的文档内容。
    当用户询问需要查找资料、解释概念、回答与已上传文档相关的问题时使用。
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

    from services.knowledge.rag.main import RAGRequest, process_rag_request

    print(f"[DEBUG knowledge_search] query={req.query}, top_k={req.top_k}", flush=True)

    try:
        rag_request = RAGRequest(
            query=req.query,
            student_id="agent",
            course_id="default",
            top_k=req.top_k,
            use_rewrite=False,
            use_rerank=False
        )

        result = await process_rag_request(rag_request)

        sources = result.get("sources", [])
        formatted_results = []
        for i, s in enumerate(sources[:req.top_k]):
            metadata = s.get("doc_metadata", {})
            formatted_results.append({
                "rank": i + 1,
                "source": metadata.get("filename", "未知来源"),
                "content": s.get("content", ""),
                "score": s.get("score", 0.0),
                "chunk_index": metadata.get("chunk_index", 0)
            })

        return ResponseModel(
            code=200,
            message="success",
            data={
                "query": req.query,
                "total_results": len(formatted_results),
                "results": formatted_results,
                "summary": f"在知识库中找到 {len(formatted_results)} 条相关内容"
            }
        )

    except Exception as e:
        import traceback
        print(f"[ERROR knowledge_search] {traceback.format_exc()}", flush=True)
        return ResponseModel(
            code=500,
            message=f"知识库检索失败: {str(e)}",
            data={"query": req.query, "results": []}
        )


@router.get("/list", response_model=ResponseModel)
async def list_builtin_tools():
    """返回内置工具列表（供前端默认勾选）"""
    tools = [
        {"id": "reading", "name": "阅读", "desc": "对文件进行检索和查看"},
        {"id": "editing", "name": "编辑", "desc": "对文件进行增删和编辑"},
        {"id": "terminal", "name": "终端", "desc": "在终端运行命令并获取状态和结果"},
        {"id": "preview", "name": "预览", "desc": "在生成前端结果后提供预览入口"},
        {"id": "web_search", "name": "联网搜索", "desc": "搜索和用户任务相关的网页内容"},
        {"id": "download_to_knowledge", "name": "下载资料", "desc": "从网上下载资料（PDF、网页）并保存到知识库"},
        {"id": "knowledge_search", "name": "知识库检索", "desc": "搜索知识库中的相关资料"},
    ]
    return ResponseModel(code=200, message="success", data={"tools": tools})
