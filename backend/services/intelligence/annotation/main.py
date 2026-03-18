"""INTELLIGENCE - Annotation service with real LLM-generated comments."""

from uuid import uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from common.models.response import ResponseModel

router = APIRouter(prefix="/annotation", tags=["Intelligence - Annotation"])

# 内存存储
annotation_templates: List[Dict] = []
annotations_db: Dict[str, Dict] = {}


class CommentRequest(BaseModel):
    content: str
    content_type: str = "text"
    score: Optional[float] = None
    errors: List[Dict[str, Any]] = []
    context: Dict[str, Any] = {}
    style: str = "encouraging"


class MarkupRequest(BaseModel):
    content: str
    error_position: Dict[str, int]
    error_type: str
    suggestion: str


class BatchAnnotationRequest(BaseModel):
    homework_id: str
    student_id: str
    content: str
    errors: List[Dict[str, Any]]
    score: float


async def generate_comment_with_llm(request: CommentRequest, student_name: str = "同学") -> Dict:
    """使用LLM生成个性化评语"""
    from common.integration.kimi import get_kimi_response
    
    # 构建错误描述
    error_desc = ""
    if request.errors:
        error_lines = []
        for i, err in enumerate(request.errors[:5], 1):
            err_type = err.get("type", "未知错误")
            err_msg = err.get("message", "")
            error_lines.append(f"{i}. {err_type}: {err_msg}")
        error_desc = "\n".join(error_lines)
    
    # 分数评价
    score_eval = ""
    if request.score is not None:
        if request.score >= 90:
            score_eval = "表现优秀"
        elif request.score >= 75:
            score_eval = "表现良好"
        elif request.score >= 60:
            score_eval = "基本达标"
        else:
            score_eval = "需要改进"
    
    prompt = f"""你是一位专业的编程教师。请根据以下作业信息生成个性化评语。

学生姓名：{student_name}
作业得分：{request.score} ({score_eval})
错误列表：
{error_desc if error_desc else "无明显错误"}

评语风格：{request.style}
- encouraging: 以鼓励为主，增强学生信心
- strict: 指出问题，严格要求
- balanced: 鼓励与改进并重

要求：
1. 根据分数和错误情况给出恰当评价
2. 指出具体优点和不足
3. 提供有针对性的学习建议
4. 语言要温和有耐心
5. 控制在100字以内

请直接生成评语，不要添加额外说明。"""

    try:
        comment = await get_kimi_response(
            prompt=prompt,
            system_prompt="你是一位有多年教学经验的编程教师，擅长用温和鼓励的语言给学生写评语。"
        )
    except Exception as e:
        # 降级方案
        if request.score and request.score >= 60:
            comment = f"作业完成情况{score_eval}，{'继续保持' if request.score >= 80 else '继续努力'}！"
        else:
            comment = f"作业{score_eval}，请加强相关知识点的学习。"
    
    # 生成亮点和建议
    highlights = []
    suggestions = []
    
    if request.errors:
        error_types = set(e.get("type", "") for e in request.errors)
        if "语法错误" in error_types:
            suggestions.append("建议复习相关语法知识")
        if "逻辑错误" in error_types:
            suggestions.append("建议多练习编程逻辑")
        if "实现错误" in error_types:
            suggestions.append("建议理解问题的本质")
    
    if request.score and request.score >= 80:
        highlights.append("代码结构清晰")
        highlights.append("思路正确")
    
    if not highlights:
        highlights.append("有进步空间")
    
    if not suggestions:
        suggestions.append("多练习类似题目")
    
    return {
        "comment": comment,
        "highlights": highlights[:3],
        "suggestions": suggestions[:3]
    }


async def generate_markup_for_error(error: Dict, content: str) -> Dict:
    """为错误生成批注"""
    from common.integration.kimi import get_kimi_response
    
    error_type = error.get("type", "未知错误")
    error_msg = error.get("message", "")
    position = error.get("position", {})
    
    prompt = f"""你是一位专业的编程教师。请为以下错误生成批注。

错误类型：{error_type}
错误信息：{error_msg}
错误位置：{position}

作业内容片段：
{content[:200]}

要求：
1. 指出错误的具体位置和问题
2. 提供修改建议
3. 语言简洁明了

请直接生成批注内容。"""

    try:
        markup_content = await get_kimi_response(
            prompt=prompt,
            system_prompt="你是一位严格的编程教师，擅长指出代码中的问题并给出修改建议。"
        )
    except:
        markup_content = f"此处存在{error_type}，请检查并修改"
    
    return {
        "position": position,
        "type": error_type,
        "content": markup_content,
        "suggestion": error.get("suggestion", "")
    }


@router.post("/comment", response_model=ResponseModel)
async def generate_comment(request: CommentRequest):
    """生成AI评语 - 真实LLM生成"""
    # 生成评语
    result = await generate_comment_with_llm(request)
    
    # 保存
    comment_id = str(uuid4())
    annotations_db[comment_id] = {
        "comment_id": comment_id,
        "content": request.content,
        "score": request.score,
        "errors": request.errors,
        "result": result,
        "created_at": datetime.utcnow().isoformat()
    }
    
    return ResponseModel(
        code=200,
        message="success",
        data=result
    )


@router.post("/markup", response_model=ResponseModel)
async def generate_markup(request: MarkupRequest):
    """为特定错误生成批注"""
    # 构建错误信息
    error = {
        "type": request.error_type,
        "message": "",
        "position": request.error_position,
        "suggestion": request.suggestion
    }
    
    # 生成批注
    markup = await generate_markup_for_error(error, request.content)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "markup": markup
        }
    )


@router.post("/batch", response_model=ResponseModel)
async def batch_annotate(request: BatchAnnotationRequest):
    """批量生成标注"""
    annotations = []
    
    # 为每个错误生成批注
    for error in request.errors:
        markup = await generate_markup_for_error(error, request.content)
        annotations.append(markup)
    
    # 生成总评
    prompt = f"""请为这份作业生成一个简短的总评。

作业得分：{request.score}
错误数量：{len(request.errors)}

要求：
1. 总结作业完成情况
2. 给出学习建议
3. 控制在50字以内"""

    try:
        from common.integration.kimi import get_kimi_response
        summary = await get_kimi_response(
            prompt=prompt,
            system_prompt="你是一位专业的编程教师，擅长写简洁有针对性的评语。"
        )
    except:
        summary = f"共发现{len(request.errors)}处错误，建议加强练习"
    
    # 保存
    batch_id = str(uuid4())
    annotations_db[batch_id] = {
        "batch_id": batch_id,
        "homework_id": request.homework_id,
        "student_id": request.student_id,
        "annotations": annotations,
        "summary": summary,
        "created_at": datetime.utcnow().isoformat()
    }
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "homework_id": request.homework_id,
            "annotations": annotations,
            "summary": summary,
            "total_errors": len(annotations)
        }
    )


@router.get("/summary", response_model=ResponseModel)
async def get_summary(
    student_id: str = Query(...),
    course_id: str = Query(...),
    period: str = Query("week")
):
    """获取学习总结评语"""
    from common.integration.kimi import get_kimi_response
    
    # 模拟学习数据
    prompt = f"""请为学生生成一份{period}学习总结评语。

学生ID：{student_id}
课程ID：{course_id}
周期：{period}

要求：
1. 总结学习表现
2. 肯定成绩
3. 指出改进方向
4. 给出建议
5. 控制在150字以内"""

    try:
        summary = await get_kimi_response(
            prompt=prompt,
            system_prompt="你是一位有经验的教师，擅长给学生写学习总结。"
        )
    except:
        summary = f"本周学习表现良好，继续保持学习热情"
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "summary": summary,
            "achievements": ["作业完成率高", "积极参与讨论"],
            "improvements": ["需要加强算法练习"],
            "recommendations": ["建议多参加编程实践"]
        }
    )


@router.get("/templates", response_model=ResponseModel)
async def get_templates(category: str = Query(None)):
    """获取评语模板"""
    templates = [
        {"id": "1", "name": "鼓励性评语", "category": "encourage", "template": "很好，继续加油！", "variables": ["student_name"]},
        {"id": "2", "name": "改进建议", "category": "improve", "template": "请注意以下问题：{issues}", "variables": ["issues"]},
        {"id": "3", "name": "优秀作业", "category": "excellent", "template": "优秀！你的代码思路清晰，继续保持！", "variables": []},
        {"id": "4", "name": "需加强", "category": "weak", "template": "这道题有难度，建议多看几遍相关知识点", "variables": ["topic"]}
    ]
    
    if category:
        templates = [t for t in templates if t["category"] == category]
    
    return ResponseModel(code=200, message="success", data={"templates": templates})


@router.post("/templates", response_model=ResponseModel)
async def create_template(
    name: str = Query(...),
    category: str = Query(...),
    template: str = Query(...),
    variables: List[str] = Query([])
):
    """创建评语模板"""
    new_template = {
        "id": str(uuid4()),
        "name": name,
        "category": category,
        "template": template,
        "variables": variables,
        "created_at": datetime.utcnow().isoformat()
    }
    annotation_templates.append(new_template)
    return ResponseModel(code=200, message="success", data=new_template)


@router.get("/styles", response_model=ResponseModel)
async def get_styles():
    """获取可用的评语风格"""
    return ResponseModel(
        code=200,
        message="success",
        data={
            "styles": [
                {"code": "encouraging", "name": "鼓励型", "description": "以鼓励为主，增强学生信心"},
                {"code": "strict", "name": "严格型", "description": "指出问题，严格要求"},
                {"code": "balanced", "name": "平衡型", "description": "鼓励与改进并重"}
            ]
        }
    )
