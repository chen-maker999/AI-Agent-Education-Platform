"""练习文件生成服务 - 根据知识库文档生成PDF格式练习题"""

import uuid
import io
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from common.database.postgresql import Base, AsyncSessionLocal
from common.models.response import ResponseModel
from common.core.config import settings
from minio import Minio
from minio.error import S3Error
import json

router = APIRouter(prefix="/worksheet", tags=["Worksheet Generator"])

# SQLAlchemy Model - 练习文件记录
class Worksheet(Base):
    __tablename__ = "worksheets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worksheet_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    course = Column(String(100))
    source_doc_id = Column(String(100))
    source_filename = Column(String(500))
    file_url = Column(Text)
    file_size = Column(Integer, default=0)
    exercise_count = Column(Integer, default=0)
    exercise_type = Column(String(100))
    difficulty = Column(String(20))
    status = Column(String(50), default="pending")
    created_by = Column(String(100))
    # 保存练习题内容（JSON格式）
    exercises_content = Column("exercises_content", JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic Models
class WorksheetGenerateRequest(BaseModel):
    course_id: str = Field(..., description="知识库ID/课程ID")
    title: Optional[str] = Field(None, description="练习标题")
    exercise_count: int = Field(5, ge=1, le=50, description="练习题数量")
    exercise_types: List[str] = Field(["choice"], description="题型列表: choice, blank, coding, short_answer")
    difficulty: str = Field("medium", description="难度: easy, medium, hard")
    created_by: Optional[str] = Field(None, description="创建者")


class WorksheetCreate(BaseModel):
    title: str
    course: Optional[str] = None
    source_doc_id: Optional[str] = None
    source_filename: Optional[str] = None
    exercise_count: int = 5
    exercise_type: Optional[str] = None
    difficulty: str = "medium"
    created_by: Optional[str] = None


class ExerciseItem(BaseModel):
    question: str
    options: Optional[List[str]] = None
    answer: str
    explanation: Optional[str] = None
    exercise_type: str = "choice"
    difficulty: str = "medium"
    knowledge_point: Optional[str] = None


# MinIO Client
def get_minio_client() -> Minio:
    """Get MinIO client."""
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )


# ==================== 练习生成核心逻辑 ====================

async def generate_exercises_from_documents(
    course_id: str,
    count: int,
    exercise_types: List[str],
    difficulty: str
) -> List[Dict]:
    """从知识库文档生成练习题"""
    import logging
    logger = logging.getLogger(__name__)

    exercises = []

    try:
        from services.knowledge.rag.main import RAGDocument
        from sqlalchemy import select, text

        logger.info(f"[Worksheet] 开始生成练习, course_id={course_id}, count={count}")

        # 使用原始 SQL 查询确保能获取数据
        async with AsyncSessionLocal() as session:
            # 先检查表是否存在
            try:
                check_result = await session.execute(text("SELECT COUNT(*) FROM rag_documents"))
                total_count = check_result.scalar()
                logger.info(f"[Worksheet] rag_documents 表存在，共有 {total_count} 条记录")
            except Exception as e:
                logger.error(f"[Worksheet] 查询 rag_documents 失败: {e}")
                return []

            # 查询文档
            if course_id in ['default', '', None]:
                query = select(RAGDocument).limit(10)
            else:
                query = select(RAGDocument).where(RAGDocument.course_id == course_id).limit(10)

            result = await session.execute(query)
            documents = result.scalars().all()

        logger.info(f"[Worksheet] 查询到文档数量: {len(documents)}")

        if not documents:
            logger.warning(f"[Worksheet] 未找到课程 {course_id} 的文档")
            return []

        # 构建知识内容摘要
        knowledge_content = "\n\n".join([
            f"文档片段{i+1} [{doc.course_id}]: {doc.content[:500]}"
            for i, doc in enumerate(documents[:5])
        ])

        logger.info(f"[Worksheet] 准备调用 Kimi API 生成练习...")

        # 使用LLM生成练习题
        try:
            from common.integration.kimi import get_kimi_response

            exercise_type_prompts = {
                "choice": "选择题（提供4个选项）",
                "blank": "填空题",
                "coding": "编程题",
                "short_answer": "简答题"
            }

            type_descriptions = [exercise_type_prompts.get(t, t) for t in exercise_types]
            type_str = "、".join(type_descriptions)

            difficulty_prompts = {
                "easy": "题目应简单基础，考察基本概念和定义",
                "medium": "题目应涉及理解和应用，需要一定分析能力",
                "hard": "题目应涉及综合分析和设计，需要深入理解"
            }

            prompt = f"""你是一位专业的编程教师。请根据以下知识内容生成{count}道练习题。

知识内容：
{knowledge_content}

题型要求：{type_str}
难度要求：{difficulty_prompts.get(difficulty, '中等难度')}

请严格按照以下JSON格式返回，不要包含任何其他内容：
{{
    "exercises": [
        {{
            "question": "题目内容（选择题要包含完整题干）",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"] (选择题必须有此项),
            "answer": "正确答案",
            "explanation": "详细解析",
            "exercise_type": "choice/blank/coding/short_answer",
            "knowledge_point": "相关知识点"
        }}
    ]
}}

注意：
1. 每个题目的answer必须与选项对应（选择题答案为A/B/C/D）
2. 填空题答案应该简洁明确
3. 编程题和简答题应提供评分要点
4. 生成的题目必须与提供的知识内容相关"""

            logger.info(f"[Worksheet] 调用 Kimi API...")
            result = await get_kimi_response(
                prompt=prompt,
                system_prompt="你是一个专业的教育AI助手，擅长生成高质量的编程练习题。请严格按JSON格式返回。"
            )
            logger.info(f"[Worksheet] Kimi API 返回成功，长度: {len(result) if result else 0}")

            data = json.loads(result)
            exercises = data.get("exercises", [])
            logger.info(f"[Worksheet] 解析到练习题数量: {len(exercises)}")

        except json.JSONDecodeError as e:
            logger.error(f"[Worksheet] JSON解析失败: {e}, 返回内容: {result[:500] if result else 'None'}")
            exercises = get_fallback_exercises(count, exercise_types, difficulty)
        except Exception as e:
            logger.error(f"[Worksheet] Kimi API 调用失败: {e}", exc_info=True)
            exercises = get_fallback_exercises(count, exercise_types, difficulty)

    except Exception as e:
        logger.error(f"[Worksheet] 整体生成失败: {e}", exc_info=True)
        raise

    return exercises[:count]


def get_fallback_exercises(count: int, exercise_types: List[str], difficulty: str) -> List[Dict]:
    """使用模板生成练习题（兜底方案）"""
    import random

    knowledge_topics = ["Python基础语法", "数据结构与算法", "函数与模块", "面向对象编程", "异常处理"]

    templates = [
        {
            "question": "以下关于{topic}的说法，正确的是？",
            "options": ["A. {topic}是最基础的概念", "B. {topic}在实际开发中不常用", "C. {topic}不需要深入理解", "D. {topic}是高级特性"],
            "answer": "A",
            "explanation": "{topic}是编程中的基础概念，需要扎实掌握。",
            "exercise_type": "choice"
        },
        {
            "question": "请简述{topic}的核心特点和使用场景。",
            "answer": "核心特点：1) 简洁高效 2) 易于理解 3) 实用性强\n使用场景：适用于日常开发和项目实践。",
            "explanation": "考察对{topic}的理解深度。",
            "exercise_type": "short_answer"
        },
        {
            "question": "补全代码：在Python中，___用于定义一个函数。",
            "answer": "def",
            "explanation": "def是Python中定义函数的关键字。",
            "exercise_type": "blank"
        },
        {
            "question": "编写一个函数，实现{topic}的核心功能。",
            "answer": "def core_function():\n    # 实现逻辑\n    return result",
            "explanation": "考察实际编码能力。",
            "exercise_type": "coding"
        }
    ]

    exercises = []
    for i in range(count):
        template = templates[i % len(templates)]
        topic = random.choice(knowledge_topics)

        exercise = {
            "question": template["question"].format(topic=topic),
            "options": [opt.format(topic=topic) for opt in template["options"]] if template.get("options") else None,
            "answer": template["answer"],
            "explanation": template["explanation"].format(topic=topic),
            "exercise_type": exercise_types[i % len(exercise_types)],
            "knowledge_point": topic
        }
        exercises.append(exercise)

    return exercises


# ==================== PDF生成逻辑 ====================

def generate_pdf_content(
    title: str,
    course: str,
    exercises: List[Dict],
    difficulty: str,
    created_by: Optional[str] = None
) -> bytes:
    """生成PDF格式的练习文件内容"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
    except ImportError:
        raise ImportError("请安装 reportlab: pip install reportlab")

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    # 自定义样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=22,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a1a2e')
    )

    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=10,
        textColor=colors.HexColor('#4a4a4a')
    )

    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=8,
        leading=18,
        textColor=colors.HexColor('#1a1a1a')
    )

    option_style = ParagraphStyle(
        'Option',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=4,
        leftIndent=20,
        leading=16,
        textColor=colors.HexColor('#333333')
    )

    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER
    )

    elements = []

    # 标题
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 10))

    # 基本信息
    current_date = datetime.now().strftime("%Y年%m月%d日")
    difficulty_names = {"easy": "简单", "medium": "中等", "hard": "困难"}
    difficulty_text = difficulty_names.get(difficulty, "中等")

    info_text = f"课程：{course or '通用'}&nbsp;&nbsp;&nbsp;&nbsp;难度：{difficulty_text}&nbsp;&nbsp;&nbsp;&nbsp;题目数：{len(exercises)}&nbsp;&nbsp;&nbsp;&nbsp;日期：{current_date}"
    if created_by:
        info_text += f"&nbsp;&nbsp;&nbsp;&nbsp;出题人：{created_by}"

    elements.append(Paragraph(info_text, info_style))
    elements.append(Spacer(1, 20))

    # 分隔线
    line_data = [['']]
    line_table = Table(line_data, colWidths=[17*cm])
    line_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 20))

    # 遍历添加每道题目
    for idx, exercise in enumerate(exercises, 1):
        ex_type = exercise.get("exercise_type", "choice")
        type_names = {
            "choice": "选择题",
            "blank": "填空题",
            "coding": "编程题",
            "short_answer": "简答题"
        }
        type_text = type_names.get(ex_type, "题目")

        # 题号和题型
        q_header = f"<b>第 {idx} 题</b>（{type_text}）"
        elements.append(Paragraph(q_header, header_style))

        # 题目内容
        question_text = exercise.get("question", "")
        elements.append(Paragraph(question_text, question_style))

        # 选项（如果是选择题）
        if ex_type == "choice" and exercise.get("options"):
            for option in exercise["options"]:
                elements.append(Paragraph(option, option_style))
            elements.append(Spacer(1, 10))

        # 填空题提示
        elif ex_type == "blank":
            elements.append(Paragraph("（请在下方空白处作答）", option_style))
            elements.append(Spacer(1, 20))

        # 编程题/简答题提示
        elif ex_type in ["coding", "short_answer"]:
            elements.append(Spacer(1, 30))

        # 换页（每5题一页）
        if idx % 5 == 0 and idx < len(exercises):
            elements.append(PageBreak())

    # 答案区域（单独一页）
    elements.append(PageBreak())
    elements.append(Paragraph("参考答案", title_style))
    elements.append(Spacer(1, 20))

    for idx, exercise in enumerate(exercises, 1):
        ex_type = exercise.get("exercise_type", "choice")
        type_names = {
            "choice": "选择题",
            "blank": "填空题",
            "coding": "编程题",
            "short_answer": "简答题"
        }

        answer_text = f"<b>第 {idx} 题</b>（{type_names.get(ex_type, '题')}）"
        elements.append(Paragraph(answer_text, header_style))

        # 题目简要
        q_brief = exercise.get("question", "")[:80] + "..." if len(exercise.get("question", "")) > 80 else exercise.get("question", "")
        elements.append(Paragraph(f"题目：{q_brief}", question_style))

        # 答案
        answer = exercise.get("answer", "")
        answer_style = ParagraphStyle(
            'Answer',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=4,
            textColor=colors.HexColor('#2e7d32')
        )
        elements.append(Paragraph(f"<b>答案：</b>{answer}", answer_style))

        # 解析
        if exercise.get("explanation"):
            exp_style = ParagraphStyle(
                'Explanation',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=15,
                textColor=colors.HexColor('#666666'),
                leading=14
            )
            elements.append(Paragraph(f"<i>解析：{exercise['explanation']}</i>", exp_style))

        elements.append(Spacer(1, 10))

    # 页脚
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#999999'))
        footer_text = "AI-Agent教育平台 - 智能练习生成系统"
        canvas.drawCentredString(A4[0] / 2, 1*cm, footer_text)
        canvas.restoreState()

    doc.build(elements, onFirstPage=footer, onLaterPages=footer)

    pdf_content = buffer.getvalue()
    buffer.close()

    return pdf_content


# ==================== API 路由 ====================

@router.post("/generate", response_model=ResponseModel)
async def generate_worksheet(request: WorksheetGenerateRequest):
    """根据知识库文档生成练习PDF文件"""
    try:
        course_id = request.course_id
        title = request.title or f"练习题 - {datetime.now().strftime('%Y%m%d%H%M')}"

        # 生成练习题
        exercises = await generate_exercises_from_documents(
            course_id=course_id,
            count=request.exercise_count,
            exercise_types=request.exercise_types,
            difficulty=request.difficulty
        )

        if not exercises:
            return ResponseModel(
                code=400,
                message="未找到相关知识库文档，请先上传文档到知识库",
                data=None
            )

        # 生成PDF
        exercise_type_str = "/".join(request.exercise_types)
        pdf_content = generate_pdf_content(
            title=title,
            course=course_id,
            exercises=exercises,
            difficulty=request.difficulty,
            created_by=request.created_by
        )

        # 上传到MinIO
        worksheet_id = f"ws_{datetime.now().timestamp()}"
        filename = f"{title}.pdf"
        object_name = f"worksheets/{course_id}/{worksheet_id}/{filename}"

        try:
            client = get_minio_client()
            bucket_name = "edu-worksheets"
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
            client.put_object(
                bucket_name, object_name, io.BytesIO(pdf_content),
                length=len(pdf_content), content_type="application/pdf"
            )
            file_url = f"http://{settings.MINIO_ENDPOINT}/{bucket_name}/{object_name}"
        except Exception as e:
            file_url = None

        # 保存到数据库（包含练习内容）
        async with AsyncSessionLocal() as session:
            worksheet = Worksheet(
                worksheet_id=worksheet_id,
                title=title,
                course=course_id,
                file_url=file_url,
                file_size=len(pdf_content),
                exercise_count=len(exercises),
                exercise_type=exercise_type_str,
                difficulty=request.difficulty,
                status="completed",
                created_by=request.created_by,
                exercises_content=exercises
            )
            session.add(worksheet)
            await session.commit()

        return ResponseModel(
            code=200,
            message="练习文件生成成功",
            data={
                "worksheet_id": worksheet_id,
                "title": title,
                "exercise_count": len(exercises),
                "exercises": exercises[:5],
                "file_url": file_url,
                "file_size": len(pdf_content)
            }
        )

    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"缺少依赖库: {str(e)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/list", response_model=ResponseModel)
async def list_worksheets(
    course_id: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """获取练习文件列表"""
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"[Worksheet List] course_id={course_id}, page={page}, page_size={page_size}")

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func, text

        # 先检查表是否存在以及记录数
        try:
            count_result = await session.execute(text("SELECT COUNT(*) FROM worksheets"))
            total_all = count_result.scalar()
            logger.info(f"[Worksheet List] worksheets 表共有 {total_all} 条记录")
        except Exception as e:
            logger.error(f"[Worksheet List] 查询 worksheets 表失败: {e}")

        query = select(Worksheet)
        count_query = select(func.count(Worksheet.id))

        if course_id:
            query = query.where(Worksheet.course == course_id)
            count_query = count_query.where(Worksheet.course == course_id)
            logger.info(f"[Worksheet List] 按 course_id={course_id} 筛选")

        query = query.order_by(Worksheet.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        result = await session.execute(query)
        worksheets = result.scalars().all()

        logger.info(f"[Worksheet List] 查询到 {len(worksheets)} 条记录，总计 {total} 条")

        items = [{
            "worksheet_id": w.worksheet_id,
            "title": w.title,
            "course": w.course,
            "source_filename": w.source_filename,
            "exercise_count": w.exercise_count,
            "exercise_type": w.exercise_type,
            "difficulty": w.difficulty,
            "status": w.status,
            "file_url": w.file_url,
            "file_size": w.file_size,
            "created_by": w.created_by,
            "created_at": w.created_at.isoformat() if w.created_at else None
        } for w in worksheets]

        return ResponseModel(
            code=200,
            message="查询成功",
            data={
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )


@router.get("/{worksheet_id}", response_model=ResponseModel)
async def get_worksheet(worksheet_id: str):
    """获取练习文件详情"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Worksheet).where(Worksheet.worksheet_id == worksheet_id)
        )
        w = result.scalar_one_or_none()

        if not w:
            raise HTTPException(status_code=404, detail="练习文件不存在")

        return ResponseModel(
            code=200,
            message="查询成功",
            data={
                "worksheet_id": w.worksheet_id,
                "title": w.title,
                "course": w.course,
                "source_filename": w.source_filename,
                "exercise_count": w.exercise_count,
                "exercise_type": w.exercise_type,
                "difficulty": w.difficulty,
                "status": w.status,
                "file_url": w.file_url,
                "file_size": w.file_size,
                "created_by": w.created_by,
                "created_at": w.created_at.isoformat() if w.created_at else None
            }
        )


@router.get("/{worksheet_id}/download")
async def download_worksheet(worksheet_id: str):
    """下载练习文件PDF"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Worksheet).where(Worksheet.worksheet_id == worksheet_id)
        )
        w = result.scalar_one_or_none()

        if not w:
            raise HTTPException(status_code=404, detail="练习文件不存在")

        # 生成新的PDF（包含答案）
        exercises = await generate_exercises_from_documents(
            course_id=w.course or "default",
            count=w.exercise_count or 5,
            exercise_types=[w.exercise_type.split("/")[0]] if w.exercise_type else ["choice"],
            difficulty=w.difficulty or "medium"
        )

        pdf_content = generate_pdf_content(
            title=w.title,
            course=w.course,
            exercises=exercises,
            difficulty=w.difficulty or "medium",
            created_by=w.created_by
        )

        filename = f"{w.title}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
            }
        )


@router.delete("/{worksheet_id}", response_model=ResponseModel)
async def delete_worksheet(worksheet_id: str):
    """删除练习文件"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, delete
        result = await session.execute(
            select(Worksheet).where(Worksheet.worksheet_id == worksheet_id)
        )
        w = result.scalar_one_or_none()

        if not w:
            raise HTTPException(status_code=404, detail="练习文件不存在")

        # 从MinIO删除
        try:
            if w.file_url:
                client = get_minio_client()
                bucket_name = "edu-worksheets"
                object_name = f"worksheets/{w.course}/{worksheet_id}/{w.title}.pdf"
                client.remove_object(bucket_name, object_name)
        except Exception:
            pass

        await session.execute(
            delete(Worksheet).where(Worksheet.worksheet_id == worksheet_id)
        )
        await session.commit()

        return ResponseModel(code=200, message="删除成功")


@router.get("/preview/{worksheet_id}", response_model=ResponseModel)
async def preview_worksheet(worksheet_id: str):
    """预览练习题内容（直接从数据库读取，不重新生成）"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Worksheet).where(Worksheet.worksheet_id == worksheet_id)
        )
        w = result.scalar_one_or_none()

        if not w:
            raise HTTPException(status_code=404, detail="练习文件不存在")

        # 直接返回已保存的练习内容
        exercises = w.exercises_content or []

        return ResponseModel(
            code=200,
            message="预览成功",
            data={
                "worksheet_id": w.worksheet_id,
                "title": w.title,
                "course": w.course,
                "exercise_count": w.exercise_count,
                "difficulty": w.difficulty,
                "exercise_type": w.exercise_type,
                "file_url": w.file_url,
                "file_size": w.file_size,
                "status": w.status,
                "created_by": w.created_by,
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "exercises": exercises
            }
        )


@router.get("/list", response_model=ResponseModel)