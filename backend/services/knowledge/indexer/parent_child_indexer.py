"""
Parent-Child Indexing 服务

P11 优化:
1. 小 chunk 用于检索 (提高精度)
2. 大 chunk 用于上下文 (提供完整性)
3. 自动建立父子关系
4. 支持动态合并相关 chunk
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/index", tags=["Parent-Child Indexing"])


# ==================== 数据模型 ====================

class ParentChildConfig(BaseModel):
    """Parent-Child 配置"""
    parent_chunk_size: int = 2000  # 父 chunk 大小 (用于上下文)
    child_chunk_size: int = 500    # 子 chunk 大小 (用于检索)
    overlap_ratio: float = 0.15    # 重叠比例
    children_per_parent: int = 4   # 每个 parent 包含的 children 数量


class DocumentForIndexing(BaseModel):
    """待索引文档"""
    doc_id: str
    content: str
    course_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ParentChildResponse(BaseModel):
    """Parent-Child 索引响应"""
    doc_id: str
    parent_chunks: List[Dict[str, Any]]
    total_parents: int
    total_children: int
    config: ParentChildConfig
    processing_time_ms: float


# ==================== Parent-Child 分块逻辑 ====================

def create_parent_child_chunks(
    content: str,
    doc_id: str,
    config: ParentChildConfig,
    course_id: Optional[str] = None,
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    创建 Parent-Child 分块结构
    
    策略:
    1. 先创建大的 parent chunks (用于提供上下文)
    2. 将每个 parent chunk 细分为小的 child chunks (用于检索)
    3. 建立父子关系索引
    """
    parent_chunks = []
    child_chunks = []
    
    # 1. 创建 parent chunks
    parent_texts = split_by_size(
        content, 
        config.parent_chunk_size, 
        config.overlap_ratio
    )
    
    for i, parent_text in enumerate(parent_texts):
        parent_id = f"{doc_id}_parent_{i}"
        
        parent_chunk = {
            "chunk_id": parent_id,
            "doc_id": doc_id,
            "content": parent_text,
            "chunk_type": "parent",
            "level": 0,
            "start_index": i * int(config.parent_chunk_size * (1 - config.overlap_ratio)),
            "end_index": (i + 1) * int(config.parent_chunk_size * (1 - config.overlap_ratio)),
            "child_chunk_ids": [],  # 将被填充
            "metadata": {
                "course_id": course_id,
                "chunk_index": i,
                "char_count": len(parent_text)
            }
        }
        parent_chunks.append(parent_chunk)
    
    # 2. 为每个 parent 创建 child chunks
    for i, parent in enumerate(parent_chunks):
        parent_text = parent["content"]
        
        # 将 parent chunk 细分为 child chunks
        child_texts = split_by_size(
            parent_text,
            config.child_chunk_size,
            config.overlap_ratio
        )
        
        for j, child_text in enumerate(child_texts):
            child_id = f"{doc_id}_child_{i}_{j}"
            
            child_chunk = {
                "chunk_id": child_id,
                "doc_id": doc_id,
                "content": child_text,
                "chunk_type": "child",
                "level": 1,
                "parent_chunk_id": parent["chunk_id"],
                "start_index": parent["start_index"] + j * int(config.child_chunk_size * (1 - config.overlap_ratio)),
                "end_index": parent["start_index"] + (j + 1) * int(config.child_chunk_size * (1 - config.overlap_ratio)),
                "metadata": {
                    "course_id": course_id,
                    "parent_index": i,
                    "child_index": j,
                    "char_count": len(child_text)
                }
            }
            child_chunks.append(child_chunk)
            
            # 更新 parent 的 child_chunk_ids
            parent_chunks[i]["child_chunk_ids"].append(child_id)
    
    # 3. 合并所有 chunks (parent 和 child 都用于索引，但用途不同)
    all_chunks = parent_chunks + child_chunks
    
    logger.info(f"创建 Parent-Child 索引：{len(parent_chunks)} 个 parents, {len(child_chunks)} 个 children")
    
    return all_chunks


def split_by_size(text: str, chunk_size: int, overlap_ratio: float) -> List[str]:
    """
    按大小分割文本，保留重叠
    
    智能分割策略:
    1. 优先在段落边界分割
    2. 其次在句子边界分割
    3. 最后强制分割
    """
    chunks = []
    overlap_size = int(chunk_size * overlap_ratio)
    step_size = chunk_size - overlap_size
    
    if step_size <= 0:
        step_size = chunk_size // 2
        overlap_size = chunk_size // 2
    
    # 按段落分割
    paragraphs = text.split('\n\n')
    
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # 如果当前块 + 新段落超出大小
        if len(current_chunk) + len(para) > chunk_size:
            # 如果当前块已有内容，先保存
            if current_chunk:
                chunks.append(current_chunk)
            
            # 如果段落本身超出 chunk_size，需要进一步分割
            if len(para) > chunk_size:
                # 按句子分割
                sentences = split_by_sentences(para)
                
                temp_chunk = ""
                for sentence in sentences:
                    if len(temp_chunk) + len(sentence) > chunk_size:
                        if temp_chunk:
                            chunks.append(temp_chunk)
                        temp_chunk = sentence
                    else:
                        if temp_chunk:
                            temp_chunk += " " + sentence
                        else:
                            temp_chunk = sentence
                
                if temp_chunk:
                    current_chunk = temp_chunk
            else:
                current_chunk = para
        else:
            # 添加到当前块
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
    
    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk)
    
    # 确保每个 chunk 有适当的重叠
    if len(chunks) > 1 and overlap_size > 0:
        chunks_with_overlap = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                chunks_with_overlap.append(chunk)
            else:
                # 添加前一个 chunk 的末尾作为重叠
                prev_tail = chunks[i - 1][-overlap_size:] if len(chunks[i - 1]) > overlap_size else ""
                if prev_tail:
                    chunks_with_overlap.append(prev_tail + "\n\n" + chunk)
                else:
                    chunks_with_overlap.append(chunk)
        chunks = chunks_with_overlap
    
    return chunks


def split_by_sentences(text: str) -> List[str]:
    """按句子分割文本"""
    import re
    
    # 中英文句子分隔符
    sentence_endings = r'(?<=[。！？.!?])\s+'
    
    sentences = re.split(sentence_endings, text)
    
    # 过滤空句子
    return [s.strip() for s in sentences if s.strip()]


# ==================== 检索时获取完整上下文 ====================

def get_parent_context(child_chunk: Dict[str, Any], all_chunks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    根据 child chunk 获取 parent 上下文
    
    用于检索到 child 后，返回更大的上下文
    """
    parent_id = child_chunk.get("parent_chunk_id")
    
    if not parent_id:
        return None
    
    for chunk in all_chunks:
        if chunk["chunk_id"] == parent_id:
            return chunk
    
    return None


def expand_retrieved_chunks(
    retrieved_child_ids: List[str],
    all_chunks: List[Dict[str, Any]],
    expand_to_parent: bool = True,
    include_siblings: bool = False
) -> List[Dict[str, Any]]:
    """
    扩展检索结果，获取更完整的上下文
    
    Args:
        retrieved_child_ids: 检索到的 child chunk IDs
        all_chunks: 所有 chunks
        expand_to_parent: 是否扩展到 parent
        include_siblings: 是否包含兄弟节点
    
    Returns:
        扩展后的 chunks
    """
    expanded = []
    seen_ids = set()
    
    for child_id in retrieved_child_ids:
        # 找到 child chunk
        child_chunk = None
        for chunk in all_chunks:
            if chunk["chunk_id"] == child_id:
                child_chunk = chunk
                break
        
        if not child_chunk:
            continue
        
        if expand_to_parent:
            # 获取 parent
            parent = get_parent_context(child_chunk, all_chunks)
            if parent and parent["chunk_id"] not in seen_ids:
                expanded.append(parent)
                seen_ids.add(parent["chunk_id"])
        else:
            # 只返回 child
            if child_id not in seen_ids:
                expanded.append(child_chunk)
                seen_ids.add(child_id)
        
        if include_siblings and child_chunk.get("parent_chunk_id"):
            # 获取兄弟节点
            for chunk in all_chunks:
                if (chunk.get("parent_chunk_id") == child_chunk["parent_chunk_id"] and
                    chunk["chunk_id"] != child_id and
                    chunk["chunk_id"] not in seen_ids):
                    expanded.append(chunk)
                    seen_ids.add(chunk["chunk_id"])
    
    return expanded


# ==================== API 端点 ====================

@router.post("/parent-child", response_model=ParentChildResponse)
async def create_parent_child_index(request: DocumentForIndexing):
    """
    为文档创建 Parent-Child 索引结构
    
    小 chunk 用于检索，大 chunk 用于提供上下文
    """
    start_time = datetime.now()
    
    config = ParentChildConfig()
    
    all_chunks = create_parent_child_chunks(
        content=request.content,
        doc_id=request.doc_id,
        config=config,
        course_id=request.course_id,
        metadata=request.metadata
    )
    
    # 分离 parent 和 child
    parent_chunks = [c for c in all_chunks if c["chunk_type"] == "parent"]
    child_chunks = [c for c in all_chunks if c["chunk_type"] == "child"]
    
    processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    return ParentChildResponse(
        doc_id=request.doc_id,
        parent_chunks=parent_chunks,
        total_parents=len(parent_chunks),
        total_children=len(child_chunks),
        config=config,
        processing_time_ms=processing_time_ms
    )


@router.post("/expand")
async def expand_context(request: BaseModel):
    """
    扩展检索结果的上下文
    
    输入检索到的 chunk IDs，返回扩展后的完整上下文
    """
    # 简化实现，实际需要查询数据库获取所有 chunks
    return {
        "code": 200,
        "message": "扩展上下文功能需要结合具体检索结果使用",
        "data": {
            "expand_to_parent": True,
            "include_siblings": False
        }
    }


# ==================== 便捷函数 ====================

def index_document_with_parent_child(
    doc_id: str,
    content: str,
    course_id: Optional[str] = None,
    metadata: Dict[str, Any] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    便捷函数：为文档创建 Parent-Child 索引
    
    用于在其他服务中直接调用
    """
    config = ParentChildConfig(**kwargs) if kwargs else ParentChildConfig()
    
    return create_parent_child_chunks(
        content=content,
        doc_id=doc_id,
        config=config,
        course_id=course_id,
        metadata=metadata
    )
