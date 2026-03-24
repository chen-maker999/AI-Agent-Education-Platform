"""查询路由与意图识别服务 - 自动路由到最佳检索渠道"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import re


router = APIRouter(prefix="/router", tags=["Query Router"])


# 意图类型定义
class IntentType:
    CONCEPT_EXPLANATION = "concept_explanation"  # 概念解释
    RELATION_QUERY = "relation_query"  # 关系查询
    CODE_QUESTION = "code_question"  # 代码问题
    HISTORY_REVIEW = "history_review"  # 历史回顾
    EXERCISE_FIND = "exercise_find"  # 题目查找
    GENERAL = "general"  # 通用查询


# 意图到检索渠道的映射
INTENT_TO_CHANNELS = {
    IntentType.CONCEPT_EXPLANATION: ["semantic", "keyword", "graph"],  # 添加 keyword 以支持跨语言检索
    IntentType.RELATION_QUERY: ["graph", "keyword"],  # 添加 keyword 作为 fallback
    IntentType.CODE_QUESTION: ["semantic", "keyword"],
    IntentType.HISTORY_REVIEW: ["keyword"],
    IntentType.EXERCISE_FIND: ["keyword", "semantic"],
    IntentType.GENERAL: ["semantic", "keyword"],
}


# 关键词规则
INTENT_KEYWORDS = {
    IntentType.CONCEPT_EXPLANATION: [
        "什么是", "解释", "定义", "含义", "意思", "概念", "介绍", "说明",
        "what", "define", "definition", "explain", "meaning"
    ],
    IntentType.RELATION_QUERY: [
        "关系", "联系", "区别", "差异", "对比", "关联", "影响", "作用",
        "relationship", "relation", "difference", "vs", "versus", "compare"
    ],
    IntentType.CODE_QUESTION: [
        "代码", "编程", "实现", "怎么写", "如何实现", "函数", "方法", "类",
        "code", "programming", "implement", "function", "class", "method"
    ],
    IntentType.HISTORY_REVIEW: [
        "历史", "记录", "之前", "曾经", "上次", "回顾", "学过", "看过",
        "history", "record", "previous", "review"
    ],
    IntentType.EXERCISE_FIND: [
        "题目", "练习", "习题", "试题", "考题", "刷题", "做题",
        "exercise", "practice", "question", "problem", "exam"
    ],
}


class QueryRouterRequest(BaseModel):
    """查询路由请求"""
    query: str
    course_id: Optional[str] = None
    student_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}


class QueryRouterResponse(BaseModel):
    """查询路由响应"""
    query: str
    intent: str
    confidence: float
    channels: List[str]
    keywords: List[str]
    rewritten_queries: List[str]


class IntentClassifier:
    """意图分类器"""
    
    def __init__(self):
        # 问题类型特征
        self.question_patterns = {
            "what": r"(什么 | 啥|what)",
            "how": r"(怎么 | 如何|how)",
            "why": r"(为什么 | 为啥|why)",
            "which": r"(哪个 | 哪些|which)",
            "when": r"(什么时候 | 何时|when)",
            "where": r"(哪里 | 何处|where)",
        }
        
        # 编程相关关键词
        self.code_keywords = {
            "python", "java", "c++", "javascript", "go", "rust",
            "函数", "方法", "类", "对象", "变量", "循环", "条件",
            "function", "class", "object", "variable", "loop"
        }
        
        # 概念相关关键词
        self.concept_keywords = {
            "概念", "定义", "含义", "意思", "解释", "说明",
            "concept", "definition", "meaning", "explain"
        }
    
    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        try:
            import jieba.analyse
            keywords = jieba.analyse.extract_tags(text, topK=10, withWeight=False)
            return keywords
        except ImportError:
            # 简单提取
            words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', text)
            return words[:10]
    
    def classify(self, query: str) -> tuple[str, float]:
        """
        分类查询意图
        
        Returns:
            (intent_type, confidence)
        """
        query_lower = query.lower()
        keywords = self.extract_keywords(query)
        keyword_set = set(keywords)
        
        # 计分板
        scores = {intent: 0.0 for intent in INTENT_KEYWORDS.keys()}
        
        # 1. 关键词匹配
        for intent, intent_keywords in INTENT_KEYWORDS.items():
            for kw in intent_keywords:
                if kw in query_lower:
                    scores[intent] += 0.3
        
        # 2. 问题类型分析
        for qtype, pattern in self.question_patterns.items():
            if re.search(pattern, query_lower):
                if qtype == "what":
                    scores[IntentType.CONCEPT_EXPLANATION] += 0.2
                elif qtype == "how":
                    scores[IntentType.CODE_QUESTION] += 0.2
                elif qtype == "why":
                    scores[IntentType.CONCEPT_EXPLANATION] += 0.2
        
        # 3. 领域关键词
        if keyword_set & self.code_keywords:
            scores[IntentType.CODE_QUESTION] += 0.3
        
        if keyword_set & self.concept_keywords:
            scores[IntentType.CONCEPT_EXPLANATION] += 0.3
        
        # 4. 检查是否是关系查询
        if any(kw in query_lower for kw in ["区别", "差异", "对比", "vs", "versus"]):
            scores[IntentType.RELATION_QUERY] += 0.4
        
        # 5. 检查是否是历史回顾
        if any(kw in query_lower for kw in ["我之前", "上次", "曾经", "学过"]):
            scores[IntentType.HISTORY_REVIEW] += 0.4
        
        # 找到最高分的意图
        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]
        
        # 计算置信度
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] > sorted_scores[1]:
            confidence = min(0.95, 0.5 + (sorted_scores[0] - sorted_scores[1]) * 0.5)
        else:
            confidence = 0.5
        
        # 如果没有明显意图，返回通用
        if max_score < 0.2:
            return IntentType.GENERAL, 0.5
        
        return max_intent, confidence


class QueryRewriter:
    """查询改写器"""
    
    def __init__(self):
        # 同义词映射
        self.synonyms = {
            "python": ["Python 编程", "Python 语言", "Python 开发"],
            "java": ["Java 编程", "Java 语言", "Java 开发"],
            "函数": ["function", "方法", "函数定义"],
            "类": ["class", "面向对象", "类定义"],
            "变量": ["variable", "数据类型", "变量声明"],
            "循环": ["loop", "for 循环", "while 循环", "迭代"],
            "列表": ["list", "数组", "序列"],
            "字典": ["dict", "dictionary", "映射", "hashmap"],
            "异常": ["exception", "错误处理", "try-catch"],
            "继承": ["inheritance", "派生", "子类"],
            "多态": ["polymorphism", "重载", "重写"],
            "封装": ["encapsulation", "数据隐藏"],
        }
    
    def rewrite(self, query: str, intent: str) -> List[str]:
        """
        改写查询
        
        Returns:
            查询变体列表
        """
        queries = [query]
        query_lower = query.lower()
        
        # 1. 同义词扩展
        for original, synonyms in self.synonyms.items():
            if original in query_lower:
                for synonym in synonyms:
                    new_query = query.replace(original, synonym)
                    if new_query != query:
                        queries.append(new_query)
        
        # 2. 添加关键词组合
        try:
            import jieba.analyse
            keywords = jieba.analyse.extract_tags(query, topK=5, withWeight=False)
            
            # 添加纯关键词查询
            if keywords:
                keyword_query = " ".join(keywords)
                if keyword_query != query:
                    queries.append(keyword_query)
                
                # 添加每个关键词的扩展
                for kw in keywords[:3]:
                    queries.append(f"{query} {kw}")
        except ImportError:
            pass
        
        # 3. 根据意图扩展
        if intent == IntentType.CONCEPT_EXPLANATION:
            queries.append(f"详细解释 {query}")
            queries.append(f"{query} 的概念和用法")
        
        elif intent == IntentType.CODE_QUESTION:
            queries.append(f"{query} 代码示例")
            queries.append(f"{query} 实现方法")
        
        elif intent == IntentType.RELATION_QUERY:
            queries.append(f"对比分析 {query}")
        
        # 去重
        seen = set()
        unique_queries = []
        for q in queries:
            if q not in seen:
                seen.add(q)
                unique_queries.append(q)
        
        return unique_queries[:10]  # 限制最多 10 个变体


# 全局实例
intent_classifier = IntentClassifier()
query_rewriter = QueryRewriter()


@router.post("/route", response_model=QueryRouterResponse)
async def route_query(request: QueryRouterRequest):
    """
    查询路由
    
    分析查询意图，选择最佳检索渠道
    """
    start_time = datetime.now()
    
    # 1. 意图识别
    intent, confidence = intent_classifier.classify(request.query)
    
    # 2. 提取关键词
    keywords = intent_classifier.extract_keywords(request.query)
    
    # 3. 查询改写
    rewritten_queries = query_rewriter.rewrite(request.query, intent)
    
    # 4. 获取检索渠道
    channels = INTENT_TO_CHANNELS.get(intent, ["semantic", "keyword"])
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    return QueryRouterResponse(
        query=request.query,
        intent=intent,
        confidence=round(confidence, 3),
        channels=channels,
        keywords=keywords,
        rewritten_queries=rewritten_queries
    )


@router.post("/classify")
async def classify_intent(query: str):
    """仅意图分类"""
    intent, confidence = intent_classifier.classify(query)
    keywords = intent_classifier.extract_keywords(query)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "query": query,
            "intent": intent,
            "confidence": round(confidence, 3),
            "keywords": keywords
        }
    }


@router.post("/rewrite")
async def rewrite_query(query: str, intent: Optional[str] = None):
    """查询改写"""
    if not intent:
        intent, _ = intent_classifier.classify(query)
    
    rewritten = query_rewriter.rewrite(query, intent)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "original_query": query,
            "intent": intent,
            "rewritten_queries": rewritten
        }
    }


@router.get("/intents")
async def list_intents():
    """列出所有意图类型"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "intents": {
                IntentType.CONCEPT_EXPLANATION: "概念解释 - 什么是 X",
                IntentType.RELATION_QUERY: "关系查询 - X 和 Y 的区别",
                IntentType.CODE_QUESTION: "代码问题 - 如何实现 X",
                IntentType.HISTORY_REVIEW: "历史回顾 - 我之前学过",
                IntentType.EXERCISE_FIND: "题目查找 - 练习题",
                IntentType.GENERAL: "通用查询"
            },
            "channels": {
                "semantic": "语义检索 (FAISS)",
                "keyword": "关键词检索 (BM25/ES)",
                "graph": "知识图谱检索 (Neo4j)"
            }
        }
    }


@router.get("/config")
async def get_router_config():
    """获取路由配置"""
    return {
        "code": 200,
        "data": {
            "intent_to_channels": INTENT_TO_CHANNELS,
            "description": {
                "concept_explanation": "概念解释 → 语义检索 + 图谱检索",
                "relation_query": "关系查询 → 图谱检索",
                "code_question": "代码问题 → 语义检索 + 关键词检索",
                "history_review": "历史回顾 → 关键词检索",
                "exercise_find": "题目查找 → 关键词检索 + 语义检索",
                "general": "通用查询 → 语义检索 + 关键词检索"
            }
        }
    }
