"""作业生成服务 - 结合知识库内容，大模型生成 PDF 作业文件"""

import io
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from common.database.postgresql import Base, AsyncSessionLocal
from common.models.response import ResponseModel
from common.core.config import settings
from minio import Minio
from minio.error import S3Error
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.pdfbase.pdfmetrics import registerFontFamily

router = APIRouter(prefix="/homework-gen", tags=["Homework Generator"])

BUCKET_HOMEWORK = "homework-files"
BUCKET_GENERATED = "generated-homework"

# 注册 ReportLab 内置的 CJK 字体
try:
    from reportlab.pdfbase import cidfonts
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    pdfmetrics.registerFont(UnicodeCIDFont('STHeiti-Regular'))
    print("成功注册 ReportLab 内置 CJK 字体")
except Exception as e:
    print(f"注册 CJK 字体失败: {e}")

# 注册中文字体（系统字体，优先于 CJK 字体）
chinese_font_registered = False
try:
    # 尝试使用系统中文字体
    import os
    font_paths = [
        # Windows
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        # Linux
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Hiragino Sans GB.ttc",
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                # 注册为常规字体，使用较大索引尝试
                font_name = 'ChineseFont'
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                # 如果是 TTC 文件，尝试注册其他样式
                if font_path.endswith('.ttc'):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFontBold', font_path, 1))
                    except:
                        pass
                # 设置字体族
                addMapping('ChineseFont', 0, 0, 'ChineseFont')  # normal
                addMapping('ChineseFont', 0, 1, 'ChineseFontBold')  # bold
                addMapping('ChineseFont', 1, 0, 'ChineseFont')  # italic
                addMapping('ChineseFont', 1, 1, 'ChineseFontBold')  # bold-italic
                chinese_font_registered = True
                print(f"成功注册中文字体: {font_path}")
                break
            except Exception as e:
                print(f"字体 {font_path} 注册失败: {e}")
                continue

    if not chinese_font_registered:
        print("警告：未找到中文字体，PDF 中文可能显示为方框")
except Exception as e:
    print(f"字体注册失败: {e}")


# ==================== SQLAlchemy Model ====================
class GeneratedHomework(Base):
    __tablename__ = "generated_homework"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    homework_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    course = Column(String(100))
    course_id = Column(String(100))
    source_type = Column(String(50), default="knowledge_base")  # knowledge_base | document
    source_doc_id = Column(String(100))
    file_url = Column(Text)
    file_size = Column(Integer, default=0)
    file_key = Column(String(500))  # MinIO object key
    question_count = Column(Integer, default=0)
    difficulty = Column(String(20))
    status = Column(String(50), default="pending")
    created_by = Column(String(100))
    generation_params = Column("generation_params", JSON, default=dict)  # 保存生成参数
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


# ==================== Pydantic Models ====================
class HomeworkGenRequest(BaseModel):
    course_id: Optional[str] = Field("general", description="课程/知识库 ID，不填则使用通用模式")
    title: Optional[str] = Field(None, description="作业标题，默认自动生成")
    question_count: int = Field(5, ge=1, le=50, description="题目数量")
    question_types: List[str] = Field(
        ["choice"], description="题型：choice(选择), blank(填空), short_answer(简答), coding(编程)"
    )
    difficulty: str = Field("medium", description="难度: easy / medium / hard / mixed")
    include_answers: bool = Field(True, description="是否包含参考答案")
    knowledge_point_ids: Optional[List[str]] = Field(None, description="指定知识点 ID 列表，不填则全选")
    created_by: Optional[str] = Field(None, description="创建者 ID")


class HomeworkGenResponse(BaseModel):
    homework_id: str
    title: str
    course: str
    question_count: int
    file_url: Optional[str]
    file_size: int
    status: str
    preview_questions: Optional[List[Dict]] = None


# ==================== MinIO Client ====================
def get_minio_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )


def ensure_bucket(client: Minio, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


# ==================== 知识库内容获取 ====================
async def fetch_knowledge_content(course_id: str, point_ids: Optional[List[str]] = None) -> str:
    """
    从知识库获取内容文本，用于喂给大模型生成作业。
    优先获取知识点描述 + RAG 文档内容。
    """
    content_parts = []
    async with AsyncSessionLocal() as session:
        try:
            # 1. 获取知识点
            from sqlalchemy import select, text
            if point_ids:
                result = await session.execute(
                    select(KnowledgePoint).where(
                        KnowledgePoint.point_id.in_(point_ids),
                        KnowledgePoint.course_id == course_id
                    )
                )
            else:
                result = await session.execute(
                    select(KnowledgePoint).where(KnowledgePoint.course_id == course_id)
                )
            points = result.scalars().all()

            if points:
                content_parts.append("【知识点】")
                for p in points[:20]:  # 最多 20 个知识点
                    name = p.name or ""
                    desc = p.description or ""
                    code = p.code or ""
                    if name or desc:
                        content_parts.append(f"· {code} {name}: {desc[:200]}")

            # 2. 尝试获取 RAG 文档片段
            try:
                result2 = await session.execute(
                    select(RAGDocument).where(RAGDocument.course_id == course_id).limit(10)
                )
                docs = result2.scalars().all()
                if docs:
                    content_parts.append("\n【相关文档内容】")
                    for doc in docs:
                        chunk_text = doc.content[:500] if doc.content else ""
                        if chunk_text:
                            content_parts.append(f"[{doc.doc_title or '文档片段'}] {chunk_text}")
            except Exception:
                pass

        except Exception:
            pass

    return "\n".join(content_parts) if content_parts else "通用学科知识内容"


# 延迟导入（表可能不存在）
KnowledgePoint = None
RAGDocument = None


def _ensure_lazy_refs():
    global KnowledgePoint, RAGDocument
    if KnowledgePoint is None:
        try:
            from sqlalchemy import select
            from services.knowledge.points.main import KnowledgePoint as KP
            KnowledgePoint = KP
        except Exception:
            class _DummyKP:
                point_id = ""
                course_id = ""
                name = ""
                description = ""
                code = ""
            KnowledgePoint = _DummyKP

    if RAGDocument is None:
        try:
            from services.knowledge.rag.main import RAGDocument as RD
            RAGDocument = RD
        except Exception:
            class _DummyRD:
                course_id = ""
                content = ""
                doc_title = ""
            RAGDocument = _DummyRD


# ==================== PDF 生成 ====================
def generate_homework_pdf(
    title: str,
    course: str,
    questions: List[Dict],
    difficulty: str,
    include_answers: bool = True,
    created_by: Optional[str] = None,
    homework_id: str = ""
) -> bytes:
    """生成作业 PDF 文件"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, PageBreak,
            Table, TableStyle, HRFlowable
        )
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    except ImportError:
        raise ImportError("请安装 reportlab: pip install reportlab")

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    # 使用中文字体
    # 优先使用注册的字体，其次使用 ReportLab 内置的 CJK 字体
    font_name = 'ChineseFont' if chinese_font_registered else 'STSong-Light'
    bold_font_name = 'ChineseFontBold' if chinese_font_registered else 'STHeiti-Regular'

    # 样式定义
    title_style = ParagraphStyle('Hometitle', parent=styles['Title'],
        fontSize=20, spaceAfter=16, alignment=TA_CENTER,
        textColor=colors.HexColor('#1a1a2e'), leading=26,
        fontName=font_name)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
        fontSize=11, spaceAfter=6, alignment=TA_CENTER,
        textColor=colors.HexColor('#666666'),
        fontName=font_name)
    section_style = ParagraphStyle('Section', parent=styles['Normal'],
        fontSize=12, spaceAfter=8, spaceBefore=16,
        textColor=colors.HexColor('#1a1a2e'),
        fontName=bold_font_name)
    q_style = ParagraphStyle('Question', parent=styles['Normal'],
        fontSize=11, spaceAfter=6, leading=18,
        textColor=colors.HexColor('#1a1a1a'),
        fontName=font_name)
    opt_style = ParagraphStyle('Option', parent=styles['Normal'],
        fontSize=10, spaceAfter=3, leftIndent=24, leading=15,
        textColor=colors.HexColor('#333333'),
        fontName=font_name)
    ans_label_style = ParagraphStyle('AnsLabel', parent=styles['Normal'],
        fontSize=11, spaceAfter=4, spaceBefore=10,
        textColor=colors.HexColor('#0070C0'),
        fontName=bold_font_name)
    ans_style = ParagraphStyle('Answer', parent=styles['Normal'],
        fontSize=10, spaceAfter=6, leftIndent=24, leading=15,
        textColor=colors.HexColor('#333333'),
        fontName=font_name)
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
        fontSize=9, alignment=TA_CENTER,
        textColor=colors.HexColor('#999999'),
        fontName=font_name)

    difficulty_labels = {"easy": "基础", "medium": "中等", "hard": "拓展", "mixed": "综合"}
    diff_text = difficulty_labels.get(difficulty, difficulty)

    elements = []

    # 封面标题
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(f"课程：{course}　　难度：{diff_text}　　题数：{len(questions)}", subtitle_style))

    if created_by:
        elements.append(Paragraph(f"出题人：{created_by}", subtitle_style))

    elements.append(Spacer(1, 0.3*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
    elements.append(Spacer(1, 0.3*cm))

    # 注意事项（必须指定中文字体；继承 Normal 会得到 Helvetica，中文会显示为灰色方框）
    notice_style = ParagraphStyle('Notice', parent=styles['Normal'],
        fontSize=9, spaceAfter=12, leading=14,
        textColor=colors.HexColor('#888888'),
        fontName=font_name)
    elements.append(Paragraph(
        "【注意事项】请认真阅读题目，独立完成。简答题和编程题请写出完整过程或代码。",
        notice_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
    elements.append(Spacer(1, 0.5*cm))

    # 按题型分组
    type_order = ["choice", "blank", "short_answer", "coding"]
    type_names = {
        "choice": "一、选择题",
        "blank": "二、填空题",
        "short_answer": "三、简答题",
        "coding": "四、编程题"
    }

    grouped: Dict[str, List] = {t: [] for t in type_order if t in [q.get("type") for q in questions]}
    for q in questions:
        t = q.get("type", "choice")
        grouped[t].append(q)

    answer_elements = []
    q_number = 1

    for qtype in type_order:
        qs = grouped.get(qtype, [])
        if not qs:
            continue

        elements.append(Paragraph(type_names.get(qtype, qtype), section_style))

        for qi, q in enumerate(qs):
            question_text = q.get("question", "")
            options = q.get("options", [])
            answer = q.get("answer", "")
            explanation = q.get("explanation", "")
            knowledge = q.get("knowledge_point", "")

            # 题目
            if qtype == "choice":
                q_text = f"<b>{q_number}.</b> {question_text}"
                elements.append(Paragraph(q_text, q_style))
                for oi, opt in enumerate(options):
                    label = chr(65 + oi)  # A, B, C, D
                    elements.append(Paragraph(f"　{label}. {opt}", opt_style))
            elif qtype == "blank":
                q_text = f"<b>{q_number}.</b> {question_text}"
                elements.append(Paragraph(q_text, q_style))
                elements.append(Paragraph("　________________________", opt_style))
            else:
                q_text = f"<b>{q_number}.</b> {question_text}"
                elements.append(Paragraph(q_text, q_style))
                if qtype == "coding":
                    elements.append(Paragraph("　", q_style))
                    for _ in range(3):
                        elements.append(Paragraph("_" * 60, opt_style))

            if knowledge:
                elements.append(Paragraph(
                    f"<font color='#888888' size='9'>【知识点】{knowledge}</font>",
                    opt_style))

            elements.append(Spacer(1, 0.2*cm))

            # 收集答案
            if include_answers and answer:
                answer_elements.append({
                    "number": q_number,
                    "type": qtype,
                    "answer": answer,
                    "explanation": explanation
                })

            q_number += 1

        elements.append(Spacer(1, 0.3*cm))

    # ===== 答案区 =====
    if include_answers and answer_elements:
        elements.append(PageBreak())
        elements.append(Paragraph("参考答案", title_style))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
        elements.append(Spacer(1, 0.3*cm))

        ans_sec_style = ParagraphStyle('AnsSection', parent=styles['Normal'],
            fontSize=12, spaceAfter=6, spaceBefore=12,
            textColor=colors.HexColor('#1a1a2e'), fontName='Helvetica-Bold')

        for ae in answer_elements:
            num = ae["number"]
            ans = ae["answer"]
            exp = ae.get("explanation", "")
            t = ae["type"]
            tname = {"choice": "选择", "blank": "填空", "short_answer": "简答", "coding": "编程"}.get(t, t)

            elements.append(Paragraph(f"{num}. [{tname}] {ans}", ans_style))
            if exp:
                elements.append(Paragraph(
                    f"<font color='#0070C0'>解析：{exp}</font>",
                    ans_style))
            elements.append(Spacer(1, 0.15*cm))

    # 页脚
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(
        f"— AI 作业生成平台 · {datetime.now().strftime('%Y-%m-%d')} —",
        footer_style))

    doc.build(elements)
    return buffer.getvalue()


# ==================== AI 生成作业题目 ====================
async def generate_questions_with_ai(
    course_id: str,
    count: int,
    question_types: List[str],
    difficulty: str,
    knowledge_content: str
) -> List[Dict]:
    """
    调用大模型（Kimi）生成作业题目。
    结合知识库内容生成针对性作业。
    """
    from common.integration.kimi import kimi_client

    difficulty_desc = {
        "easy": "基础知识为主，侧重概念辨析",
        "medium": "中等难度，综合性题目",
        "hard": "高难度，拓展性题目",
        "mixed": "难易混合"
    }.get(difficulty, "中等难度")

    type_prompts = {
        "choice": "选择题（4个选项，单选）",
        "blank": "填空题",
        "short_answer": "简答题（3-5句话）",
        "coding": "编程题（Python/Java）"
    }

    types_desc = "、".join([type_prompts.get(t, t) for t in question_types])

    system_prompt = (
        "你是一位专业的课程教师，擅长根据知识库内容设计高质量作业题目。\n"
        "你的职责是严格根据提供的知识内容生成作业题目，不要编造超出知识库范围的内容。\n"
        "请严格按照以下 JSON 格式输出，不要包含任何其他文字：\n"
        "{\n"
        '  "questions": [\n'
        '    {\n'
        '      "type": "<choice|blank|short_answer|coding>",\n'
        '      "question": "<题目内容>",\n'
        '      "options": ["<A选项>", "<B选项>", "<C选项>", "<D选项>"],  // 仅选择题需要\n'
        '      "answer": "<参考答案>",\n'
        '      "explanation": "<答案解析，可选>",\n'
        '      "difficulty": "<easy|medium|hard>",\n'
        '      "knowledge_point": "<对应知识点名称>\n'
        '    }\n'
        '  ]\n'
        "}"
    )

    # 控制每种题型的数量
    per_type = max(1, count // len(question_types))
    type_count_str = "\n".join([
        f"- {type_prompts.get(t, t)}: 约 {per_type} 道"
        for t in question_types
    ])

    user_prompt = f"""请根据以下知识库内容，设计 {count} 道作业题。
难度要求：{difficulty_desc}
题型分布（总数约 {count} 道）：
{type_count_str}

---
知识库内容：
{knowledge_content[:8000]}
---

请确保：
1. 题目内容真实来源于上述知识库，不要编造
2. 选择题答案唯一，选项有区分度
3. 编程题给出清晰的输入输出示例
4. 每道题标注对应知识点
5. 答案准确，解析清晰
"""

    try:
        result = await kimi_client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=8192
        )

        # 检查返回结果
        if result.get("error"):
            import logging
            logging.error(f"Kimi API 调用失败: {result.get('error')}, detail: {result.get('detail')}")
            return []

        raw_content = ""
        if "choices" in result and len(result["choices"]) > 0:
            raw_content = result["choices"][0]["message"]["content"]
        elif "content" in result:
            raw_content = result["content"]

        if not raw_content:
            import logging
            logging.error("Kimi API 返回内容为空")
            return []

        # 提取 JSON
        json_str = raw_content.strip()
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            json_str = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        parsed = json.loads(json_str)
        questions = parsed.get("questions", [])
        return questions[:count]

    except json.JSONDecodeError as e:
        import logging
        logging.error(f"JSON 解析失败: {e}, 原始内容: {raw_content[:500] if raw_content else 'empty'}")
        return []
    except Exception as e:
        import logging
        import traceback
        logging.error(f"AI 生成题目异常: {e}")
        traceback.print_exc()
        return []


# ==================== API 端点 ====================

@router.post("/generate", response_model=ResponseModel)
async def generate_homework(request: HomeworkGenRequest):
    """
    生成作业：结合知识库内容调用大模型生成作业题目，输出 PDF 文件。
    """
    _ensure_lazy_refs()

    import logging
    logger = logging.getLogger(__name__)

    try:
        # 1. 标题
        title = request.title or f"{request.course_id} 作业练习"

        # 2. 获取知识库内容（不强制要求有内容）
        knowledge_content = await fetch_knowledge_content(
            request.course_id, request.knowledge_point_ids
        )

        if not knowledge_content.strip():
            # 使用通用知识提示，让AI自由发挥
            knowledge_content = f"这是一份关于 {request.course_id or '通用学科'} 的作业练习。请根据常见的学科知识生成合适的题目。"

        # 3. 调用 AI 生成题目
        questions = await generate_questions_with_ai(
            course_id=request.course_id,
            count=request.question_count,
            question_types=request.question_types,
            difficulty=request.difficulty,
            knowledge_content=knowledge_content
        )

        if not questions:
            return ResponseModel(
                code=400,
                message="AI 生成题目失败，请检查知识库是否有足够的知识内容，或稍后重试",
                data=None
            )

        # 4. 生成 PDF
        homework_id = f"hw_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
        filename = f"{title}.pdf"

        pdf_bytes = generate_homework_pdf(
            title=title,
            course=request.course_id,
            questions=questions,
            difficulty=request.difficulty,
            include_answers=request.include_answers,
            created_by=request.created_by,
            homework_id=homework_id
        )

        # 5. 上传 MinIO
        object_name = f"generated/{request.course_id}/{homework_id}/{filename}"
        file_url = None

        try:
            client = get_minio_client()
            ensure_bucket(client, BUCKET_GENERATED)
            client.put_object(
                BUCKET_GENERATED, object_name,
                io.BytesIO(pdf_bytes),
                length=len(pdf_bytes),
                content_type="application/pdf"
            )
            file_url = f"http://{settings.MINIO_ENDPOINT}/{BUCKET_GENERATED}/{object_name}"
        except Exception as e:
            logger.warning(f"MinIO 上传失败: {e}")

        # 6. 保存记录
        async with AsyncSessionLocal() as session:
            gh = GeneratedHomework(
                homework_id=homework_id,
                title=title,
                course=request.course_id,
                course_id=request.course_id,
                source_type="knowledge_base",
                file_url=file_url,
                file_size=len(pdf_bytes),
                file_key=object_name,
                question_count=len(questions),
                difficulty=request.difficulty,
                status="completed",
                created_by=request.created_by,
                generation_params={
                    "question_count": request.question_count,
                    "question_types": request.question_types,
                    "include_answers": request.include_answers,
                    "knowledge_point_ids": request.knowledge_point_ids
                }
            )
            session.add(gh)
            await session.commit()

        return ResponseModel(
            code=200,
            message="作业生成成功",
            data={
                "homework_id": homework_id,
                "title": title,
                "course": request.course_id,
                "question_count": len(questions),
                "file_url": file_url,
                "file_size": len(pdf_bytes),
                "status": "completed",
                "preview_questions": questions[:3]
            }
        )

    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"缺少依赖: {str(e)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/download/{homework_id}", tags=["Homework Generator"])
async def download_generated_homework(homework_id: str):
    """
    下载生成的作业 PDF 文件。
    """
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(GeneratedHomework).where(GeneratedHomework.homework_id == homework_id)
        )
        gh = result.scalar_one_or_none()

        if not gh or not gh.file_key:
            raise HTTPException(status_code=404, detail="作业文件不存在")

        if not gh.file_url:
            raise HTTPException(status_code=404, detail="文件未上传到存储")

        # 直接从 MinIO 流式传输文件，避免跨域问题
        try:
            client = get_minio_client()
            response = client.get_object(BUCKET_GENERATED, gh.file_key)
            file_content = response.read()
            response.close()
            response.release_conn()

            filename = f"{gh.title}.pdf"
            # 编码文件名以支持中文
            from starlette.responses import Response
            from urllib.parse import quote

            headers = {
                'Content-Disposition': f'attachment; filename="{quote(filename)}"; filename*=UTF-8\'\'{quote(filename)}',
                'Content-Type': 'application/pdf',
            }
            return Response(
                content=file_content,
                media_type='application/pdf',
                headers=headers
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取文件失败: {e}")


@router.delete("/{homework_id}", tags=["Homework Generator"])
async def delete_generated_homework(homework_id: str):
    """
    删除已生成的作业。
    """
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(GeneratedHomework).where(GeneratedHomework.homework_id == homework_id)
        )
        gh = result.scalar_one_or_none()

        if not gh:
            raise HTTPException(status_code=404, detail="作业不存在")

        # 从 MinIO 删除文件
        if gh.file_key:
            try:
                client = get_minio_client()
                client.remove_object(BUCKET_GENERATED, gh.file_key)
            except Exception as e:
                print(f"删除 MinIO 文件失败: {e}")

        # 从数据库删除记录
        await session.delete(gh)
        await session.commit()

        return ResponseModel(code=200, message="删除成功")


@router.get("/list", response_model=ResponseModel)
async def list_generated_homework(
    course_id: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """获取已生成的作业列表"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func
        query = select(GeneratedHomework)
        count_q = select(func.count(GeneratedHomework.id))

        if course_id:
            query = query.where(GeneratedHomework.course_id == course_id)
            count_q = count_q.where(GeneratedHomework.course_id == course_id)

        total_result = await session.execute(count_q)
        total = total_result.scalar() or 0

        query = query.order_by(GeneratedHomework.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await session.execute(query)
        rows = result.scalars().all()

        items = [{
            "homework_id": r.homework_id,
            "title": r.title,
            "course": r.course,
            "course_id": r.course_id,
            "question_count": r.question_count,
            "difficulty": r.difficulty,
            "file_url": r.file_url,
            "file_size": r.file_size,
            "status": r.status,
            "created_by": r.created_by,
            "created_at": r.created_at.isoformat() if r.created_at else None
        } for r in rows]

        return ResponseModel(
            code=200, message="success",
            data={"items": items, "total": total, "page": page, "page_size": page_size}
        )


@router.get("/courses", response_model=ResponseModel)
async def list_available_courses():
    """
    获取可选的课程/知识库列表（用于前端下拉选择）。
    """
    _ensure_lazy_refs()

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func, text
        try:
            # 尝试从知识点表获取课程列表
            result = await session.execute(
                select(KnowledgePoint.course_id, func.count(KnowledgePoint.id).label("count"))
                .group_by(KnowledgePoint.course_id)
                .order_by(func.count(KnowledgePoint.id).desc())
            )
            courses = [{"course_id": r[0], "point_count": r[1]} for r in result.all()]
            return ResponseModel(code=200, message="success", data={"courses": courses})
        except Exception:
            return ResponseModel(code=200, message="success", data={"courses": []})


@router.get("/detail/{homework_id}", response_model=ResponseModel)
async def get_generated_homework_detail(homework_id: str):
    """获取生成作业的详细信息（含预览题目）"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(GeneratedHomework).where(GeneratedHomework.homework_id == homework_id)
        )
        gh = result.scalar_one_or_none()

        if not gh:
            raise HTTPException(status_code=404, detail="作业不存在")

        return ResponseModel(
            code=200, message="success",
            data={
                "homework_id": gh.homework_id,
                "title": gh.title,
                "course": gh.course,
                "course_id": gh.course_id,
                "question_count": gh.question_count,
                "difficulty": gh.difficulty,
                "file_url": gh.file_url,
                "file_size": gh.file_size,
                "status": gh.status,
                "created_by": gh.created_by,
                "created_at": gh.created_at.isoformat() if gh.created_at else None,
                "generation_params": gh.generation_params
            }
        )
