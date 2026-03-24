"""
动态库索引管理 - 实时计算 TF-IDF，支持增量更新

特性:
- 实时计算查询向量
- 增量更新文档向量
- 支持文档删除
- 自动晋升到静态库 (7 天无修改)
"""

import asyncio
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

logger = logging.getLogger("dynamic_index")


class DocumentData:
    """动态文档数据"""
    
    def __init__(self, doc_id: str, content: str, course_id: str, metadata: Dict = None):
        self.doc_id = doc_id
        self.content = content
        self.course_id = course_id or "default"
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.modified_at = datetime.now()
        self.access_count = 0
        self.last_accessed = None
        self.tfidf_vector: Optional[np.ndarray] = None
    
    def touch(self):
        """更新访问时间"""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def update_content(self, new_content: str):
        """更新内容"""
        self.content = new_content
        self.modified_at = datetime.now()
        self.tfidf_vector = None  # 清除向量，需要重新计算
    
    def is_stable(self, days: int = 7, min_access: int = 10) -> bool:
        """判断是否稳定 (可晋升到静态库)"""
        days_since_modified = (datetime.now() - self.modified_at).days
        return days_since_modified >= days and self.access_count >= min_access


class DynamicIndex:
    """
    动态文档索引
    
    用于存储频繁变更的文档（如用户上传、最新资料等）
    支持实时增删改操作
    """
    
    def __init__(self):
        # 文档存储
        self.documents: Dict[str, DocumentData] = {}  # doc_id -> DocumentData
        
        # 向量缓存
        self.tfidf_vectors: Dict[str, np.ndarray] = {}  # doc_id -> vector
        
        # 词表和 IDF
        self.vocabulary: Dict[str, int] = {}
        self.idf_values: Dict[str, float] = {}
        self.doc_count = 0
        self.vocab_size = 0
        
        # 课程 ID 索引
        self.course_id_map: Dict[str, List[str]] = defaultdict(list)  # course_id -> [doc_ids]
        
        # 配置
        self.promotion_days = 7  # 7 天无修改可晋升
        self.promotion_min_access = 10  # 最少访问次数
        
        # 更新锁
        self._lock = asyncio.Lock()
    
    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """计算词频 TF"""
        tf = {}
        total = len(tokens) if tokens else 1
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        for token in tf:
            tf[token] /= total
        return tf
    
    def _chinese_tokenize(self, text: str) -> List[str]:
        """使用 jieba 进行中文分词"""
        import jieba
        
        words = jieba.cut(text)
        stopwords = {
            '的', '是', '在', '和', '了', '有', '我', '你', '他', '她', '它', '们',
            '这', '那', '个', '与', '或', '及', '等', '为', '以', '于', '也', '就',
            '都', '而', '着', '一个', '没有', '我们', '你们', '可以', '进行', '使用'
        }
        return [w for w in words if w.strip() and len(w) > 1 and w not in stopwords]
    
    def _update_idf(self, tokens_list: List[List[str]]):
        """更新 IDF 值 (增量)"""
        import math
        
        # 统计文档频率
        df = {}
        for tokens in tokens_list:
            for token in set(tokens):
                df[token] = df.get(token, 0) + 1
        
        # 更新 IDF
        N = self.doc_count
        for token, freq in df.items():
            self.idf_values[token] = math.log((N + 1) / (freq + 1)) + 1
    
    def _compute_vector(self, text: str) -> np.ndarray:
        """计算 TF-IDF 向量"""
        tokens = self._chinese_tokenize(text)
        tf = self._compute_tf(tokens)
        
        # 动态扩展词表
        for token in tokens:
            if token not in self.vocabulary:
                self.vocabulary[token] = len(self.vocabulary)
        
        # 构建向量
        vector = np.zeros(len(self.vocabulary), dtype=np.float32)
        for token, tf_val in tf.items():
            idx = self.vocabulary[token]
            idf_val = self.idf_values.get(token, 1.0)
            vector[idx] = tf_val * idf_val
        
        # L2 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        添加文档到动态库
        
        Args:
            documents: 文档列表，每个包含 doc_id, content, course_id, metadata
        
        Returns:
            成功添加的文档数
        """
        async with self._lock:
            added_count = 0
            
            for doc_data in documents:
                doc_id = doc_data["doc_id"]
                content = doc_data["content"]
                course_id = doc_data.get("course_id", "default")
                metadata = doc_data.get("metadata", {})
                
                # 创建或更新文档
                if doc_id in self.documents:
                    # 更新现有文档
                    self.documents[doc_id].update_content(content)
                    self.documents[doc_id].course_id = course_id
                    self.documents[doc_id].metadata = metadata
                else:
                    # 新增文档
                    doc = DocumentData(doc_id, content, course_id, metadata)
                    self.documents[doc_id] = doc
                    self.course_id_map[course_id].append(doc_id)
                    self.doc_count += 1
                
                # 计算向量
                vector = self._compute_vector(content)
                self.tfidf_vectors[doc_id] = vector
                doc.tfidf_vector = vector
                
                added_count += 1
            
            # 更新 IDF (使用所有文档)
            if added_count > 0:
                all_tokens = [self._chinese_tokenize(d.content) for d in self.documents.values()]
                self._update_idf(all_tokens)
                
                # 重新计算所有向量 (因为 IDF 变了)
                for doc_id, doc in self.documents.items():
                    doc.tfidf_vector = self._compute_vector(doc.content)
                    self.tfidf_vectors[doc_id] = doc.tfidf_vector
            
            self.vocab_size = len(self.vocabulary)
            
            logger.info(f"动态库添加文档：{added_count} 个，总计：{self.doc_count} 个")
            return added_count
    
    async def remove_documents(self, doc_ids: List[str]) -> int:
        """
        从动态库删除文档
        
        Args:
            doc_ids: 要删除的文档 ID 列表
        
        Returns:
            成功删除的文档数
        """
        async with self._lock:
            removed_count = 0
            
            for doc_id in doc_ids:
                if doc_id in self.documents:
                    doc = self.documents[doc_id]
                    course_id = doc.course_id
                    
                    # 从课程索引移除
                    if doc_id in self.course_id_map[course_id]:
                        self.course_id_map[course_id].remove(doc_id)
                    
                    # 删除文档和向量
                    del self.documents[doc_id]
                    if doc_id in self.tfidf_vectors:
                        del self.tfidf_vectors[doc_id]
                    
                    self.doc_count -= 1
                    removed_count += 1
            
            # 更新 IDF
            if removed_count > 0 and self.doc_count > 0:
                all_tokens = [self._chinese_tokenize(d.content) for d in self.documents.values()]
                self._update_idf(all_tokens)
                
                # 重新计算所有向量
                for doc_id, doc in self.documents.items():
                    doc.tfidf_vector = self._compute_vector(doc.content)
                    self.tfidf_vectors[doc_id] = doc.tfidf_vector
            
            logger.info(f"动态库删除文档：{removed_count} 个，剩余：{self.doc_count} 个")
            return removed_count
    
    async def search(self, 
                     query: str,
                     top_k: int = 10,
                     course_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        实时检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数
            course_id: 课程 ID 过滤 (可选)
        
        Returns:
            (结果列表，统计信息)
        """
        start_time = datetime.now()
        stats = {"source": "dynamic"}
        
        if self.doc_count == 0:
            return [], stats
        
        try:
            # 计算查询向量
            query_vector = self._compute_vector(query)
            
            # 获取候选文档
            if course_id and course_id in self.course_id_map:
                candidate_doc_ids = self.course_id_map[course_id]
            else:
                candidate_doc_ids = list(self.documents.keys())
            
            if not candidate_doc_ids:
                return [], stats
            
            # 计算相似度
            scores = []
            for doc_id in candidate_doc_ids:
                if doc_id in self.tfidf_vectors:
                    doc_vector = self.tfidf_vectors[doc_id]
                    score = float(np.dot(query_vector, doc_vector))
                    scores.append((doc_id, score))
                    
                    # 更新访问统计
                    if doc_id in self.documents:
                        self.documents[doc_id].touch()
            
            # 排序
            scores.sort(key=lambda x: x[1], reverse=True)
            
            # 构建结果
            results = []
            for doc_id, score in scores[:top_k]:
                if score > 0 and doc_id in self.documents:
                    doc = self.documents[doc_id]
                    results.append({
                        "doc_id": doc_id,
                        "content": doc.content[:500],
                        "score": score,
                        "channel": "dynamic",
                        "course_id": doc.course_id,
                        "metadata": doc.metadata
                    })
            
            stats["dynamic_count"] = len(results)
            stats["dynamic_search_time"] = (datetime.now() - start_time).total_seconds()
            
            return results, stats
        
        except Exception as e:
            logger.error(f"动态库检索失败：{e}", exc_info=True)
            return [], {"error": str(e), "source": "dynamic"}
    
    async def get_stable_documents(self) -> List[str]:
        """获取可晋升到静态库的文档 ID 列表"""
        stable_ids = []
        for doc_id, doc in self.documents.items():
            if doc.is_stable(self.promotion_days, self.promotion_min_access):
                stable_ids.append(doc_id)
        return stable_ids
    
    async def promote_to_static(self, doc_ids: List[str]) -> List[Dict[str, Any]]:
        """
        将文档晋升到静态库 (返回文档数据供静态库使用)
        
        Args:
            doc_ids: 要晋升的文档 ID 列表
        
        Returns:
            晋升的文档数据列表
        """
        documents_data = []
        
        for doc_id in doc_ids:
            if doc_id in self.documents:
                doc = self.documents[doc_id]
                documents_data.append({
                    "doc_id": doc_id,
                    "content": doc.content,
                    "course_id": doc.course_id,
                    "metadata": doc.metadata
                })
                
                # 从动态库移除
                await self.remove_documents([doc_id])
        
        logger.info(f"晋升文档到静态库：{len(documents_data)} 个")
        return documents_data
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "doc_count": self.doc_count,
            "vocab_size": self.vocab_size,
            "course_count": len(self.course_id_map),
            "memory_usage_mb": sum(v.nbytes for v in self.tfidf_vectors.values()) / 1024 / 1024,
            "promotion_candidates": sum(1 for d in self.documents.values() if d.is_stable())
        }
