"""意图识别和路由服务 (ROUTER)"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import re

router = APIRouter(prefix="/router", tags=["Intent Router"])

# 意图分类规则
INTENT_PATTERNS = {
    "概念解释": {
        "keywords": ["什么是", "是什么", "定义", "解释", "含义", "概念", "原理", "为什么"],
        "channels": ["semantic", "graph"]
    },
    "关系查询": {
        "keywords": ["关系", "关联", "区别", "联系", "和", "与", "对比"],
        "channels": ["graph"]
    },
    "题目查找": {
        "keywords": ["题", "练习", "作业", "考试", "题目", "求解", "答案"],
        "channels": ["keyword", "semantic"]
    },
    "代码问题": {
        "keywords": ["代码", "函数", "方法", "编程", "写", "实现", "程序", "def", "class"],
        "channels": ["semantic", "keyword"]
    },
    "历史回顾": {
        "keywords": ["之前", "之前讲过", "上次", "以前", "历史"],
        "channels": ["keyword"]
    }
}

DEFAULT_CHANNELS = ["semantic", "keyword"]


class QueryIntentRequest(BaseModel):
    query: str
    course_id: Optional[str] = None
    student_id: Optional[str] = None


class QueryIntentResponse(BaseModel):
    query: str
    intent: str
    confidence: float
    channels: List[str]
    features: Dict[str, Any]


def extract_query_features(query: str) -> Dict[str, Any]:
    """提取查询特征"""
    features = {
        "query_length": len(query),
        "word_count": len(query.split()),
        "has_question_mark": "？" in query or "?" in query,
        "has_code": bool(re.search(r'(def|class|function|var|let|const|import)', query)),
        "question_type": detect_question_type(query)
    }
    return features


def detect_question_type(query: str) -> str:
    """检测问题类型"""
    question_patterns = {
        "what": r"(什么是|是什么|哪个|哪些|什么)",
        "why": r"(为什么|为何|原因|怎么)",
        "how": r"(如何|怎样|怎么|方法)",
        "when": r"(什么时候|何时|时间)",
        "where": r"(哪里|何处|位置)"
    }
    
    for qtype, pattern in question_patterns.items():
        if re.search(pattern, query):
            return qtype
    return "unknown"


def classify_intent(query: str) -> tuple:
    """意图分类"""
    query_lower = query.lower()
    best_intent = "general"
    best_score = 0
    
    for intent_name, intent_info in INTENT_PATTERNS.items():
        score = 0
        keywords = intent_info.get("keywords", [])
        
        for keyword in keywords:
            if keyword in query_lower:
                score += 1
        
        if score > best_score:
            best_score = score
            best_intent = intent_name
    
    # 计算置信度
    if best_score > 0:
        confidence = min(0.5 + best_score * 0.1, 0.95)
    else:
        confidence = 0.5
    
    # 获取路由渠道
    if best_intent in INTENT_PATTERNS:
        channels = INTENT_PATTERNS[best_intent]["channels"]
    else:
        channels = DEFAULT_CHANNELS
    
    return best_intent, confidence, channels


@router.post("/intent", response_model=QueryIntentResponse)
async def classify_query_intent(request: QueryIntentRequest):
    """意图分类接口"""
    features = extract_query_features(request.query)
    intent, confidence, channels = classify_intent(request.query)
    
    return QueryIntentResponse(
        query=request.query,
        intent=intent,
        confidence=confidence,
        channels=channels,
        features=features
    )


@router.get("/intents")
async def get_supported_intents():
    """获取支持的意图类型"""
    return {
        "code": 200,
        "data": {
            "intents": INTENT_PATTERNS,
            "default_channels": DEFAULT_CHANNELS
        }
    }
