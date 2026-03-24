"""
静态库索引管理 - 预计算 TF-IDF 矩阵，只读优化

特性:
- 预计算 TF-IDF 矩阵 (稀疏矩阵存储)
- 支持快速加载/卸载
- 定期后台重建 (低频)
- 支持按 course_id 过滤
"""

import asyncio
import pickle
import os
import logging
import numpy as np
from scipy import sparse
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger("static_index")


class StaticIndex:
    """
    静态文档索引
    
    用于存储稳定、不频繁变更的文档（如教材、手册、历史资料等）
    使用预计算的 TF-IDF 矩阵实现快速检索
    """
    
    def __init__(self):
        # TF-IDF 矩阵 (稀疏矩阵)
        self.tfidf_matrix: Optional[sparse.spmatrix] = None
        
        # 文档元数据
        self.doc_id_list: List[str] = []  # index -> doc_id
        self.doc_contents: List[str] = []  # index -> content
        self.doc_course_ids: Dict[str, str] = {}  # doc_id -> course_id
        
        # 词表和 IDF 值
        self.vocabulary: Dict[str, int] = {}  # token -> index
        self.idf_values: Dict[str, float] = {}  # token -> idf
        
        # 课程 ID 索引 (用于快速过滤)
        self.course_id_map: Dict[str, List[int]] = {}  # course_id -> [indices]
        
        # 状态管理
        self.last_rebuild: Optional[datetime] = None
        self.loaded = False
        self.doc_count = 0
        self.vocab_size = 0
        
        # 配置
        self.model_path = "data/tfidf_static_model.pkl"
        self.matrix_path = "data/tfidf_static_matrix.dat.npz"
    
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
    
    def _build_tfidf_vectors(self, texts: List[str]) -> sparse.lil_matrix:
        """构建 TF-IDF 向量矩阵 (稀疏矩阵)"""
        # 分词
        tokenized_docs = [self._chinese_tokenize(text) for text in texts]
        
        # 构建词表
        all_tokens = set()
        for doc in tokenized_docs:
            all_tokens.update(doc)
        
        self.vocabulary = {token: idx for idx, token in enumerate(sorted(all_tokens))}
        self.vocab_size = len(self.vocabulary)
        
        # 计算 IDF
        N = len(tokenized_docs)
        df = {}
        for doc in tokenized_docs:
            for token in set(doc):
                df[token] = df.get(token, 0) + 1
        
        import math
        self.idf_values = {}
        for token, freq in df.items():
            self.idf_values[token] = math.log((N + 1) / (freq + 1)) + 1
        
        # 构建稀疏 TF-IDF 矩阵
        tfidf_matrix = sparse.lil_matrix((len(texts), self.vocab_size), dtype=np.float32)
        
        for doc_idx, doc_tokens in enumerate(tokenized_docs):
            tf = self._compute_tf(doc_tokens)
            for token, tf_val in tf.items():
                if token in self.vocabulary:
                    vocab_idx = self.vocabulary[token]
                    idf_val = self.idf_values.get(token, 1.0)
                    tfidf_matrix[doc_idx, vocab_idx] = tf_val * idf_val
        
        # L2 归一化 (按行)
        from sklearn.preprocessing import normalize
        tfidf_matrix = normalize(tfidf_matrix, norm='l2', axis=1)
        
        return tfidf_matrix.tocsr()  # 转换为 CSR 格式加速检索
    
    async def load_from_disk(self) -> bool:
        """从磁盘加载预计算矩阵"""
        try:
            if not os.path.exists(self.model_path):
                logger.warning(f"静态库模型文件不存在：{self.model_path}")
                return False
            
            # 加载元数据
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.doc_id_list = data.get('doc_ids', [])
                self.doc_contents = data.get('contents', [])
                self.vocabulary = data.get('vocabulary', {})
                self.idf_values = data.get('idf', {})
                self.doc_course_ids = data.get('course_ids', {})
                self.last_rebuild = data.get('last_rebuild')
            
            # 加载稀疏矩阵 (使用内存映射优化)
            if os.path.exists(self.matrix_path):
                self.tfidf_matrix = sparse.load_npz(self.matrix_path)
            
            # 构建课程 ID 索引
            self._build_course_id_index()
            
            self.doc_count = len(self.doc_id_list)
            self.vocab_size = len(self.vocabulary)
            self.loaded = True
            
            logger.info(f"静态库加载成功：{self.doc_count} 个文档，词表大小：{self.vocab_size}")
            return True
        
        except Exception as e:
            logger.error(f"静态库加载失败：{e}", exc_info=True)
            return False
    
    def _build_course_id_index(self):
        """构建课程 ID 索引"""
        self.course_id_map = {}
        for idx, doc_id in enumerate(self.doc_id_list):
            course_id = self.doc_course_ids.get(doc_id, "default")
            if course_id not in self.course_id_map:
                self.course_id_map[course_id] = []
            self.course_id_map[course_id].append(idx)
    
    async def save_to_disk(self):
        """保存静态库到磁盘"""
        try:
            os.makedirs("data", exist_ok=True)
            
            # 保存元数据
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'doc_ids': self.doc_id_list,
                    'contents': self.doc_contents,
                    'vocabulary': self.vocabulary,
                    'idf': self.idf_values,
                    'course_ids': self.doc_course_ids,
                    'last_rebuild': self.last_rebuild
                }, f)
            
            # 保存稀疏矩阵
            if self.tfidf_matrix is not None:
                sparse.save_npz(self.matrix_path, self.tfidf_matrix)
            
            logger.info(f"静态库已保存：{self.doc_count} 个文档")
        
        except Exception as e:
            logger.error(f"静态库保存失败：{e}", exc_info=True)
    
    async def rebuild(self, documents: List[Dict[str, Any]]) -> bool:
        """
        重建静态库索引
        
        Args:
            documents: 文档列表，每个包含 doc_id, content, course_id
        
        Returns:
            是否成功
        """
        logger.info(f"开始重建静态库，共 {len(documents)} 个文档")
        start_time = datetime.now()
        
        try:
            # 提取内容
            self.doc_id_list = [d["doc_id"] for d in documents]
            self.doc_contents = [d["content"] for d in documents]
            self.doc_course_ids = {d["doc_id"]: d.get("course_id", "default") for d in documents}
            
            # 构建 TF-IDF 矩阵
            self.tfidf_matrix = self._build_tfidf_vectors(self.doc_contents)
            
            # 构建课程 ID 索引
            self._build_course_id_index()
            
            # 更新状态
            self.doc_count = len(self.doc_id_list)
            self.vocab_size = len(self.vocabulary)
            self.last_rebuild = datetime.now()
            self.loaded = True
            
            # 保存到磁盘
            await self.save_to_disk()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"静态库重建完成：{self.doc_count} 个文档，耗时：{processing_time:.2f}s")
            
            return True
        
        except Exception as e:
            logger.error(f"静态库重建失败：{e}", exc_info=True)
            return False
    
    async def search(self, 
                     query_vector: np.ndarray,
                     top_k: int = 10,
                     course_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        快速检索 (O(1) 矩阵运算)
        
        Args:
            query_vector: 查询向量 (已归一化)
            top_k: 返回结果数
            course_id: 课程 ID 过滤 (可选)
        
        Returns:
            (结果列表，统计信息)
        """
        start_time = datetime.now()
        stats = {"source": "static"}
        
        if self.tfidf_matrix is None or not self.loaded:
            return [], stats
        
        try:
            # 获取候选文档索引
            if course_id and course_id in self.course_id_map:
                candidate_indices = self.course_id_map[course_id]
                if not candidate_indices:
                    return [], stats
                
                # 只检索候选文档
                candidate_matrix = self.tfidf_matrix[candidate_indices]
            else:
                candidate_matrix = self.tfidf_matrix
                candidate_indices = list(range(self.doc_count))
            
            # 计算余弦相似度 (矩阵点积)
            similarities = np.asarray(candidate_matrix @ query_vector).flatten()
            
            # 获取 top_k 索引
            if len(similarities) <= top_k:
                top_indices = np.argsort(similarities)[::-1]
            else:
                top_indices = np.argpartition(similarities, -top_k)[-top_k:]
                top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]
            
            # 构建结果
            results = []
            for local_idx in top_indices:
                global_idx = candidate_indices[local_idx]
                score = float(similarities[local_idx])
                
                if score > 0:
                    results.append({
                        "doc_id": self.doc_id_list[global_idx],
                        "content": self.doc_contents[global_idx][:500],
                        "score": score,
                        "channel": "static",
                        "course_id": self.doc_course_ids.get(self.doc_id_list[global_idx], "default")
                    })
            
            stats["static_count"] = len(results)
            stats["static_search_time"] = (datetime.now() - start_time).total_seconds()
            
            return results, stats
        
        except Exception as e:
            logger.error(f"静态库检索失败：{e}", exc_info=True)
            return [], {"error": str(e), "source": "static"}
    
    def get_query_vector(self, query: str) -> np.ndarray:
        """
        计算查询的 TF-IDF 向量
        
        Args:
            query: 查询文本
        
        Returns:
            归一化的查询向量
        """
        tokens = self._chinese_tokenize(query)
        tf = self._compute_tf(tokens)
        
        vector = np.zeros(self.vocab_size, dtype=np.float32)
        for token, tf_val in tf.items():
            if token in self.vocabulary:
                idx = self.vocabulary[token]
                idf_val = self.idf_values.get(token, 1.0)
                vector[idx] = tf_val * idf_val
        
        # L2 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "doc_count": self.doc_count,
            "vocab_size": self.vocab_size,
            "loaded": self.loaded,
            "last_rebuild": self.last_rebuild.isoformat() if self.last_rebuild else None,
            "course_count": len(self.course_id_map),
            "memory_usage_mb": self.tfidf_matrix.data.nbytes / 1024 / 1024 if self.tfidf_matrix is not None else 0
        }
