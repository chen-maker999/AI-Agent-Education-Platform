"""
智能答案生成器 - 不使用 LLM

基于检索结果的智能答案组织：
1. 提取关键段落
2. 去重和合并
3. 结构化呈现
4. 添加来源引用
"""

import re
from typing import List, Dict, Any, Tuple
from collections import Counter


class SmartAnswerGenerator:
    """智能答案生成器"""

    def __init__(self):
        self.max_answer_length = 1500
        self.min_sentence_length = 20
        self.max_sentence_length = 200

    def generate_answer(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        top_k: int = 5
    ) -> Tuple[str, List[Dict]]:
        """
        基于检索结果生成结构化答案

        Args:
            query: 用户问题
            retrieved_docs: 检索到的文档列表
            top_k: 使用的文档数量

        Returns:
            (答案文本，来源列表)
        """
        if not retrieved_docs:
            return self._generate_no_answer(query), []

        # 1. 提取关键句子
        key_sentences = self._extract_key_sentences(query, retrieved_docs, top_k)

        # 2. 去重和排序
        unique_sentences = self._deduplicate_sentences(key_sentences)

        # 3. 组织答案结构
        answer = self._organize_answer(query, unique_sentences, retrieved_docs)

        # 4. 准备来源
        sources = self._prepare_sources(retrieved_docs[:top_k])

        return answer, sources

    def _extract_key_sentences(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        top_k: int
    ) -> List[Tuple[str, str, float]]:
        """
        从文档中提取关键句子

        Returns:
            [(句子，doc_id, 相关性分数), ...]
        """
        # 提取查询关键词
        query_keywords = self._extract_keywords(query)

        key_sentences = []

        for doc in docs[:top_k]:
            content = doc.get("content", "")
            doc_id = doc.get("doc_id", "")
            score = doc.get("final_score", doc.get("score", 1.0))

            # 分割成句子
            sentences = self._split_into_sentences(content)

            for sentence in sentences:
                # 计算句子与查询的相关性
                relevance = self._calculate_sentence_relevance(
                    sentence, query_keywords, score
                )

                if relevance > 0.05:  # 降低阈值，捕获更多内容
                    key_sentences.append((sentence, doc_id, relevance))

        # 按相关性排序
        key_sentences.sort(key=lambda x: x[2], reverse=True)

        return key_sentences

    def _calculate_sentence_relevance(
        self,
        sentence: str,
        query_keywords: List[str],
        doc_score: float
    ) -> float:
        """计算句子与查询的相关性"""
        if not query_keywords:
            return doc_score * 0.5

        sentence_lower = sentence.lower()
        
        # 精确匹配（关键词完整出现在句子中）
        exact_matches = sum(
            1 for kw in query_keywords
            if kw.lower() in sentence_lower
        )
        
        # 部分匹配（词的字符级别重叠）
        sentence_words = set(self._tokenize(sentence_lower))
        partial_matches = sum(
            1 for kw in query_keywords
            if any(kw.lower() in sw or sw in kw.lower() for sw in sentence_words)
        )

        # 组合匹配率：精确匹配 (70%) + 部分匹配 (30%)
        match_rate = (0.7 * exact_matches + 0.3 * partial_matches) / len(query_keywords)

        # 组合分数：关键词匹配 (60%) + 文档分数 (40%)
        relevance = (match_rate * 0.6 + doc_score * 0.4)

        # 长度奖励：适中长度的句子得分更高
        sent_len = len(sentence)
        if 30 <= sent_len <= 150:
            relevance *= 1.1  # 奖励适中长度
        elif sent_len > 200:
            relevance *= 0.9  # 惩罚过长句子

        return relevance

    def _deduplicate_sentences(
        self,
        sentences: List[Tuple[str, str, float]],
        similarity_threshold: float = 0.7
    ) -> List[Tuple[str, str, float]]:
        """去重句子（基于 Jaccard 相似度）"""
        if not sentences:
            return []

        unique = []
        seen_hashes = set()

        for sentence, doc_id, relevance in sentences:
            # 使用词袋哈希进行快速去重
            words = set(self._tokenize(sentence.lower()))
            sentence_hash = hash(frozenset(words))

            if sentence_hash not in seen_hashes:
                seen_hashes.add(sentence_hash)
                unique.append((sentence, doc_id, relevance))

        return unique

    def _organize_answer(
        self,
        query: str,
        sentences: List[Tuple[str, str, float]],
        docs: List[Dict[str, Any]]
    ) -> str:
        """组织答案结构"""
        if not sentences:
            return self._generate_no_answer(query)

        # 选择最相关的句子（最多 5 个）
        top_sentences = sentences[:5]

        # 构建答案
        answer_parts = []

        # 开头：直接回答（最相关的句子）
        if top_sentences:
            best_sentence = top_sentences[0][0]
            # 确保开头句子完整表达意思
            if not best_sentence[0].isupper() and not self._is_chinese_char(best_sentence[0]):
                best_sentence = best_sentence[0].upper() + best_sentence[1:]
            answer_parts.append(best_sentence)

        # 主体：补充信息（按相关性排序）
        if len(top_sentences) > 1:
            additional_info = []
            for sent, doc_id, rel in top_sentences[1:]:
                # 避免与第一个句子重复
                if self._jaccard_similarity(sent, top_sentences[0][0]) < 0.5:
                    additional_info.append(sent)
            
            # 用换行分隔补充信息
            if additional_info:
                answer_parts.extend(additional_info[:3])  # 最多 3 个补充

        # 合并答案
        answer = "\n\n".join(answer_parts)

        # 添加来源标记
        unique_docs = len(set(doc_id for _, doc_id, _ in top_sentences))
        answer += "\n\n---\n**参考资料**: 共 {} 个文档".format(unique_docs)

        # 长度控制
        if len(answer) > self.max_answer_length:
            answer = answer[:self.max_answer_length - 50] + "..."

        return answer

    def _is_chinese_char(self, char: str) -> bool:
        """判断是否为中文字符"""
        return '\u4e00' <= char <= '\u9fff'

    def _jaccard_similarity(self, s1: str, s2: str) -> float:
        """计算两个句子的 Jaccard 相似度"""
        set1 = set(self._tokenize(s1.lower()))
        set2 = set(self._tokenize(s2.lower()))
        
        if not set1 or not set2:
            return 0.0
        
        intersection = set1 & set2
        union = set1 | set2
        
        return len(intersection) / len(union) if union else 0.0

    def _generate_no_answer(self, query: str) -> str:
        """无法回答时的回复"""
        return f"抱歉，当前知识库中未找到与\"{query}\"直接相关的内容。建议：\n1. 尝试使用不同的关键词\n2. 检查问题描述是否清晰\n3. 联系教师获取帮助"

    def _prepare_sources(self, docs: List[Dict[str, Any]]) -> List[Dict]:
        """准备来源列表"""
        sources = []
        seen_doc_ids = set()
        
        for i, doc in enumerate(docs):
            doc_id = doc.get("doc_id", "")
            
            # 去重
            if doc_id in seen_doc_ids:
                continue
            seen_doc_ids.add(doc_id)
            
            source = {
                "doc_id": doc_id,
                "content": doc.get("content", "")[:500],  # 增加内容长度
                "score": doc.get("final_score", doc.get("score", 0)),
                "metadata": doc.get("metadata", {}) or {},
                "course_id": doc.get("course_id", ""),
                "channel": doc.get("channel", "keyword"),
                "final_score": doc.get("final_score", 0),
                "channels": doc.get("channels", ["keyword"])
            }
            sources.append(source)
        return sources

    # ==================== 辅助方法 ====================

    def _tokenize(self, text: str) -> List[str]:
        """简单的中文分词（按字符和词）"""
        # 移除标点
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        # 按空格和字符分割
        words = text.split()
        return words if words else list(text)

    def _extract_keywords(self, query: str) -> List[str]:
        """提取查询关键词"""
        # 移除常见停用词
        stopwords = {
            '的', '了', '是', '在', '和', '与', '及', '等', '个', '什么',
            '如何', '怎么', '怎样', '为什么', '哪些', '哪个', '请', '说明',
            '介绍', '一下', '请', '问', '呢', '吗', '？', '?', '。', '，'
        }

        words = self._tokenize(query)
        keywords = [w for w in words if w not in stopwords and len(w) > 0]

        return keywords

    def _split_into_sentences(self, text: str) -> List[str]:
        """将文本分割成句子"""
        # 按句号、问号、感叹号、换行分割
        sentences = re.split(r'[。！？!?;\n]', text)
        # 过滤空句子和过短的句子
        sentences = [
            s.strip() for s in sentences
            if s.strip() and len(s.strip()) >= self.min_sentence_length
        ]
        return sentences

    def _calculate_sentence_relevance(
        self,
        sentence: str,
        query_keywords: List[str],
        doc_score: float
    ) -> float:
        """计算句子与查询的相关性"""
        if not query_keywords:
            return doc_score * 0.5

        sentence_words = set(self._tokenize(sentence.lower()))

        # 关键词匹配率
        matched_keywords = sum(
            1 for kw in query_keywords
            if kw.lower() in sentence_words or kw in sentence
        )

        keyword_match_rate = matched_keywords / len(query_keywords) if query_keywords else 0

        # 组合分数：关键词匹配 (60%) + 文档分数 (40%)
        relevance = (keyword_match_rate * 0.6 + doc_score * 0.4)

        return relevance


# 全局实例
answer_generator = SmartAnswerGenerator()


async def generate_smart_answer(
    query: str,
    retrieved_docs: List[Dict[str, Any]],
    top_k: int = 5
) -> Tuple[str, List[Dict]]:
    """生成智能答案的主函数"""
    return answer_generator.generate_answer(query, retrieved_docs, top_k)
