"""智能分块引擎 (CHUNK-ENGINE) - 按内容类型使用不同分块策略"""

from fastapi import APIRouter
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import re
import hashlib

router = APIRouter(prefix="/chunk", tags=["Chunk Engine"])


@router.get("/", response_model=dict)
async def get_chunk_stats():
    """获取分块引擎状态"""
    return {"code": 200, "message": "success", "data": {"status": "ok", "service": "chunk engine"}}


@router.get("/stats", response_model=dict)
async def get_chunk_stats_alias():
    """获取分块统计信息"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "strategies": list(CHUNK_STRATEGIES.keys()),
            "default_strategy": "教材",
            "service": "chunk"
        }
    }


# 分块策略配置
CHUNK_STRATEGIES = {
    "教材": {
        "chunk_size": 1000,
        "overlap": 200,
        "separators": ["\n\n", "\n", "。", "；", "，"]
    },
    "代码示例": {
        "chunk_size": 500,
        "overlap": 50,
        "separators": ["\n\n", "\n", "def ", "class ", "function"]
    },
    "公式": {
        "chunk_size": 200,
        "overlap": 20,
        "separators": ["$$", "$", "\\[", "\\]"]
    },
    "对话历史": {
        "chunk_size": 300,
        "overlap": 30,
        "separators": ["\n\n", "\n", "用户：", "助手："]
    }
}


class ChunkRequest(BaseModel):
    """分块请求"""
    content: str
    content_type: str = "教材"  # 教材, 代码示例, 公式, 对话历史
    chunk_size: Optional[int] = None
    overlap: Optional[int] = None
    metadata: Dict[str, Any] = {}


class ChunkResponse(BaseModel):
    """分块响应"""
    chunks: List[Dict[str, Any]]
    total_chunks: int
    content_type: str
    processing_time: float


def get_chunk_strategy(content_type: str) -> Dict:
    """获取指定内容类型的分块策略"""
    return CHUNK_STRATEGIES.get(content_type, CHUNK_STRATEGIES["教材"])


def split_text_by_separators(text: str, separators: List[str]) -> List[str]:
    """使用分隔符列表递归分割文本"""
    if not separators:
        return [text]
    
    first_sep = separators[0]
    remaining_seps = separators[1:]
    
    parts = []
    for part in text.split(first_sep):
        if remaining_seps:
            sub_parts = split_text_by_separators(part, remaining_seps)
            parts.extend(sub_parts)
        else:
            if part.strip():
                parts.append(part)
    
    return [p for p in parts if p.strip()]


def merge_small_chunks(chunks: List[str], min_size: int = 50) -> List[str]:
    """合并过小的块"""
    if not chunks:
        return []
    
    merged = []
    current = chunks[0]
    
    for chunk in chunks[1:]:
        if len(current) < min_size:
            current = current + "\n" + chunk
        else:
            merged.append(current)
            current = chunk
    
    if current:
        merged.append(current)
    
    return merged


def chunk_text_by_strategy(text: str, strategy: Dict) -> List[str]:
    """
    根据策略分块文本
    
    Args:
        text: 待分块文本
        strategy: 包含 chunk_size, overlap, separators 的字典
    
    Returns:
        文本块列表
    """
    chunk_size = strategy.get("chunk_size", 1000)
    overlap = strategy.get("overlap", 200)
    separators = strategy.get("separators", ["\n\n", "\n"])
    
    # 首先使用分隔符分割
    segments = split_text_by_separators(text, separators)
    
    # 合并 segments 成块
    chunks = []
    current_chunk = ""
    
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
            
        # 如果单个 segment 超出了 chunk_size，进一步分割
        if len(segment) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            # 递归处理长段落，但设置最大递归深度限制
            new_chunk_size = chunk_size // 2
            new_overlap = overlap // 2
            new_separators = separators[1:] if len(separators) > 1 else separators

            # 如果 chunk_size 已经太小，直接强制分割
            if new_chunk_size < 50:
                # 强制按固定长度分割
                fixed_chunks = []
                for i in range(0, len(segment), chunk_size):
                    fixed_chunks.append(segment[i:i + chunk_size])
                chunks.extend(fixed_chunks)
            else:
                # 递归处理长段落
                sub_chunks = chunk_text_by_strategy(
                    segment,
                    {"chunk_size": new_chunk_size, "overlap": new_overlap, "separators": new_separators}
                )
                chunks.extend(sub_chunks)
            if new_chunk_size < 50:
                # 强制按固定长度分割
                fixed_chunks = []
                for i in range(0, len(segment), chunk_size):
                    fixed_chunks.append(segment[i:i + chunk_size])
                chunks.extend(fixed_chunks)
            else:
                # 递归处理长段落
                sub_chunks = chunk_text_by_strategy(
                    segment,
                    {"chunk_size": new_chunk_size, "overlap": new_overlap, "separators": new_separators}
                )
                chunks.extend(sub_chunks)
            continue
        
        # 检查是否需要开始新块
        if len(current_chunk) + len(segment) + 1 > chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                # 保留 overlap 部分
                if overlap > 0 and len(current_chunk) > overlap:
                    current_chunk = current_chunk[-(overlap):]
                else:
                    current_chunk = ""
        
        if current_chunk:
            current_chunk += "\n" + segment
        else:
            current_chunk = segment
    
    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk)
    
    # 合并过小的块
    chunks = merge_small_chunks(chunks)
    
    return chunks


def create_chunk_metadata(chunk_text: str, index: int, content_type: str, original_metadata: Dict) -> Dict:
    """为每个chunk创建元数据"""
    chunk_id = hashlib.md5(f"{original_metadata.get('source', 'unknown')}_{index}".encode()).hexdigest()[:16]
    
    # 提取关键词作为chunk的特征
    keywords = extract_chunk_keywords(chunk_text)
    
    # 估算token数量 (中文约1.5字符/token, 英文约4字符/token)
    chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', chunk_text))
    english_words = len(re.findall(r'[a-zA-Z]+', chunk_text))
    estimated_tokens = int(chinese_chars / 1.5 + english_words / 4)
    
    return {
        "chunk_id": chunk_id,
        "index": index,
        "content_type": content_type,
        "content": chunk_text,
        "char_count": len(chunk_text),
        "estimated_tokens": estimated_tokens,
        "keywords": keywords,
        "metadata": original_metadata,
        "created_at": datetime.utcnow().isoformat()
    }


def extract_chunk_keywords(text: str) -> List[str]:
    """从chunk中提取关键词"""
    # 移除常见停用词
    stopwords = {
        "的", "是", "在", "和", "了", "有", "我", "你", "他", "她", "它", "们",
        "这", "那", "个", "与", "或", "及", "等", "为", "以", "于", "也", "就",
        "都", "而", "及", "与", "着", "或", "一个", "没有", "我们", "你们"
    }
    
    # 提取中文词
    chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
    chinese_keywords = [w for w in chinese_words if w not in stopwords]
    
    # 提取英文词
    english_words = re.findall(r'[a-zA-Z]{3,}', text)
    
    # 合并并去重，保留出现频率最高的10个
    all_words = chinese_keywords + english_words
    word_freq = {}
    for word in all_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [w[0] for w in sorted_words[:10]]


@router.post("/text", response_model=ChunkResponse)
async def chunk_text(request: ChunkRequest):
    """
    对文本进行智能分块
    
    根据 content_type 使用不同的分块策略:
    - 教材: chunk_size=1000, overlap=200
    - 代码示例: chunk_size=500, overlap=50
    - 公式: chunk_size=200, overlap=20
    - 对话历史: chunk_size=300, overlap=30
    """
    start_time = datetime.now()
    
    # 获取分块策略
    strategy = get_chunk_strategy(request.content_type)
    
    # 允许自定义覆盖
    if request.chunk_size:
        strategy["chunk_size"] = request.chunk_size
    if request.overlap:
        strategy["overlap"] = request.overlap
    
    # 执行分块
    chunk_texts = chunk_text_by_strategy(request.content, strategy)
    
    # 创建元数据
    chunks = []
    for i, chunk_text in enumerate(chunk_texts):
        chunk_meta = create_chunk_metadata(
            chunk_text, 
            i, 
            request.content_type,
            request.metadata
        )
        chunks.append(chunk_meta)
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    return ChunkResponse(
        chunks=chunks,
        total_chunks=len(chunks),
        content_type=request.content_type,
        processing_time=processing_time
    )


@router.post("/batch")
async def chunk_batch_documents(documents: List[ChunkRequest]):
    """批量分块处理多个文档"""
    all_chunks = []
    
    for doc in documents:
        strategy = get_chunk_strategy(doc.content_type)
        if doc.chunk_size:
            strategy["chunk_size"] = doc.chunk_size
        if doc.overlap:
            strategy["overlap"] = doc.overlap
            
        chunk_texts = chunk_text_by_strategy(doc.content, strategy)
        
        for i, chunk_text in enumerate(chunk_texts):
            chunk_meta = create_chunk_metadata(
                chunk_text,
                i,
                doc.content_type,
                doc.metadata
            )
            all_chunks.append(chunk_meta)
    
    return {
        "code": 200,
        "message": f"成功处理 {len(documents)} 个文档",
        "data": {
            "total_chunks": len(all_chunks),
            "chunks": all_chunks
        }
    }


@router.get("/strategies")
async def get_chunk_strategies():
    """获取所有可用的分块策略"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "strategies": CHUNK_STRATEGIES,
            "default": "教材"
        }
    }


@router.post("/estimate")
async def estimate_chunk_count(request: ChunkRequest):
    """估算分块数量（不实际分块）"""
    strategy = get_chunk_strategy(request.content_type)
    chunk_size = request.chunk_size or strategy["chunk_size"]
    
    # 粗略估算
    estimated_chunks = max(1, len(request.content) // (chunk_size - strategy["overlap"]))
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "estimated_chunks": estimated_chunks,
            "strategy_used": strategy,
            "content_length": len(request.content)
        }
    }
