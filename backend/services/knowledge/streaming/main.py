"""流式输出服务 (P3-003) - 支持 SSE 和 WebSocket 实时输出"""

import asyncio
import json
import time
import uuid
from typing import AsyncGenerator, Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import hashlib

router = APIRouter(prefix="/stream", tags=["Streaming"])


# ==================== 数据结构 ====================
class StreamChunk(BaseModel):
    """流式输出数据块"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # "start", "retrieval", "rerank", "generation", "end", "error"
    data: Dict[str, Any]
    timestamp: float = Field(default_factory=time.time)
    session_id: Optional[str] = None


class StreamOptions(BaseModel):
    """流式输出配置"""
    include_retrieval: bool = True      # 包含检索过程
    include_rerank: bool = True         # 包含重排序过程
    include_sources: bool = True        # 包含来源信息
    include_stats: bool = True          # 包含统计信息
    chunk_size: int = 1                 # 生成块大小 (tokens)
    ping_interval: float = 30.0         # 心跳间隔 (秒)


# ==================== SSE 事件格式化 ====================
def format_sse_event(chunk: StreamChunk) -> str:
    """格式化 SSE 事件"""
    event_data = {
        "id": chunk.id,
        "type": chunk.type,
        "data": chunk.data,
        "timestamp": chunk.timestamp,
        "session_id": chunk.session_id
    }
    return f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"


def format_sse_comment(comment: str) -> str:
    """格式化 SSE 注释（心跳）"""
    return f": {comment}\n\n"


# ==================== 流式 RAG 处理器 ====================
class StreamingRAGProcessor:
    """流式 RAG 处理器"""

    def __init__(self, query: str, student_id: str, options: StreamOptions = None):
        self.query = query
        self.student_id = student_id
        self.options = options or StreamOptions()
        self.session_id = str(uuid.uuid4())
        self.start_time = None

    async def generate_stream(self) -> AsyncGenerator[str, None]:
        """生成 SSE 流"""
        self.start_time = time.time()

        try:
            # 1. 发送开始事件
            yield format_sse_event(StreamChunk(
                type="start",
                data={
                    "session_id": self.session_id,
                    "query": self.query,
                    "timestamp": datetime.utcnow().isoformat()
                },
                session_id=self.session_id
            ))

            # 2. 意图识别
            intent = "general"
            try:
                from services.knowledge.router.main import intent_classifier
                intent_result = await intent_classifier.classify(self.query)
                intent = intent_result.get("intent", "general")
                
                if self.options.include_retrieval:
                    yield format_sse_event(StreamChunk(
                        type="retrieval",
                        data={
                            "stage": "intent",
                            "intent": intent,
                            "confidence": intent_result.get("confidence", 0.0)
                        },
                        session_id=self.session_id
                    ))
            except Exception as e:
                print(f"意图识别失败：{e}")

            # 3. 多路检索
            retrieval_results = {
                "semantic": [],
                "keyword": [],
                "graph": []
            }

            if self.options.include_retrieval:
                yield format_sse_event(StreamChunk(
                    type="retrieval",
                    data={
                        "stage": "start",
                        "channels": ["semantic", "keyword", "graph"]
                    },
                    session_id=self.session_id
                ))

            # 并发执行检索
            retrieval_tasks = []
            
            # 语义检索
            retrieval_tasks.append(self._semantic_search())
            
            # 关键词检索
            retrieval_tasks.append(self._keyword_search())
            
            # 图谱检索（可选）
            if self.options.include_retrieval:
                retrieval_tasks.append(self._graph_search())

            try:
                results = await asyncio.gather(*retrieval_tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        print(f"检索任务 {i} 失败：{result}")
                        continue
                    
                    channel = ["semantic", "keyword", "graph"][i] if i < 3 else "unknown"
                    if result:
                        retrieval_results[channel] = result
                        
                        if self.options.include_retrieval:
                            yield format_sse_event(StreamChunk(
                                type="retrieval",
                                data={
                                    "stage": "channel_result",
                                    "channel": channel,
                                    "count": len(result),
                                    "results": result[:3]  # 只返回前 3 个
                                },
                                session_id=self.session_id
                            ))
            except Exception as e:
                print(f"并发检索失败：{e}")

            # 4. 结果融合
            fused_results = await self._fuse_results(retrieval_results)
            
            if self.options.include_retrieval:
                yield format_sse_event(StreamChunk(
                    type="retrieval",
                    data={
                        "stage": "fusion",
                        "method": "rrf",
                        "count": len(fused_results),
                        "results": fused_results[:5]
                    },
                    session_id=self.session_id
                ))

            # 5. 重排序
            reranked_results = await self._rerank_results(fused_results)
            
            if self.options.include_rerank:
                yield format_sse_event(StreamChunk(
                    type="rerank",
                    data={
                        "stage": "complete",
                        "count": len(reranked_results),
                        "results": reranked_results[:5]
                    },
                    session_id=self.session_id
                ))

            # 6. 构建上下文
            context_text = self._build_context(reranked_results)
            
            # 7. 流式生成回答
            async for generation_chunk in self._stream_generation(context_text):
                yield generation_chunk

            # 8. 发送结束事件
            total_time = time.time() - self.start_time
            yield format_sse_event(StreamChunk(
                type="end",
                data={
                    "session_id": self.session_id,
                    "total_time": total_time,
                    "stats": {
                        "retrieval_count": len(fused_results),
                        "rerank_count": len(reranked_results),
                        "intent": intent
                    }
                },
                session_id=self.session_id
            ))

        except Exception as e:
            # 发送错误事件
            yield format_sse_event(StreamChunk(
                type="error",
                data={
                    "error": str(e),
                    "type": type(e).__name__
                },
                session_id=self.session_id
            ))

    async def _semantic_search(self) -> List[Dict]:
        """语义检索"""
        try:
            from services.knowledge.rag.retriever import semantic_search
            results = await semantic_search(self.query, top_k=10)
            return results.get("results", [])
        except Exception as e:
            print(f"语义检索失败：{e}")
            return []

    async def _keyword_search(self) -> List[Dict]:
        """关键词检索"""
        try:
            from services.knowledge.rag.retriever import keyword_search
            results = await keyword_search(self.query, top_k=10)
            return results.get("results", [])
        except Exception as e:
            print(f"关键词检索失败：{e}")
            return []

    async def _graph_search(self) -> List[Dict]:
        """图谱检索"""
        try:
            from services.knowledge.rag.retriever import graph_search
            results = await graph_search(self.query)
            return results.get("results", [])
        except Exception as e:
            print(f"图谱检索失败：{e}")
            return []

    async def _fuse_results(self, results: Dict[str, List]) -> List[Dict]:
        """结果融合"""
        try:
            from services.knowledge.fusion.main import reciprocal_rank_fusion
            fused = await reciprocal_rank_fusion(
                results,
                top_k=15,
                k=60
            )
            return fused.get("results", [])
        except Exception as e:
            print(f"结果融合失败：{e}")
            # 降级：简单合并
            all_results = []
            for channel_results in results.values():
                all_results.extend(channel_results)
            return all_results[:15]

    async def _rerank_results(self, results: List[Dict]) -> List[Dict]:
        """重排序"""
        try:
            from services.knowledge.rerank.main import rerank_documents
            reranked = await rerank_documents(self.query, results, top_k=10)
            return reranked.get("results", [])
        except Exception as e:
            print(f"重排序失败：{e}")
            return results[:10]

    def _build_context(self, results: List[Dict]) -> str:
        """构建上下文"""
        context_parts = []
        for i, result in enumerate(results[:10], 1):
            content = result.get("content", "")
            score = result.get("score", 0)
            channel = result.get("channel", "unknown")
            
            context_parts.append(
                f"【参考{i}】(来源：{channel}, 分数：{score:.3f})\n{content}"
            )
        
        return "\n\n".join(context_parts)

    async def _stream_generation(self, context: str) -> AsyncGenerator[str, None]:
        """流式生成回答"""
        try:
            from common.integration.kimi import kimi_client
            
            prompt = f"""你是一个智能教学助手。根据以下参考知识回答学生问题。

## 参考知识
{context}

## 学生问题
{self.query}

## 要求
1. 用中文回答，简洁准确
2. 基于参考知识回答，不要编造
3. 如果参考知识不足，请说明
4. 适当鼓励学生"""

            system_prompt = "你是一位专业的编程教师，擅长用简洁易懂的语言解释编程概念。"

            # 使用 Kimi 流式生成
            async for chunk in kimi_client.chat_stream(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000
            ):
                yield format_sse_event(StreamChunk(
                    type="generation",
                    data={
                        "content": chunk,
                        "session_id": self.session_id
                    },
                    session_id=self.session_id
                ))

        except Exception as e:
            print(f"流式生成失败：{e}")
            # 降级：使用普通生成
            try:
                from common.integration.kimi import get_kimi_response
                answer = await get_kimi_response(
                    prompt=f"""根据以下知识回答问题：

{context}

问题：{self.query}""",
                    system_prompt="你是一位专业的编程教师"
                )
                
                # 将整个答案作为一个块发送
                yield format_sse_event(StreamChunk(
                    type="generation",
                    data={
                        "content": answer,
                        "session_id": self.session_id,
                        "fallback": True
                    },
                    session_id=self.session_id
                ))
            except Exception as e2:
                print(f"降级生成失败：{e2}")
                yield format_sse_event(StreamChunk(
                    type="generation",
                    data={
                        "content": "抱歉，生成回答时遇到错误。",
                        "session_id": self.session_id,
                        "error": True
                    },
                    session_id=self.session_id
                ))


# ==================== API 接口 ====================
@router.post("/chat")
async def stream_chat(
    request: Request,
    query: str,
    student_id: str,
    include_retrieval: bool = True,
    include_rerank: bool = True,
    include_sources: bool = True,
    include_stats: bool = True
):
    """
    流式 RAG 对话 - SSE
    
    使用 Server-Sent Events 实时输出 RAG 处理过程和生成结果。
    
    事件类型:
    - start: 开始处理
    - retrieval: 检索过程（意图识别、各渠道检索、融合）
    - rerank: 重排序过程
    - generation: 生成回答（多个 chunk）
    - end: 处理完成
    - error: 发生错误
    """
    options = StreamOptions(
        include_retrieval=include_retrieval,
        include_rerank=include_rerank,
        include_sources=include_sources,
        include_stats=include_stats
    )

    processor = StreamingRAGProcessor(
        query=query,
        student_id=student_id,
        options=options
    )

    return StreamingResponse(
        processor.generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Nginx 不缓冲
        }
    )


@router.post("/chat/stream")
async def stream_chat_simple(
    request: Request,
    query: str,
    student_id: str
):
    """简化版流式对话 - 只输出最终答案"""
    
    async def simple_generate() -> AsyncGenerator[str, None]:
        try:
            # 开始事件
            yield format_sse_event(StreamChunk(
                type="start",
                data={"query": query},
                session_id=str(uuid.uuid4())
            ))

            # 普通 RAG 处理
            from services.knowledge.rag.main import process_rag_request
            from services.knowledge.rag.main import RAGRequest
            
            rag_request = RAGRequest(
                query=query,
                student_id=student_id,
                top_k=5
            )
            
            result = await process_rag_request(rag_request)
            
            # 发送答案
            yield format_sse_event(StreamChunk(
                type="generation",
                data={
                    "content": result["answer"],
                    "sources": result.get("sources", [])
                },
                session_id=result.get("session_id")
            ))

            # 结束事件
            yield format_sse_event(StreamChunk(
                type="end",
                data={
                    "processing_time": result.get("processing_time", 0)
                },
                session_id=result.get("session_id")
            ))

        except Exception as e:
            yield format_sse_event(StreamChunk(
                type="error",
                data={"error": str(e)},
                session_id=None
            ))

    return StreamingResponse(
        simple_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.get("/demo")
async def streaming_demo():
    """流式输出演示页面"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAG 流式输出演示</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; }
            #output { border: 1px solid #ddd; padding: 20px; min-height: 200px; margin-top: 20px; }
            .chunk { margin: 5px 0; padding: 5px; background: #f5f5f5; border-radius: 3px; }
            .type-start { background: #e3f2fd; }
            .type-retrieval { background: #fff3e0; }
            .type-rerank { background: #f3e5f5; }
            .type-generation { background: #e8f5e9; }
            .type-end { background: #ffebee; }
            .type-error { background: #ffcdd2; }
            button { padding: 10px 20px; font-size: 16px; cursor: pointer; }
            input { padding: 10px; width: 60%; margin-right: 10px; }
        </style>
    </head>
    <body>
        <h1>RAG 流式输出演示</h1>
        <div>
            <input type="text" id="queryInput" placeholder="输入问题..." value="什么是 Python？">
            <button onclick="startStreaming()">开始流式输出</button>
        </div>
        <div id="output"></div>
        
        <script>
            let eventSource = null;
            
            function startStreaming() {
                const query = document.getElementById('queryInput').value;
                const output = document.getElementById('output');
                output.innerHTML = '';
                
                if (eventSource) {
                    eventSource.close();
                }
                
                const url = `/api/v1/stream/chat?query=${encodeURIComponent(query)}&student_id=demo_user`;
                eventSource = new EventSource(url);
                
                eventSource.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    const chunkDiv = document.createElement('div');
                    chunkDiv.className = `chunk type-${data.type}`;
                    chunkDiv.innerHTML = `
                        <strong>[${data.type}]</strong> 
                        ${JSON.stringify(data.data, null, 2).replace(/\\n/g, '<br>')}
                        <small>(${new Date(data.timestamp * 1000).toLocaleTimeString()})</small>
                    `;
                    output.appendChild(chunkDiv);
                    output.scrollTop = output.scrollHeight;
                    
                    if (data.type === 'end' || data.type === 'error') {
                        eventSource.close();
                    }
                };
                
                eventSource.onerror = function(error) {
                    console.error('SSE Error:', error);
                    eventSource.close();
                };
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# 导入 HTMLResponse
from fastapi.responses import HTMLResponse
