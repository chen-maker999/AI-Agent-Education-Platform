"""
文档质量过滤器

过滤低质量文档切片（如纯图片说明、无意义内容等）
"""

import re
from typing import List, Dict, Tuple


class DocumentQualityFilter:
    """文档质量过滤器"""
    
    # 低质量内容模式
    LOW_QUALITY_PATTERNS = [
        # 图片说明
        (r'Figure\s+\d+\.?\d*:?\.?\s*(Screenshot|of|©)', 'figure_caption'),
        (r'Screenshot\s+of', 'screenshot'),
        (r'©\s*(Oracle|Microsoft|Google|Apple)', 'copyright'),
        
        # 纯引用/版权信息
        (r'^\s*All\s+rights\s+reserved', 'copyright'),
        (r'^\s*Copyright\s+©', 'copyright'),
        
        # 无意义内容
        (r'^\s*[A-Z]\s*$', 'single_letter'),  # 单个大写字母
        (r'^\s*\d+\s*$', 'single_number'),   # 单个数字
        
        # 纯代码片段（无注释）
        (r'^\s*[}\{]\s*$', 'bracket_only'),
        (r'^\s*;\s*$', 'semicolon_only'),
    ]
    
    # 高质量内容模式
    HIGH_QUALITY_PATTERNS = [
        # 包含代码示例
        r'(public|private|protected)\s+(static\s+)?(void|int|String|boolean|double)',
        r'@(Override|Deprecated|SuppressWarnings)',
        r'(class|interface|enum)\s+\w+',
        r'(import|package)\s+[\w.]+',
        
        # 包含解释性文本
        r'(means|refers to|is a|represents|defines)',
        r'(例如 | 比如 | 是指 | 表示)',
    ]
    
    def __init__(self):
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), label)
            for pattern, label in self.LOW_QUALITY_PATTERNS
        ]
        self.high_quality_compiled = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.HIGH_QUALITY_PATTERNS
        ]
    
    def is_low_quality(self, content: str) -> Tuple[bool, str]:
        """
        检查文档是否为低质量
        
        Returns:
            (is_low_quality, reason)
        """
        content = content.strip()
        
        # 太短的文档
        if len(content) < 20:
            return True, "too_short"
        
        # 检查低质量模式
        for pattern, label in self.compiled_patterns:
            if pattern.search(content):
                return True, label
        
        # 检查是否主要是代码（无解释）
        lines = content.split('\n')
        code_lines = 0
        text_lines = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 代码特征
            if re.match(r'^\s*(public|private|protected|static|void|int|String|class|interface|import|package)', line):
                code_lines += 1
            # 文本特征
            elif re.search(r'[\u4e00-\u9fa5]|[a-zA-Z]{3,}\s+(is|are|means|refers)', line):
                text_lines += 1
        
        # 如果 90% 以上是代码，认为是低质量（缺少解释）
        total_lines = code_lines + text_lines
        if total_lines > 3 and code_lines / total_lines > 0.9:
            return True, "code_only"
        
        return False, ""
    
    def is_high_quality(self, content: str) -> bool:
        """检查文档是否为高质量"""
        content = content.strip()
        
        # 检查高质量模式
        for pattern in self.high_quality_compiled:
            if pattern.search(content):
                return True
        
        return False
    
    def quality_score(self, content: str) -> float:
        """
        计算文档质量分数 (0.0 - 1.0)
        """
        content = content.strip()
        score = 0.5  # 基础分数
        
        # 长度评分
        if len(content) > 200:
            score += 0.1
        if len(content) > 500:
            score += 0.1
        
        # 低质量惩罚
        is_low, reason = self.is_low_quality(content)
        if is_low:
            score -= 0.4
        
        # 高质量奖励
        if self.is_high_quality(content):
            score += 0.2
        
        # 代码 - 文本混合评分
        lines = content.split('\n')
        has_code = any(re.match(r'\s*(public|private|protected|class|interface)', line) for line in lines)
        has_text = any(re.search(r'[\u4e00-\u9fa5]|[a-zA-Z]{3,}\s+(is|are|means)', line) for line in lines)
        
        if has_code and has_text:
            score += 0.1  # 代码和解释都有，加分
        
        return max(0.0, min(1.0, score))
    
    def filter_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        过滤文档列表
        
        Args:
            documents: 文档列表，每个文档包含 'content' 字段
            
        Returns:
            过滤后的文档列表
        """
        filtered = []
        
        for doc in documents:
            content = doc.get('content', '')
            is_low, reason = self.is_low_quality(content)
            
            if not is_low:
                filtered.append(doc)
        
        return filtered
    
    def rank_documents(self, documents: List[Dict]) -> List[Tuple[Dict, float]]:
        """
        对文档进行质量排序
        
        Returns:
            (文档，质量分数) 的列表，按分数降序排列
        """
        scored = []
        
        for doc in documents:
            content = doc.get('content', '')
            score = self.quality_score(content)
            scored.append((doc, score))
        
        # 按分数降序排序
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored


# 全局实例
_filter = DocumentQualityFilter()


def is_low_quality(content: str) -> bool:
    """检查文档是否为低质量（便捷函数）"""
    is_low, _ = _filter.is_low_quality(content)
    return is_low


def quality_score(content: str) -> float:
    """计算文档质量分数（便捷函数）"""
    return _filter.quality_score(content)


def filter_documents(documents: List[Dict]) -> List[Dict]:
    """过滤文档列表（便捷函数）"""
    return _filter.filter_documents(documents)
