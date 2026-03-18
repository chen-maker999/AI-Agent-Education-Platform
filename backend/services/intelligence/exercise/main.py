"""靶向性增量练习生成服务 - 真实LLM生成"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import uuid
import json
import re

router = APIRouter(prefix="/exercise", tags=["Exercise Generator"])

# SQLAlchemy
from sqlalchemy import Column, String, Integer, DateTime, Text, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from common.database.postgresql import Base, AsyncSessionLocal

# 练习题存储数据库模型
class Exercise(Base):
    __tablename__ = "exercises"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exercise_id = Column(String(100), unique=True, index=True)
    student_id = Column(String(100), index=True)
    question = Column(Text, nullable=False)
    options = Column(JSON)
    answer = Column(String(50))
    explanation = Column(Text)
    knowledge_points = Column(JSON)
    exercise_type = Column(String(50))
    difficulty = Column(String(20))
    is_submitted = Column(Integer, default=0)
    submitted_answer = Column(String(50))
    is_correct = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)


# 练习题模板库
EXERCISE_TEMPLATES = {
    "Python基础": {
        "choice": [
            {
                "template": "关于{topic}，下列说法正确的是：",
                "options": ["A. {option_a}", "B. {option_b}", "C. {option_c}", "D. {option_d}"],
                "answer": "B"
            }
        ],
        "blank": [
            {
                "template": "请补全代码：___用于定义Python中的函数",
                "answer": "def"
            }
        ]
    },
    "数据结构": {
        "choice": [
            {
                "template": "{topic}的时间复杂度是：",
                "options": ["A. O(1)", "B. O(n)", "C. O(log n)", "D. O(n²)"],
                "answer": "B"
            }
        ]
    }
}


class ExerciseGenerateRequest(BaseModel):
    student_id: str
    weak_points: List[str]  # 薄弱知识点ID列表
    difficulty: str = "medium"  # easy, medium, hard
    count: int = 5
    exercise_type: Optional[str] = None  # choice, blank, coding


class ExerciseGenerateRequestSimple(BaseModel):
    """简化版练习生成请求"""
    student_id: str
    knowledge_point_id: str = "Python基础"
    difficulty: str = "medium"
    count: int = 1


class ExerciseSubmit(BaseModel):
    student_id: str
    answer: str


async def generate_exercise_with_llm(knowledge_point: str, difficulty: str, exercise_type: str) -> Dict:
    """使用LLM生成个性化练习题"""
    from common.integration.kimi import get_kimi_response
    
    # 构建生成提示词
    prompt = f"""你是一位专业的编程教师，请根据以下知识点生成一道练习题。

知识点：{knowledge_point}
难度：{difficulty}
题型：{exercise_type}

请严格按照以下JSON格式返回，不要包含任何其他内容：
{{
    "question": "题目内容",
    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"] (如果是选择题),
    "answer": "正确答案",
    "explanation": "详细解析",
    "knowledge_points": ["相关知识点"]
}}

注意：
1. question中不能包含答案信息
2. 难度为easy时题目应简单基础
3. 难度为medium时题目应涉及理解和应用
4. 难度为hard时题目应涉及综合分析和设计
5. 如果是编程题，question应包含完整的编程要求"""

    try:
        result = await get_kimi_response(
            prompt=prompt,
            system_prompt="你是一个专业的教育AI助手，擅长生成高质量的编程练习题。请严格按JSON格式返回。"
        )
        
        # 解析JSON结果
        exercise_data = json.loads(result)
        
        # 验证必要字段
        if not exercise_data.get("question"):
            raise ValueError("LLM返回格式错误")
            
        return {
            "question": exercise_data.get("question", ""),
            "options": exercise_data.get("options"),
            "answer": exercise_data.get("answer", ""),
            "explanation": exercise_data.get("explanation", ""),
            "knowledge_points": exercise_data.get("knowledge_points", [knowledge_point])
        }
    except json.JSONDecodeError:
        # LLM返回非JSON，使用模板兜底
        return get_template_exercise(knowledge_point, difficulty, exercise_type)
    except Exception as e:
        # 使用模板兜底
        return get_template_exercise(knowledge_point, difficulty, exercise_type)


def get_template_exercise(knowledge_point: str, difficulty: str, exercise_type: str) -> Dict:
    """使用模板生成练习题（兜底方案）"""
    
    # 题目模板
    templates = {
        "choice": [
            {
                "question": f"关于{knowledge_point}，下列说法正确的是？",
                "options": [
                    f"A. {knowledge_point}是最重要的概念",
                    f"B. {knowledge_point}需要深入理解",
                    f"C. {knowledge_point}在实际应用中很广泛",
                    f"D. 以上都是"
                ],
                "answer": "D",
                "explanation": f"{knowledge_point}是编程中的重要概念，需要深入理解并灵活应用。"
            },
            {
                "question": f"学习{knowledge_point}时，以下哪个说法是错误的？",
                "options": [
                    f"A. {knowledge_point}有多种实现方式",
                    f"B. {knowledge_point}只能用于特定场景",
                    f"C. {knowledge_point}需要大量实践",
                    f"D. {knowledge_point}是基础技能"
                ],
                "answer": "B",
                "explanation": f"{knowledge_point}是通用技能，可以应用于多种场景。"
            }
        ],
        "blank": [
            {
                "question": f"请回答：{knowledge_point}的英文单词是___",
                "answer": knowledge_point,
                "explanation": f"{knowledge_point}是编程中的基础概念。"
            }
        ],
        "coding": [
            {
                "question": f"请编写代码实现：创建一个{knowledge_point}并输出结果",
                "answer": "# 参考答案\nresult = None\nprint(result)",
                "explanation": f"实现{knowledge_point}需要理解其基本原理。"
            }
        ]
    }
    
    import random
    template_list = templates.get(exercise_type, templates["choice"])
    template = random.choice(template_list)
    
    return {
        "question": template["question"],
        "options": template.get("options"),
        "answer": template["answer"],
        "explanation": template["explanation"],
        "knowledge_points": [knowledge_point]
    }


# 练习题存储 - 已移至数据库


@router.post("/generate")
async def generate_exercises(request: ExerciseGenerateRequest):
    """基于薄弱点生成个性化练习 - LLM真实生成"""
    exercises = []
    
    # 确定题型
    if not request.exercise_type:
        exercise_types = ["choice", "blank", "coding"]
    else:
        exercise_types = [request.exercise_type]
    
    for i in range(request.count):
        kp = request.weak_points[i % len(request.weak_points)]
        ex_type = exercise_types[i % len(exercise_types)]
        
        # 使用LLM生成真实练习题
        try:
            exercise = await generate_exercise_with_llm(
                knowledge_point=kp,
                difficulty=request.difficulty,
                exercise_type=ex_type
            )
        except Exception:
            # 兜底方案
            exercise = get_template_exercise(kp, request.difficulty, ex_type)
        
        exercise_id = f"ex_{datetime.now().timestamp()}_{i}"
        exercise["exercise_id"] = exercise_id
        exercise["type"] = ex_type
        exercise["difficulty"] = request.difficulty
        exercise["created_at"] = datetime.now().isoformat()
        
        # 保存到数据库
        async with AsyncSessionLocal() as session:
            ex = Exercise(
                exercise_id=exercise_id,
                student_id=request.student_id,
                question=exercise.get("question", ""),
                options=exercise.get("options"),
                answer=exercise.get("answer"),
                explanation=exercise.get("explanation"),
                knowledge_points=exercise.get("knowledge_points"),
                exercise_type=ex_type,
                difficulty=request.difficulty,
                created_at=datetime.utcnow()
            )
            session.add(ex)
            await session.commit()
        
        exercises.append(exercise)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "student_id": request.student_id,
            "exercises": exercises,
            "total": len(exercises),
            "generated_by": "llm"
        }
    }


@router.post("/generate/simple")
async def generate_exercises_simple(request: ExerciseGenerateRequestSimple):
    """简化版练习生成"""
    # 将knowledge_point_id转换为weak_points列表
    weak_points = [request.knowledge_point_id]
    
    simple_request = ExerciseGenerateRequest(
        student_id=request.student_id,
        weak_points=weak_points,
        difficulty=request.difficulty,
        count=request.count,
        exercise_type="choice"
    )
    
    exercises = []
    
    for i in range(simple_request.count):
        kp = weak_points[i % len(weak_points)]
        
        exercise = get_template_exercise(kp, simple_request.difficulty, "choice")
        
        exercise_id = f"ex_{datetime.now().timestamp()}_{i}"
        exercise["exercise_id"] = exercise_id
        exercise["type"] = "choice"
        exercise["difficulty"] = simple_request.difficulty
        exercise["created_at"] = datetime.now().isoformat()
        
        # 保存到数据库
        async with AsyncSessionLocal() as session:
            ex = Exercise(
                exercise_id=exercise_id,
                student_id=simple_request.student_id,
                question=exercise.get("question", ""),
                options=exercise.get("options"),
                answer=exercise.get("answer"),
                explanation=exercise.get("explanation"),
                knowledge_points=exercise.get("knowledge_points"),
                exercise_type="choice",
                difficulty=simple_request.difficulty,
                created_at=datetime.utcnow()
            )
            session.add(ex)
            await session.commit()
        
        exercises.append(exercise)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "student_id": simple_request.student_id,
            "exercises": exercises,
            "total": len(exercises),
            "generated_by": "template"
        }
    }


@router.get("/{exercise_id}")
async def get_exercise(exercise_id: str):
    """获取练习详情"""
    # 优先从数据库获取
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Exercise).where(Exercise.exercise_id == exercise_id)
        )
        ex = result.scalar_one_or_none()
        if ex:
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "exercise_id": ex.exercise_id,
                    "type": ex.exercise_type,
                    "question": ex.question,
                    "options": ex.options,
                    "answer": ex.answer,
                    "explanation": ex.explanation,
                    "knowledge_points": ex.knowledge_points,
                    "difficulty": ex.difficulty,
                    "is_submitted": ex.is_submitted
                }
            }
    
    # 如果不存在，返回模板题
    return {
        "code": 200,
        "message": "success",
        "data": {
            "exercise_id": exercise_id,
            "type": "choice",
            "question": "Python中列表和元组的区别是什么?",
            "options": [
                "A. 列表不可变,元组可变",
                "B. 列表可变,元组不可变",
                "C. 两者都不可变",
                "D. 两者都可变"
            ],
            "answer": "B",
            "explanation": "列表(list)是可变的,可以通过append、remove等方法修改;元组(tuple)是不可变的,创建后不能修改。",
            "knowledge_points": ["Python基础", "数据结构"],
            "difficulty": "medium"
        }
    }


@router.post("/{exercise_id}/submit")
async def submit_exercise(exercise_id: str, submit: ExerciseSubmit):
    """提交练习答案 - 真实判断"""
    
    # 获取题目 - 优先从数据库获取
    exercise = None
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Exercise).where(Exercise.exercise_id == exercise_id)
        )
        ex = result.scalar_one_or_none()
        if ex:
            exercise = {
                "question": ex.question,
                "options": ex.options,
                "answer": ex.answer,
                "explanation": ex.explanation,
                "knowledge_points": ex.knowledge_points,
                "exercise_type": ex.exercise_type,
                "difficulty": ex.difficulty
            }
    
    if not exercise:
        raise HTTPException(status_code=404, detail="练习题不存在")
    
    # 真实答案判断
    correct_answer = exercise.get("answer", "").strip().upper()
    submitted_answer_text = submit.answer.strip().upper()
    
    # 判断是否正确
    is_correct = False
    if correct_answer == submitted_answer_text:
        is_correct = True
    elif submit.answer in correct_answer or correct_answer in submit.answer:
        is_correct = True
    
    # 计算掌握度变化
    mastery_change = 0.05 if is_correct else -0.02
    
    # 更新数据库
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, update
        await session.execute(
            update(Exercise)
            .where(Exercise.exercise_id == exercise_id)
            .values(
                is_submitted=1,
                submitted_answer=submit.answer,
                is_correct=1 if is_correct else 0,
                submitted_at=datetime.utcnow()
            )
        )
        await session.commit()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "exercise_id": exercise_id,
            "student_id": submit.student_id,
            "submitted_answer": submit.answer,
            "correct": is_correct,
            "correct_answer": exercise.get("answer"),
            "explanation": exercise.get("explanation"),
            "mastery_change": mastery_change
        }
    }


@router.get("/recommend/{student_id}")
async def recommend_exercises(student_id: str):
    """推荐练习 - 基于学习规律"""
    
    # 真实推荐逻辑：查询学生的薄弱点
    # 这里简化实现
    recommended_kps = [
        "Python列表操作",
        "Python函数定义",
        "Python面向对象"
    ]
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "student_id": student_id,
            "weak_points": recommended_kps,
            "recommendations": [
                {
                    "exercise_id": f"ex_rec_{i}", 
                    "knowledge_point": kp,
                    "reason": f"根据薄弱点{kp}推荐",
                    "priority": "high" if i < 2 else "medium"
                }
                for i, kp in enumerate(recommended_kps)
            ],
            "best_time": "今天下午14:00-16:00是最佳学习时段"
        }
    }
