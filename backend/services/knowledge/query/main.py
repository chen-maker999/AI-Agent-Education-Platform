"""查询处理服务 - 查询改写、扩展、优化"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/query", tags=["Query Processing"])


def _jieba():
    import jieba
    import jieba.analyse
    return jieba, jieba.analyse


class QueryRewriteRequest(BaseModel):
    """查询改写请求"""
    query: str
    course_id: str = ""


class QueryRewriteResponse(BaseModel):
    """查询改写响应"""
    original_query: str
    expanded_queries: List[str]
    keywords: List[str]


def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    """提取关键词"""
    _, jieba_analyse = _jieba()
    keywords = jieba_analyse.extract_tags(text, topK=top_k, withWeight=False)
    return keywords


def expand_query(query: str) -> List[str]:
    """扩展查询 - 添加同义词和相关词"""
    # 定义常见编程概念的中文扩展
    expansions = {
        "python": ["Python", "Python编程", "Python语言"],
        "java": ["Java", "Java编程", "Java语言"],
        "算法": ["算法", "数据结构与算法", "算法设计"],
        "变量": ["变量", "数据类型", "变量声明"],
        "函数": ["函数", "方法", "函数定义"],
        "类": ["类", "面向对象", "类定义"],
        "循环": ["循环", "for循环", "while循环"],
        "列表": ["列表", "List", "数组"],
        "字典": ["字典", "Dict", "映射"],
        "文件": ["文件", "文件操作", "IO"],
        "网络": ["网络", "HTTP", "请求"],
        "数据库": ["数据库", "SQL", "DB"],
        "异常": ["异常", "Exception", "错误处理"],
        "测试": ["测试", "UnitTest", "单元测试"],
    }
    
    expanded = [query]
    query_lower = query.lower()
    
    for key, values in expansions.items():
        if key in query_lower:
            expanded.extend(values)
    
    # 去重
    return list(dict.fromkeys(expanded))


def rewrite_query(query: str, course_id: str = "") -> List[str]:
    """
    查询改写
    
    1. 提取关键词
    2. 扩展查询
    3. 返回多个查询变体
    """
    # 原始查询
    queries = [query]
    
    # 提取关键词并构建新查询
    keywords = extract_keywords(query)
    if keywords:
        # 添加关键词组合查询
        keywords_query = " ".join(keywords[:5])
        if keywords_query != query:
            queries.append(keywords_query)
        
        # 添加每个关键词的查询
        for kw in keywords[:3]:
            if kw not in query:
                queries.append(f"{query} {kw}")
    
    # 扩展查询
    expanded = expand_query(query)
    queries.extend(expanded)
    
    # 去重
    return list(dict.fromkeys(queries))


@router.post("/rewrite", response_model=QueryRewriteResponse)
async def rewrite_query_endpoint(request: QueryRewriteRequest):
    """查询改写接口"""
    keywords = extract_keywords(request.query)
    expanded_queries = rewrite_query(request.query, request.course_id)
    
    return QueryRewriteResponse(
        original_query=request.query,
        expanded_queries=expanded_queries,
        keywords=keywords
    )


@router.post("/keywords")
async def extract_keywords_endpoint(query: str, top_k: int = 10):
    """关键词提取接口"""
    keywords = extract_keywords(query, top_k)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "query": query,
            "keywords": keywords
        }
    }


@router.post("/expand")
async def expand_query_endpoint(query: str):
    """查询扩展接口"""
    expanded = expand_query(query)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "original_query": query,
            "expanded_queries": expanded
        }
    }
