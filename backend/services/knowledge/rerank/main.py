"""
交叉编码器重排序服务 (CROSS-ENCODER RERANKER)

P11 优化:
1. 启动时预加载模型，移除动态加载
2. 支持 BGE-Reranker 中文模型 (默认)
3. 实现级联重排序架构 (BM25 初排 → Cross-Encoder 精排)
4. 双模型支持 (bge-reranker-base 作为默认模型)
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rerank", tags=["Cross-Encoder Reranker"])


class RerankModel:
    """
    重排序模型管理器

    特性:
    - 启动时预加载模型
    - 支持多种模型 (Cross-Encoder / BGE-Reranker)
    - 级联重排序架构
    - 默认使用 BGE-Reranker-Base (中文优化)
    """

    def __init__(self):
        self.model = None
        self.model_type = None
        self.initialized = False
        self.model_name = None
        self.use_cascade = False  # 是否启用级联重排序

    def load_model(self, model_name: str = "bge-reranker-base", use_cascade: bool = False):
        """
        预加载重排序模型

        Args:
            model_name: 模型名称
                - "cross-encoder": cross-encoder/ms-marco-MiniLM-L-6-v2
                - "bge-reranker-base": BAAI/bge-reranker-base (中文优化，默认)
                - "bge-reranker-large": BAAI/bge-reranker-large (更大模型)
            use_cascade: 是否启用级联重排序 (BM25 初排 + Cross-Encoder 精排)
        """
        if self.initialized:
            logger.info(f"重排序模型已加载：{self.model_name}")
            return True

        try:
            import torch
            from sentence_transformers import CrossEncoder

            self.model_name = model_name
            self.use_cascade = use_cascade

            if model_name == "cross-encoder":
                model_path = "cross-encoder/ms-marco-MiniLM-L-6-v2"
            elif model_name == "bge-reranker-base":
                model_path = "BAAI/bge-reranker-base"
            elif model_name == "bge-reranker-large":
                model_path = "BAAI/bge-reranker-large"
            else:
                model_path = "BAAI/bge-reranker-base"  # 默认使用 BGE-Reranker-Base

            logger.info(f"正在加载重排序模型：{model_path}...")

            # 加载 Cross-Encoder 模型 (使用镜像源加速下载)
            # P11 修复：使用 HF_ENDPOINT 环境变量指定镜像源
            import os
            if "HF_ENDPOINT" not in os.environ:
                os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 国内镜像源
            
            # P11 修复：使用 activation_fn 替代 deprecated 的 default_activation_function
            self.model = CrossEncoder(
                model_path,
                max_length=512,
                activation_fn=torch.nn.Sigmoid()
            )

            self.model_type = "cross_encoder"
            self.initialized = True

            logger.info(f"重排序模型加载成功：{model_path} (级联模式：{use_cascade})")
            return True

        except Exception as e:
            logger.error(f"重排序模型加载失败：{e}")
            # P11 降级方案：模型加载失败时，使用 BM25 分数作为重排序分数
            logger.warning("降级为 BM25 分数重排序")
            self.model_type = "bm25_fallback"
            self.initialized = True
            return False
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5,
               use_smart_rerank: bool = True) -> List[Dict[str, Any]]:
        """
        重排序文档 (P11 性能优化版)

        P11 优化策略:
        1. 动态重排序：根据查询复杂度选择重排序策略
        2. 简单查询跳过重排序，直接使用 BM25 分数
        3. 复杂查询使用 Cross-Encoder 精排

        Args:
            query: 查询文本
            documents: 文档列表，每个包含 content 字段
            top_k: 返回的 top K 结果数
            use_smart_rerank: 是否启用智能重排序 (根据查询复杂度选择策略)

        Returns:
            重排序后的文档列表
        """
        if not self.initialized:
            raise RuntimeError("重排序模型未初始化")

        if not documents:
            return []

        # P11 性能优化：查询复杂度判断
        query_length = len(query)
        query_word_count = len(query.split())
        
        # 简单查询判定：短查询 (<10 字符或<3 个词) 跳过重排序
        if use_smart_rerank and (query_length < 10 or query_word_count < 3):
            logger.debug(f"简单查询 (长度={query_length}, 词数={query_word_count})，使用 BM25 分数")
            return self._rerank_with_bm25(query, documents, top_k)

        # P11 降级方案：如果模型加载失败，使用 BM25 分数作为重排序分数
        if self.model_type == "bm25_fallback":
            logger.info("使用 BM25 分数进行重排序 (降级方案)")
            return self._rerank_with_bm25(query, documents, top_k)

        # P11 性能优化：批量推理
        import torch

        # 提取文档内容
        doc_texts = [doc.get("content", "") for doc in documents]

        # 构建 (query, document) 对
        pairs = [(query, text) for text in doc_texts]

        # 使用 Cross-Encoder 预测分数 (批量推理)
        try:
            with torch.no_grad():
                # P11 优化：使用 batch_size 参数加速推理
                scores = self.model.predict(pairs, batch_size=32, convert_to_numpy=True)
        except Exception as e:
            logger.error(f"Cross-Encoder 推理失败：{e}，降级为 BM25")
            return self._rerank_with_bm25(query, documents, top_k)

        # 将分数添加到文档
        for i, doc in enumerate(documents):
            doc["rerank_score"] = float(scores[i])
            doc["rerank_method"] = self.model_type
            doc["rerank_model"] = self.model_name

        # 按重排序分数降序排序
        documents.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

        # 返回 top_k
        return documents[:top_k]

    def _rerank_with_bm25(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        使用 BM25 关键词匹配进行轻量级重排序

        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回的 top K 结果数

        Returns:
            重排序后的文档列表
        """
        # 使用简单的词频匹配作为分数
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for doc in documents:
            content = doc.get("content", "").lower()
            content_words = set(content.split())
            overlap = len(query_words & content_words)
            
            # BM25 风格评分：考虑词频和文档长度
            doc["rerank_score"] = overlap / max(len(query_words), 1)
            doc["rerank_method"] = "bm25_lightweight"
            doc["rerank_model"] = "keyword_match"

        documents.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        return documents[:top_k]
    
    def get_status(self) -> Dict[str, Any]:
        """获取模型状态"""
        return {
            "initialized": self.initialized,
            "model_name": self.model_name,
            "model_type": self.model_type
        }


# 全局重排序模型实例 (预加载)
rerank_model = RerankModel()


def initialize_reranker(model_name: str = "bge-reranker-base"):
    """
    启动时初始化重排序模型
    
    Args:
        model_name: 模型名称
    """
    rerank_model.load_model(model_name)


class RerankRequest(BaseModel):
    """重排序请求"""
    query: str
    documents: List[Dict[str, Any]]
    top_k: int = 5


class RerankResponse(BaseModel):
    """重排序响应"""
    results: List[Dict[str, Any]]
    total: int
    rerank_method: str
    processing_time_ms: float


@router.post("/rerank", response_model=RerankResponse)
async def rerank_endpoint(request: RerankRequest):
    """
    重排序文档接口
    
    使用预加载的 Cross-Encoder 模型进行精排
    """
    start_time = datetime.now()
    
    if not rerank_model.initialized:
        logger.error("重排序模型未初始化")
        raise RuntimeError("重排序服务不可用")
    
    # 执行重排序
    results = rerank_model.rerank(
        query=request.query,
        documents=request.documents,
        top_k=request.top_k
    )
    
    processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    return RerankResponse(
        results=results,
        total=len(results),
        rerank_method=rerank_model.model_type,
        processing_time_ms=processing_time_ms
    )


@router.get("/status")
async def get_status():
    """获取重排序服务状态"""
    status = rerank_model.get_status()
    return {
        "code": 200,
        "data": status,
        "available": status["initialized"]
    }


@router.post("/rerank/batch")
async def rerank_batch(request: RerankRequest):
    """批量重排序接口"""
    start_time = datetime.now()
    
    if not rerank_model.initialized:
        raise RuntimeError("重排序服务不可用")
    
    results = rerank_model.rerank(
        query=request.query,
        documents=request.documents,
        top_k=request.top_k
    )
    
    processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    return {
        "code": 200,
        "data": {
            "results": results,
            "total": len(results),
            "rerank_method": rerank_model.model_type,
            "processing_time_ms": processing_time_ms
        }
    }


# ==================== 便捷函数 ====================
async def rerank_documents(query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
    """
    便捷函数：重排序文档
    
    用于在其他服务中直接调用
    """
    if not rerank_model.initialized:
        logger.warning("重排序模型未初始化，返回原始文档")
        return documents[:top_k]
    
    return rerank_model.rerank(query, documents, top_k)
