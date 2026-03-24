"""反馈收集服务 - 收集用户反馈用于 RAG 系统优化"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json
import os
import pickle
import hashlib

router = APIRouter(prefix="/feedback", tags=["Feedback Collection"])


# ==================== 配置 ====================
class FeedbackConfig:
    """反馈配置"""
    DATA_DIR = "data/feedback"
    FEEDBACK_FILE = os.path.join(DATA_DIR, "feedbacks.json")
    STATS_FILE = os.path.join(DATA_DIR, "feedback_stats.pkl")
    MAX_FEEDBACKS = 100000  # 最大存储反馈数


# ==================== 数据模型 ====================
class FeedbackType(str, Enum):
    """反馈类型"""
    RELEVANCE = "relevance"  # 相关性评分
    QUALITY = "quality"  # 质量评分
    CORRECTION = "correction"  # 纠正反馈
    SUGGESTION = "suggestion"  # 建议反馈
    BUG_REPORT = "bug_report"  # 错误报告


class RatingScale(str, Enum):
    """评分等级"""
    VERY_POOR = "1_very_poor"
    POOR = "2_poor"
    FAIR = "3_fair"
    GOOD = "4_good"
    EXCELLENT = "5_excellent"


class FeedbackRequest(BaseModel):
    """反馈提交请求"""
    query: str = Field(..., description="用户查询")
    response: str = Field(..., description="系统响应")
    feedback_type: FeedbackType = Field(..., description="反馈类型")
    rating: Optional[RatingScale] = Field(None, description="评分")
    score: Optional[float] = Field(None, ge=0, le=5, description="数值评分 (0-5)")
    comment: Optional[str] = Field(None, description="文字评论")
    user_id: Optional[str] = Field(None, description="用户 ID")
    course_id: Optional[str] = Field(None, description="课程 ID")
    session_id: Optional[str] = Field(None, description="会话 ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="附加元数据")

    class Config:
        use_enum_values = True


class FeedbackUpdateRequest(BaseModel):
    """反馈更新请求"""
    rating: Optional[RatingScale] = None
    score: Optional[float] = Field(None, ge=0, le=5)
    comment: Optional[str] = None
    is_helpful: Optional[bool] = None


class FeedbackResponse(BaseModel):
    """反馈响应"""
    feedback_id: str
    status: str
    message: str
    created_at: str


class FeedbackListResponse(BaseModel):
    """反馈列表响应"""
    feedbacks: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


# ==================== 反馈存储 ====================
class FeedbackStore:
    """
    反馈数据存储

    功能:
    - 持久化存储用户反馈
    - 支持查询和过滤
    - 统计分析
    - 导出功能
    """

    def __init__(self):
        self.feedbacks: Dict[str, Dict] = {}
        self.stats = {
            "total": 0,
            "by_type": {},
            "by_rating": {},
            "avg_score": 0,
            "helpful_count": 0,
            "not_helpful_count": 0
        }
        self._load()

    def _ensure_dir(self):
        """确保目录存在"""
        os.makedirs(FeedbackConfig.DATA_DIR, exist_ok=True)

    def _load(self):
        """加载反馈数据"""
        self._ensure_dir()

        # 加载反馈
        if os.path.exists(FeedbackConfig.FEEDBACK_FILE):
            try:
                with open(FeedbackConfig.FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                    self.feedbacks = json.load(f)
                print(f"[Feedback] 已加载 {len(self.feedbacks)} 条反馈")
            except Exception as e:
                print(f"[Feedback] 加载反馈失败：{e}")
                self.feedbacks = {}

        # 加载统计
        if os.path.exists(FeedbackConfig.STATS_FILE):
            try:
                with open(FeedbackConfig.STATS_FILE, 'rb') as f:
                    self.stats = pickle.load(f)
            except Exception as e:
                print(f"[Feedback] 加载统计失败：{e}")
                self._recalculate_stats()
        else:
            self._recalculate_stats()

    def _save(self):
        """保存反馈数据"""
        self._ensure_dir()

        try:
            # 保存反馈
            with open(FeedbackConfig.FEEDBACK_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.feedbacks, f, ensure_ascii=False, indent=2)

            # 保存统计
            with open(FeedbackConfig.STATS_FILE, 'wb') as f:
                pickle.dump(self.stats, f)
        except Exception as e:
            print(f"[Feedback] 保存失败：{e}")

    def _recalculate_stats(self):
        """重新计算统计信息"""
        self.stats = {
            "total": len(self.feedbacks),
            "by_type": {},
            "by_rating": {},
            "avg_score": 0,
            "helpful_count": 0,
            "not_helpful_count": 0
        }

        scores = []
        for feedback in self.feedbacks.values():
            # 按类型统计
            ftype = feedback.get("feedback_type", "unknown")
            self.stats["by_type"][ftype] = self.stats["by_type"].get(ftype, 0) + 1

            # 按评分统计
            rating = feedback.get("rating")
            if rating:
                self.stats["by_rating"][rating] = self.stats["by_rating"].get(rating, 0) + 1

            # 计算平均分
            score = feedback.get("score")
            if score is not None:
                scores.append(score)

            # 有用性统计
            if feedback.get("is_helpful") is True:
                self.stats["helpful_count"] += 1
            elif feedback.get("is_helpful") is False:
                self.stats["not_helpful_count"] += 1

        if scores:
            self.stats["avg_score"] = sum(scores) / len(scores)

    def add(self, feedback_data: Dict) -> str:
        """添加反馈"""
        # 生成反馈 ID
        feedback_id = hashlib.md5(
            f"{feedback_data['query']}:{feedback_data['response']}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        # 存储反馈
        self.feedbacks[feedback_id] = {
            **feedback_data,
            "feedback_id": feedback_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_helpful": None,
            "processed": False
        }

        # 限制存储数量
        if len(self.feedbacks) > FeedbackConfig.MAX_FEEDBACKS:
            # 删除最旧的反馈
            oldest_id = min(self.feedbacks.keys(), key=lambda k: self.feedbacks[k]["created_at"])
            del self.feedbacks[oldest_id]

        # 更新统计
        self._recalculate_stats()

        # 保存
        self._save()

        return feedback_id

    def get(self, feedback_id: str) -> Optional[Dict]:
        """获取反馈"""
        return self.feedbacks.get(feedback_id)

    def update(self, feedback_id: str, updates: Dict) -> bool:
        """更新反馈"""
        if feedback_id not in self.feedbacks:
            return False

        self.feedbacks[feedback_id].update(updates)
        self.feedbacks[feedback_id]["updated_at"] = datetime.utcnow().isoformat()

        # 更新统计
        self._recalculate_stats()

        # 保存
        self._save()

        return True

    def delete(self, feedback_id: str) -> bool:
        """删除反馈"""
        if feedback_id not in self.feedbacks:
            return False

        del self.feedbacks[feedback_id]

        # 更新统计
        self._recalculate_stats()

        # 保存
        self._save()

        return True

    def list_feedbacks(
        self,
        feedback_type: Optional[str] = None,
        course_id: Optional[str] = None,
        user_id: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        is_helpful: Optional[bool] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict]:
        """查询反馈列表"""
        results = list(self.feedbacks.values())

        # 过滤
        if feedback_type:
            results = [f for f in results if f.get("feedback_type") == feedback_type]

        if course_id:
            results = [f for f in results if f.get("course_id") == course_id]

        if user_id:
            results = [f for f in results if f.get("user_id") == user_id]

        if min_score is not None:
            results = [f for f in results if f.get("score", 0) >= min_score]

        if max_score is not None:
            results = [f for f in results if f.get("score", 5) <= max_score]

        if is_helpful is not None:
            results = [f for f in results if f.get("is_helpful") == is_helpful]

        if start_date:
            results = [f for f in results if f.get("created_at", "") >= start_date]

        if end_date:
            results = [f for f in results if f.get("created_at", "") <= end_date]

        # 排序（最新的在前）
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # 分页
        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        results = results[start:end]

        return results, total

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats

    def export(self, format: str = "json") -> str:
        """导出反馈数据"""
        if format == "json":
            return json.dumps(list(self.feedbacks.values()), ensure_ascii=False, indent=2)
        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            if not self.feedbacks:
                return ""

            fieldnames = list(list(self.feedbacks.values())[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.feedbacks.values())
            return output.getvalue()
        else:
            return json.dumps(list(self.feedbacks.values()), ensure_ascii=False, indent=2)

    def get_training_data(self, min_score: float = 4.0) -> List[Dict]:
        """获取用于训练的数据（高评分反馈）"""
        return [
            {
                "query": f["query"],
                "response": f["response"],
                "score": f.get("score", 0),
                "feedback_type": f.get("feedback_type")
            }
            for f in self.feedbacks.values()
            if f.get("score", 0) >= min_score and not f.get("processed", False)
        ]


# ==================== 全局实例 ====================
feedback_store = FeedbackStore()


@router.on_event("startup")
async def startup_event():
    """启动时加载数据"""
    print(f"[Feedback] 反馈服务初始化完成，已加载 {len(feedback_store.feedbacks)} 条反馈")


# ==================== API 接口 ====================
@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    提交反馈

    收集用户对 RAG 系统响应的反馈
    """
    feedback_data = request.dict()

    # 添加反馈
    feedback_id = feedback_store.add(feedback_data)

    return FeedbackResponse(
        feedback_id=feedback_id,
        status="success",
        message="反馈提交成功",
        created_at=datetime.utcnow().isoformat()
    )


@router.get("/{feedback_id}")
async def get_feedback(feedback_id: str):
    """获取反馈详情"""
    feedback = feedback_store.get(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")

    return {
        "code": 200,
        "data": feedback
    }


@router.put("/{feedback_id}")
async def update_feedback(feedback_id: str, request: FeedbackUpdateRequest):
    """更新反馈"""
    feedback = feedback_store.get(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")

    updates = request.dict(exclude_unset=True)
    success = feedback_store.update(feedback_id, updates)

    return {
        "code": 200 if success else 500,
        "message": "更新成功" if success else "更新失败"
    }


@router.delete("/{feedback_id}")
async def delete_feedback(feedback_id: str):
    """删除反馈"""
    success = feedback_store.delete(feedback_id)

    return {
        "code": 200 if success else 404,
        "message": "删除成功" if success else "删除失败"
    }


@router.get("/list")
async def list_feedbacks(
    feedback_type: Optional[str] = Query(None, description="反馈类型"),
    course_id: Optional[str] = Query(None, description="课程 ID"),
    user_id: Optional[str] = Query(None, description="用户 ID"),
    min_score: Optional[float] = Query(None, ge=0, le=5, description="最低评分"),
    max_score: Optional[float] = Query(None, ge=0, le=5, description="最高评分"),
    is_helpful: Optional[bool] = Query(None, description="是否有用"),
    start_date: Optional[str] = Query(None, description="开始日期 (ISO 格式)"),
    end_date: Optional[str] = Query(None, description="结束日期 (ISO 格式)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """查询反馈列表"""
    feedbacks, total = feedback_store.list_feedbacks(
        feedback_type=feedback_type,
        course_id=course_id,
        user_id=user_id,
        min_score=min_score,
        max_score=max_score,
        is_helpful=is_helpful,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )

    return {
        "code": 200,
        "data": {
            "feedbacks": feedbacks,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


@router.get("/stats")
async def get_feedback_stats():
    """获取反馈统计信息"""
    return {
        "code": 200,
        "data": feedback_store.get_stats()
    }


@router.post("/helpful/{feedback_id}")
async def mark_helpful(feedback_id: str, helpful: bool = True):
    """标记反馈是否有用"""
    feedback = feedback_store.get(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")

    success = feedback_store.update(feedback_id, {"is_helpful": helpful})

    return {
        "code": 200 if success else 500,
        "message": f"已标记为{'有用' if helpful else '无用'}"
    }


@router.get("/export/{format}")
async def export_feedback(format: str = "json"):
    """导出反馈数据"""
    data = feedback_store.export(format)
    return {
        "code": 200,
        "data": {
            "format": format,
            "count": len(feedback_store.feedbacks),
            "content": data
        }
    }


@router.get("/training-data")
async def get_training_data(
    min_score: float = Query(4.0, ge=0, le=5, description="最低评分")
):
    """获取用于训练的数据"""
    training_data = feedback_store.get_training_data(min_score)

    # 标记为已处理
    for item in training_data:
        for fid, feedback in feedback_store.feedbacks.items():
            if feedback.get("query") == item["query"] and feedback.get("response") == item["response"]:
                feedback_store.update(fid, {"processed": True})

    return {
        "code": 200,
        "data": {
            "training_samples": training_data,
            "total": len(training_data),
            "min_score": min_score
        }
    }


@router.post("/analyze")
async def analyze_feedback():
    """分析反馈数据"""
    stats = feedback_store.get_stats()

    # 计算更多指标
    total = stats["total"]
    analysis = {
        **stats,
        "satisfaction_rate": stats["helpful_count"] / max(total, 1),
        "low_score_count": stats["by_rating"].get("1_very_poor", 0) + stats["by_rating"].get("2_poor", 0),
        "high_score_count": stats["by_rating"].get("4_good", 0) + stats["by_rating"].get("5_excellent", 0),
        "feedback_types": stats["by_type"]
    }

    return {
        "code": 200,
        "data": analysis
    }
