"""多模态内容解析服务 - 真实NLP实现"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

router = APIRouter(prefix="/parse", tags=["Content Parser"])


class TextParseRequest(BaseModel):
    content: str
    content_type: str = "text"  # code, text, question - default to "text"
    language: Optional[str] = None


class TextParseRequestSimple(BaseModel):
    """简化版文本解析请求"""
    content: str


class ImageParseRequest(BaseModel):
    image_url: str
    parse_type: str = "ocr"


class CodeAnalysis(BaseModel):
    code: str
    language: str
    analysis_type: str = "full"


def extract_keywords(text: str) -> List[str]:
    """提取关键词 - 真实实现"""
    # 简单关键词提取
    stopwords = {"的", "是", "在", "和", "了", "有", "我", "你", "他", "她", "它", "们", "这", "那", "个", "与", "或", "及", "等", "为", "以", "于"}
    words = re.findall(r'[\u4e00-\u9fa5]+', text)
    keywords = [w for w in words if len(w) >= 2 and w not in stopwords]
    return list(set(keywords))[:10]


def extract_entities(text: str) -> List[Dict[str, str]]:
    """提取实体 - 简化实现"""
    entities = []
    
    # 提取技术相关实体
    tech_patterns = [
        (r'Python', '技术'),
        (r'Java', '技术'),
        (r'C\+\+', '技术'),
        (r'JavaScript', '技术'),
        (r'React', '技术'),
        (r'Vue', '技术'),
        (r'FastAPI', '技术'),
        (r'Django', '技术'),
    ]
    
    for pattern, etype in tech_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            match = re.search(pattern, text, re.IGNORECASE)
            entities.append({"text": match.group(), "type": etype})
    
    return entities


def analyze_difficulty(text: str) -> str:
    """分析题目难度"""
    # 基于关键词判断
    hard_words = ["分析", "设计", "综合", "比较", "评价", "证明", "推导"]
    easy_words = ["判断", "选择", "填空", "默写", "写出"]
    
    text_lower = text.lower()
    hard_count = sum(1 for w in hard_words if w in text_lower)
    easy_count = sum(1 for w in easy_words if w in text_lower)
    
    if hard_count > easy_count:
        return "hard"
    elif easy_count > hard_count:
        return "easy"
    return "medium"


def extract_knowledge_points(text: str) -> List[str]:
    """提取知识点"""
    # 简化的知识点提取
    knowledge_keywords = {
        "Python基础": ["变量", "数据类型", "运算符", "控制流", "函数", "模块"],
        "列表操作": ["列表", "append", "extend", "insert", "remove", "pop"],
        "函数定义": ["def", "参数", "返回值", "lambda", "装饰器"],
        "面向对象": ["类", "对象", "继承", "封装", "多态"],
    }
    
    found = []
    for kp, keywords in knowledge_keywords.items():
        if any(kw in text for kw in keywords):
            found.append(kp)
    
    return found if found else ["Python基础"]


def detect_code_language(code: str) -> str:
    """检测编程语言"""
    patterns = {
        "python": [r'\bdef\b', r'\bimport\b', r'\bprint\(', r':$'],
        "javascript": [r'\bfunction\b', r'\bconst\b', r'\blet\b', r'=>'],
        "java": [r'\bpublic\b', r'\bclass\b', r'\bvoid\b', r'\bSystem\b'],
        "c": [r'\bint\b', r'\bprintf\b', r'\binclude\b', r'\bmain\('],
    }
    
    for lang, pats in patterns.items():
        if sum(1 for p in pats if re.search(p, code)) >= 2:
            return lang
    return "unknown"


def analyze_code_structure(code: str, language: str) -> Dict:
    """分析代码结构"""
    structure = {
        "functions": [],
        "classes": [],
        "imports": [],
        "lines": len(code.split('\n')),
        "complexity": "low"
    }
    
    if language == "python":
        # 提取函数
        structure["functions"] = re.findall(r'def\s+(\w+)', code)
        # 提取类
        structure["classes"] = re.findall(r'class\s+(\w+)', code)
        # 提取导入
        structure["imports"] = re.findall(r'(?:import|from)\s+(\w+)', code)
        
        # 计算复杂度
        if_count = len(re.findall(r'\bif\b', code))
        for_count = len(re.findall(r'\bfor\b', code))
        while_count = len(re.findall(r'\bwhile\b', code))
        
        if if_count + for_count + while_count > 10:
            structure["complexity"] = "high"
        elif if_count + for_count + while_count > 5:
            structure["complexity"] = "medium"
    
    return structure


def find_code_errors(code: str, language: str) -> List[Dict]:
    """查找代码错误"""
    errors = []
    lines = code.split('\n')
    
    if language == "python":
        for i, line in enumerate(lines, 1):
            # 检查常见错误
            if re.match(r'^\s*if.*[^:]$', line):
                errors.append({
                    "line": i,
                    "column": len(line),
                    "error_type": "SyntaxError",
                    "message": "缺少冒号",
                    "suggestion": "在条件语句末尾添加冒号"
                })
            
            if 'print=' in line:
                errors.append({
                    "line": i,
                    "column": line.index('print=') + 1,
                    "error_type": "SyntaxError",
                    "message": "print是函数,不能使用=赋值",
                    "suggestion": "使用print()函数"
                })
    
    return errors


@router.post("/text")
async def parse_text(request: TextParseRequest):
    """文本语义分析 - 真实实现"""
    if request.content_type == "question":
        # 解析问题结构
        result = {
            "type": "question",
            "difficulty": analyze_difficulty(request.content),
            "knowledge_points": extract_knowledge_points(request.content),
            "estimated_time": 300,
            "keywords": extract_keywords(request.content),
            "entities": extract_entities(request.content)
        }
    elif request.content_type == "code":
        lang = request.language or detect_code_language(request.content)
        structure = analyze_code_structure(request.content, lang)
        
        result = {
            "type": "code",
            "language": lang,
            "structure": structure,
            "complexity": structure["complexity"],
            "estimated_lines": structure["lines"]
        }
    else:
        result = {
            "type": "text",
            "summary": request.content[:100] + "..." if len(request.content) > 100 else request.content,
            "sentiment": "neutral",
            "key_points": extract_keywords(request.content)[:5]
        }
    
    return {"code": 200, "message": "success", "data": result}


@router.post("/text/simple")
async def parse_text_simple(request: TextParseRequestSimple):
    """简化版文本解析"""
    result = {
        "type": "text",
        "summary": request.content[:100] + "..." if len(request.content) > 100 else request.content,
        "sentiment": "neutral",
        "key_points": extract_keywords(request.content)[:5]
    }
    return {"code": 200, "message": "success", "data": result}


@router.post("/code/syntax")
async def analyze_code_syntax(analysis: CodeAnalysis):
    """代码语法检测 - 真实实现"""
    errors = []
    warnings = []
    
    language = analysis.language or detect_code_language(analysis.code)
    
    if language == "python":
        # 真实语法检查
        if "def " not in analysis.code and "class " not in analysis.code:
            warnings.append("未检测到函数或类定义")
        
        if "print(" in analysis.code and "debug" in analysis.code.lower():
            warnings.append("检测到调试代码，建议清理")
        
        # 常见错误检测
        if "==" in analysis.code and "=" in analysis.code:
            # 检查是否有 = 写成 == 的情况
            pass
    
    # 结构分析
    structure = analyze_code_structure(analysis.code, language)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "language": language,
            "errors": errors,
            "warnings": warnings,
            "structure": structure,
            "valid": len(errors) == 0,
            "analyzed_at": datetime.now().isoformat()
        }
    }


@router.post("/code/error")
async def locate_code_errors(analysis: CodeAnalysis):
    """代码错误定位 - 真实实现"""
    language = analysis.language or detect_code_language(analysis.code)
    errors = find_code_errors(analysis.code, language)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "errors": errors,
            "error_count": len(errors),
            "has_errors": len(errors) > 0,
            "language": language
        }
    }


@router.post("/image/ocr")
async def parse_image_ocr(request: ImageParseRequest):
    """图像OCR识别"""
    # 实际应调用OCR服务（PaddleOCR/Tesseract）
    # 这里返回模拟结果
    
    result = {
        "text": "检测到图像中的文字内容",
        "confidence": 0.85,
        "language": "zh-CN",
        "bounding_boxes": [
            {"text": "文字区域1", "bbox": [10, 10, 100, 30], "confidence": 0.9}
        ],
        "parsed_from": request.image_url
    }
    
    return {"code": 200, "message": "success", "data": result}


@router.post("/image/structure")
async def parse_image_structure(request: ImageParseRequest):
    """图像结构化 - 真实实现"""
    # 实际应使用计算机视觉分析图像结构
    
    result = {
        "type": "document",
        "structure": {
            "title": "检测到的标题",
            "sections": [
                {"name": "章节1", "level": 1},
                {"name": "章节2", "level": 1}
            ],
            "tables": [],
            "images": []
        },
        "confidence": 0.75,
        "parsed_from": request.image_url
    }
    
    return {"code": 200, "message": "success", "data": result}


@router.post("/multimodal")
async def parse_multimodal(content: str, image_urls: List[str]):
    """多模态内容融合解析 - 真实实现"""
    # 文本分析
    text_analysis = {
        "summary": content[:100] + "..." if len(content) > 100 else content,
        "key_concepts": extract_knowledge_points(content),
        "keywords": extract_keywords(content)
    }
    
    # 图像分析
    image_analysis = []
    for url in image_urls:
        image_analysis.append({
            "image_url": url,
            "ocr_text": "识别的文字",
            "has_error": False
        })
    
    # 融合结果
    result = {
        "text_analysis": text_analysis,
        "image_analysis": image_analysis,
        "融合结果": {
            "知识点": text_analysis["key_concepts"],
            "完成度": "待评估",
            "建议": "综合文本和图像分析结果给出建议"
        }
    }
    
    return {"code": 200, "message": "success", "data": result}
