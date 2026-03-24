"""
语义分块服务 (SEMANTIC CHUNKING)

P11 优化:
1. 基于段落/标题的语义分块
2. 保持章节完整性
3. 语义相似度检测边界
4. 支持 Parent-Child Indexing 基础结构
"""

import logging
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chunk", tags=["Semantic Chunking"])


# ==================== 数据模型 ====================

class SemanticChunkRequest(BaseModel):
    """语义分块请求"""
    content: str
    content_type: str = "textbook"  # textbook, code, paper, mixed
    course_id: Optional[str] = None
    max_chunk_size: int = 1500
    min_chunk_size: int = 200
    overlap_ratio: float = 0.15  # 15% 重叠
    use_semantic_boundary: bool = True


class SemanticChunkResponse(BaseModel):
    """语义分块响应"""
    chunks: List[Dict[str, Any]]
    total_chunks: int
    content_type: str
    strategy: str
    processing_time_ms: float


class ChunkInfo(BaseModel):
    """Chunk 信息"""
    chunk_id: str
    content: str
    start_index: int
    end_index: int
    level: int  # 层级 (基于标题)
    parent_chunk_id: Optional[str] = None
    child_chunk_ids: List[str] = []
    metadata: Dict[str, Any] = {}


# ==================== 标题/段落检测 ====================

# 中文标题模式
CHINESE_HEADING_PATTERNS = [
    r'^(第 [一二三四五六七八九十\d]+章)',  # 第一章，第 1 章
    r'^(第 [一二三四五六七八九十\d]+节)',  # 第一节
    r'^(第 [一二三四五六七八九十\d]+条)',  # 第一条
    r'^(\d+\.\d+\.?\d*)\s+',  # 1.1, 1.1.1
    r'^(\d+、)',  # 1、
    r'^(一、|二、|三、|四、|五、)',  # 一、
    r'^\s*#\s+(.+)',  # Markdown H1
    r'^\s*##\s+(.+)',  # Markdown H2
    r'^\s*###\s+(.+)',  # Markdown H3
]

# 英文标题模式
ENGLISH_HEADING_PATTERNS = [
    r'^(Chapter\s+\d+)',  # Chapter 1
    r'^(Section\s+\d+)',  # Section 1
    r'^(\d+\.\d+\.?\d*)\s+',  # 1.1, 1.1.1
    r'^(Part\s+[IVX]+)',  # Part I
    r'^\s*#\s+(.+)',  # Markdown H1
    r'^\s*##\s+(.+)',  # Markdown H2
    r'^\s*###\s+(.+)',  # Markdown H3
]

# 段落分隔符
PARAGRAPH_SEPARATORS = [
    '\n\n\n',  # 3 个以上换行
    '\n\n',     # 2 个换行
    '\n',       # 单个换行
]


def detect_headings(text: str) -> List[Dict[str, Any]]:
    """
    检测文本中的标题
    
    Returns:
        标题列表，每个包含：text, start, end, level
    """
    headings = []
    lines = text.split('\n')
    current_pos = 0
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # 检测各级标题
        level = None
        title_text = None
        
        # Markdown H1
        if line_stripped.startswith('# '):
            level = 1
            title_text = line_stripped[2:].strip()
        # Markdown H2
        elif line_stripped.startswith('## '):
            level = 2
            title_text = line_stripped[3:].strip()
        # Markdown H3
        elif line_stripped.startswith('### '):
            level = 3
            title_text = line_stripped[4:].strip()
        # 数字标题 1.1, 1.1.1
        elif re.match(r'^\d+\.\d+\.?\d*\s+', line_stripped):
            match = re.match(r'^(\d+)\.(\d+)', line_stripped)
            if match:
                level = 2 if match.group(2) == '0' or not match.group(2) else 3
                title_text = line_stripped
        # 中文数字标题
        elif re.match(r'^第 [一二三四五六七八九十\d]+[章节条]', line_stripped):
            level = 1
            title_text = line_stripped
        
        if level and title_text:
            headings.append({
                "text": title_text,
                "start": current_pos,
                "end": current_pos + len(line),
                "level": level,
                "line_number": i
            })
        
        current_pos += len(line) + 1  # +1 for newline
    
    return headings


def detect_paragraphs(text: str) -> List[Dict[str, Any]]:
    """
    检测文本中的段落
    
    Returns:
        段落列表，每个包含：content, start, end
    """
    paragraphs = []
    
    # 按双换行分割
    raw_paragraphs = re.split(r'\n\n+', text)
    
    current_pos = 0
    for para in raw_paragraphs:
        para = para.strip()
        if para:
            start = text.find(para, current_pos)
            if start >= 0:
                paragraphs.append({
                    "content": para,
                    "start": start,
                    "end": start + len(para)
                })
                current_pos = start + len(para)
    
    return paragraphs


# ==================== 语义相似度计算 ====================

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    计算两段文本的语义相似度
    
    使用简化的词重叠方法 (实际应该用向量相似度)
    """
    # 分词
    def tokenize(text: str) -> set:
        # 中文：按字符 bigram
        # 英文：按单词
        chinese_chars = re.findall(r'[\u4e00-\u9fa5]', text)
        english_words = re.findall(r'[a-zA-Z]+', text.lower())
        
        # 创建 bigram
        bigrams = set()
        for i in range(len(chinese_chars) - 1):
            bigrams.add(chinese_chars[i] + chinese_chars[i + 1])
        
        bigrams.update(english_words)
        return bigrams
    
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    
    if not tokens1 or not tokens2:
        return 0.0
    
    # Jaccard 相似度
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    
    return len(intersection) / len(union) if union else 0.0


def find_semantic_boundaries(
    paragraphs: List[Dict[str, Any]], 
    threshold: float = 0.3
) -> List[int]:
    """
    基于语义相似度找到段落边界
    
    当相邻段落的语义相似度突然下降时，认为是语义边界
    """
    boundaries = []
    
    for i in range(len(paragraphs) - 1):
        sim = calculate_semantic_similarity(
            paragraphs[i]["content"],
            paragraphs[i + 1]["content"]
        )
        
        # 相似度低于阈值，认为是边界
        if sim < threshold:
            boundaries.append(i)
    
    return boundaries


# ==================== 语义分块核心逻辑 ====================

def semantic_chunking(
    text: str,
    max_chunk_size: int = 1500,
    min_chunk_size: int = 200,
    overlap_ratio: float = 0.15,
    use_semantic_boundary: bool = True
) -> List[Dict[str, Any]]:
    """
    基于语义的分块算法
    
    策略:
    1. 优先按标题分块 (保持章节完整性)
    2. 在标题内按语义边界分块
    3. 确保块大小在合理范围内
    """
    chunks = []
    
    # 1. 检测标题
    headings = detect_headings(text)
    
    # 2. 检测段落
    paragraphs = detect_paragraphs(text)
    
    if not paragraphs:
        return []
    
    # 3. 按标题分割
    if headings:
        # 按标题将文本分为多个部分
        sections = []
        for i, heading in enumerate(headings):
            section_start = heading["start"]
            section_end = headings[i + 1]["start"] if i + 1 < len(headings) else len(text)
            section_text = text[section_start:section_end]
            
            sections.append({
                "title": heading["text"],
                "level": heading["level"],
                "content": section_text,
                "start": section_start,
                "end": section_end
            })
    else:
        # 没有标题，整个文本作为一个部分
        sections = [{
            "title": "Main Content",
            "level": 0,
            "content": text,
            "start": 0,
            "end": len(text)
        }]
    
    # 4. 处理每个部分
    chunk_index = 0
    parent_chunk_id = None
    
    for section in sections:
        section_content = section["content"]
        section_paragraphs = detect_paragraphs(section_content)
        
        if not section_paragraphs:
            continue
        
        # 5. 在部分内按语义边界分块
        if use_semantic_boundary and len(section_paragraphs) > 2:
            boundaries = find_semantic_boundaries(section_paragraphs)
        else:
            boundaries = []
        
        # 6. 根据边界和大小限制分块
        current_chunk_content = ""
        current_chunk_start = section["start"]
        
        for i, para in enumerate(section_paragraphs):
            para_content = para["content"]
            
            # 检查是否应该开始新块
            should_split = False
            
            # 条件 1: 达到语义边界
            if i - 1 in boundaries:
                should_split = True
            
            # 条件 2: 当前块已超出最大大小
            if len(current_chunk_content) + len(para_content) > max_chunk_size:
                should_split = True
            
            if should_split and current_chunk_content:
                # 创建新块
                chunk = create_chunk(
                    content=current_chunk_content,
                    index=chunk_index,
                    start=current_chunk_start,
                    level=section["level"],
                    parent_chunk_id=parent_chunk_id,
                    metadata={"section_title": section["title"]}
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # 更新 parent (用于 Parent-Child Indexing)
                if parent_chunk_id is None:
                    parent_chunk_id = chunk["chunk_id"]
                
                # 开始新块，保留 overlap
                overlap_length = int(len(current_chunk_content) * overlap_ratio)
                current_chunk_content = current_chunk_content[-overlap_length:] if overlap_length > 0 else ""
                current_chunk_start = para["start"]
            
            # 添加段落到当前块
            if current_chunk_content:
                current_chunk_content += "\n\n" + para_content
            else:
                current_chunk_content = para_content
        
        # 添加最后一个块
        if current_chunk_content:
            chunk = create_chunk(
                content=current_chunk_content,
                index=chunk_index,
                start=current_chunk_start,
                level=section["level"],
                parent_chunk_id=parent_chunk_id,
                metadata={"section_title": section["title"]}
            )
            chunks.append(chunk)
            chunk_index += 1
    
    # 7. 合并过小的块
    chunks = merge_small_chunks(chunks, min_chunk_size)
    
    # 8. 重新分配 chunk_id 和 parent-child 关系
    chunks = rebuild_hierarchy(chunks)
    
    return chunks


def create_chunk(
    content: str,
    index: int,
    start: int,
    level: int,
    parent_chunk_id: Optional[str] = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """创建 chunk 数据结构"""
    chunk_id = hashlib.md5(f"chunk_{index}_{start}".encode()).hexdigest()[:16]
    
    return {
        "chunk_id": chunk_id,
        "content": content,
        "start_index": start,
        "end_index": start + len(content),
        "level": level,
        "parent_chunk_id": parent_chunk_id,
        "child_chunk_ids": [],
        "metadata": metadata or {},
        "char_count": len(content),
        "estimated_tokens": estimate_tokens(content)
    }


def estimate_tokens(text: str) -> int:
    """估算 token 数量"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    return int(chinese_chars / 1.5 + english_words / 4)


def merge_small_chunks(chunks: List[Dict[str, Any]], min_size: int) -> List[Dict[str, Any]]:
    """合并过小的块"""
    if not chunks:
        return []
    
    merged = []
    current = chunks[0].copy()
    
    for chunk in chunks[1:]:
        if current["char_count"] < min_size:
            # 合并到当前块
            current["content"] += "\n\n" + chunk["content"]
            current["end_index"] = chunk["end_index"]
            current["char_count"] = len(current["content"])
            current["estimated_tokens"] = estimate_tokens(current["content"])
        else:
            merged.append(current)
            current = chunk.copy()
    
    if current:
        merged.append(current)
    
    return merged


def rebuild_hierarchy(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """重建父子层级关系"""
    if not chunks:
        return []
    
    # 重新分配 chunk_id
    for i, chunk in enumerate(chunks):
        chunk["chunk_id"] = hashlib.md5(f"chunk_{i}_{chunk['start_index']}".encode()).hexdigest()[:16]
    
    # 建立父子关系
    parent_chunk_id = None
    for i, chunk in enumerate(chunks):
        if chunk["level"] <= 1:
            # 顶级 chunk 作为 parent
            parent_chunk_id = chunk["chunk_id"]
            chunk["parent_chunk_id"] = None
        else:
            # 子 chunk
            chunk["parent_chunk_id"] = parent_chunk_id
        
        # 清除 child_chunk_ids (重新构建)
        chunk["child_chunk_ids"] = []
    
    # 收集 child_chunk_ids
    for chunk in chunks:
        if chunk["parent_chunk_id"]:
            # 找到 parent 并添加 child_id
            for parent in chunks:
                if parent["chunk_id"] == chunk["parent_chunk_id"]:
                    parent["child_chunk_ids"].append(chunk["chunk_id"])
                    break
    
    return chunks


# ==================== API 端点 ====================

@router.post("/semantic", response_model=SemanticChunkResponse)
async def semantic_chunk_endpoint(request: SemanticChunkRequest):
    """
    语义分块接口
    
    基于段落/标题的语义分块，保持章节完整性
    """
    start_time = datetime.now()
    
    chunks = semantic_chunking(
        text=request.content,
        max_chunk_size=request.max_chunk_size,
        min_chunk_size=request.min_chunk_size,
        overlap_ratio=request.overlap_ratio,
        use_semantic_boundary=request.use_semantic_boundary
    )
    
    processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    return SemanticChunkResponse(
        chunks=chunks,
        total_chunks=len(chunks),
        content_type=request.content_type,
        strategy="semantic_boundary",
        processing_time_ms=processing_time_ms
    )


@router.post("/estimate")
async def estimate_chunks(request: SemanticChunkRequest):
    """估算分块数量"""
    chunks = semantic_chunking(
        text=request.content,
        max_chunk_size=request.max_chunk_size,
        min_chunk_size=request.min_chunk_size,
        overlap_ratio=request.overlap_ratio,
        use_semantic_boundary=request.use_semantic_boundary
    )
    
    return {
        "code": 200,
        "data": {
            "estimated_chunks": len(chunks),
            "total_chars": len(request.content),
            "avg_chunk_size": len(request.content) / len(chunks) if chunks else 0
        }
    }


# ==================== 便捷函数 ====================

def chunk_document(content: str, **kwargs) -> List[Dict[str, Any]]:
    """
    便捷函数：分块文档
    
    用于在其他服务中直接调用
    """
    return semantic_chunking(content, **kwargs)
