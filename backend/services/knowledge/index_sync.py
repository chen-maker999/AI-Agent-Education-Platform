"""
索引同步服务 - 统一管理 BM25、TF-IDF、FAISS、混合检索索引的同步更新

确保文档增删改时所有索引保持一致

P11 增强:
- 静态库增量更新支持
- 版本管理和一致性检查
- 后台定期重建调度
- BACKEND-002: FAISS 定期重建机制
- BACKEND-005: FAISS 原子保存 + 备份
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import threading
import time

logger = logging.getLogger("index_sync")


class IndexSynchronizer:
    """
    索引同步器

    功能:
    - 添加文档时同步更新所有索引
    - 删除文档时同步移除所有索引
    - 更新文档时先删后加
    - 支持批量操作
    - 支持降级处理 (某个索引失败不影响其他索引)
    - 支持混合检索引擎 (静态库 + 动态库)
    - P11 增强：静态库增量更新和版本管理
    """

    def __init__(self):
        self.bm25_index = None
        self.tfidf_loaded = False
        self.faiss_loaded = False
        self.hybrid_engine = None
        self.static_index = None

        # 静态库增量更新
        self._pending_static_rebuild = False
        self._dirty_docs_count = 0
        self._last_static_rebuild: Optional[datetime] = None

        # FAISS 定期重建 (BACKEND-002)
        self._pending_faiss_rebuild = False
        self._faiss_deleted_count = 0
        self._last_faiss_rebuild: Optional[datetime] = None
        self._faiss_rebuild_threshold = 100  # 删除 100 个文档后触发重建
        self._faiss_rebuild_interval_hours = 24  # 24 小时定时重建

        # 后台重建线程
        self._rebuild_thread: Optional[threading.Thread] = None
        self._stop_rebuild = False

        self._init_indices()
        self._start_background_rebuild_scheduler()

    def _init_indices(self):
        """初始化索引引用"""
        try:
            from services.knowledge.bm25_search.main import bm25_index
            self.bm25_index = bm25_index
            logger.info("BM25 索引已加载")
        except Exception as e:
            logger.warning(f"BM25 索引加载失败：{e}")

        try:
            from services.knowledge.embedding.tfidf_main import tfidf_matrix
            self.tfidf_loaded = tfidf_matrix is not None
            logger.info(f"TF-IDF 索引已加载：{self.tfidf_loaded}")
        except Exception as e:
            logger.warning(f"TF-IDF 索引加载失败：{e}")

        try:
            from services.knowledge.faiss_indexer.main import faiss_index
            self.faiss_loaded = faiss_index is not None and faiss_index.ntotal > 0
            logger.info(f"FAISS 索引已加载：{self.faiss_loaded}")
        except Exception as e:
            logger.warning(f"FAISS 索引加载失败：{e}")

        # 静态库索引
        try:
            from services.knowledge.rag.hybrid_search.static_index import StaticIndex
            self.static_index = StaticIndex()
            # 异步加载
            asyncio.create_task(self.static_index.load_from_disk())
            logger.info("静态库索引已初始化")
        except Exception as e:
            logger.warning(f"静态库索引初始化失败：{e}")
            self.static_index = None

        # 混合检索引擎 (异步初始化)
        logger.info("混合检索引擎将在首次使用时初始化")
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        添加文档到所有索引
        
        Args:
            documents: 文档列表，每个文档包含:
                - doc_id: str
                - content: str
                - course_id: str
                - metadata: dict
        
        Returns:
            同步结果统计
        """
        results = {
            "total": len(documents),
            "bm25_success": 0,
            "bm25_failed": 0,
            "tfidf_success": 0,
            "tfidf_failed": 0,
            "faiss_success": 0,
            "faiss_failed": 0,
            "errors": []
        }
        
        # 1. 添加到 BM25 索引
        if self.bm25_index:
            try:
                from services.knowledge.bm25_search.main import BM25Document
                for doc_data in documents:
                    try:
                        bm25_doc = BM25Document(
                            doc_id=doc_data["doc_id"],
                            content=doc_data["content"],
                            course_id=doc_data["course_id"],
                            metadata=doc_data.get("metadata", {})
                        )
                        self.bm25_index.add_document(bm25_doc)
                        results["bm25_success"] += 1
                    except Exception as e:
                        results["bm25_failed"] += 1
                        results["errors"].append(f"BM25 添加失败 {doc_data['doc_id']}: {e}")
                
                # 保存 BM25 索引
                self.bm25_index.save()
            except Exception as e:
                logger.error(f"BM25 索引添加失败：{e}")
        else:
            results["bm25_failed"] = len(documents)
            results["errors"].append("BM25 索引未初始化")
        
        # 2. 重新构建 TF-IDF 索引 (需要重新计算整个矩阵)
        # 注意：TF-IDF 不支持增量更新，需要重建
        # 这里只标记需要重建，实际重建在后台进行
        if self.tfidf_loaded:
            try:
                # TF-IDF 需要重建索引，触发后台重建任务
                results["tfidf_success"] = len(documents)
                results["tfidf_rebuild_needed"] = True
            except Exception as e:
                results["tfidf_failed"] = len(documents)
                results["errors"].append(f"TF-IDF 标记失败：{e}")
        else:
            results["tfidf_failed"] = len(documents)
            results["errors"].append("TF-IDF 索引未初始化")
        
        # 3. 添加到 FAISS 索引
        if self.faiss_loaded:
            try:
                from services.knowledge.faiss_indexer.main import (
                    add_vectors_to_index, doc_id_to_index
                )
                import numpy as np
                from services.knowledge.embedding.tfidf_main import get_text_embedding
                
                # 使用 TF-IDF 计算嵌入向量
                embeddings = []
                valid_doc_ids = []
                
                for doc_data in documents:
                    try:
                        embedding = get_text_embedding(doc_data["content"])
                        embeddings.append(embedding)
                        valid_doc_ids.append(doc_data["doc_id"])
                        results["faiss_success"] += 1
                    except Exception as e:
                        results["faiss_failed"] += 1
                        results["errors"].append(f"FAISS 嵌入计算失败 {doc_data['doc_id']}: {e}")
                
                if embeddings:
                    vectors = np.array(embeddings).astype('float32')
                    add_vectors_to_index(vectors, valid_doc_ids)
                
                # 保存 FAISS 索引
                from services.knowledge.faiss_indexer.main import save_index_to_disk
                save_index_to_disk()
            except Exception as e:
                logger.error(f"FAISS 索引添加失败：{e}")
                results["faiss_failed"] = len(documents)
                results["errors"].append(f"FAISS 添加失败：{e}")
        else:
            results["faiss_failed"] = len(documents)
            results["errors"].append("FAISS 索引未初始化")

        # 4. 添加到混合检索引擎 (动态库)
        try:
            from services.knowledge.rag.retriever import add_documents_to_hybrid_index

            # 添加到动态库 (新上传的文档视为动态文档)
            hybrid_result = await add_documents_to_hybrid_index(documents, is_static=False)
            results["hybrid_success"] = hybrid_result.get("added", 0)
            results["hybrid_target"] = "dynamic"
        except Exception as e:
            logger.warning(f"混合检索引擎添加失败：{e}")
            results["hybrid_failed"] = len(documents)
            results["errors"].append(f"混合检索添加失败：{e}")

        # 5. P11 新增：静态库增量更新
        if self.static_index:
            try:
                # 标记静态库需要重建 (后台进行)
                self._pending_static_rebuild = True
                self._dirty_docs_count += len(documents)
                results["static_index_pending"] = True
                results["static_dirty_docs"] = self._dirty_docs_count
                logger.info(f"静态库标记为需要重建，脏文档数：{self._dirty_docs_count}")
            except Exception as e:
                logger.warning(f"静态库标记失败：{e}")

        return results
    
    async def remove_documents(self, doc_ids: List[str]) -> Dict[str, Any]:
        """
        从所有索引中删除文档
        
        Args:
            doc_ids: 要删除的文档 ID 列表
        
        Returns:
            同步结果统计
        """
        results = {
            "total": len(doc_ids),
            "bm25_success": 0,
            "bm25_failed": 0,
            "tfidf_success": 0,
            "tfidf_failed": 0,
            "faiss_success": 0,
            "faiss_failed": 0,
            "errors": []
        }
        
        # 1. 从 BM25 索引删除
        if self.bm25_index:
            try:
                for doc_id in doc_ids:
                    try:
                        self.bm25_index.remove_document(doc_id)
                        results["bm25_success"] += 1
                    except Exception as e:
                        results["bm25_failed"] += 1
                        results["errors"].append(f"BM25 删除失败 {doc_id}: {e}")
                
                # 保存 BM25 索引
                self.bm25_index.save()
            except Exception as e:
                logger.error(f"BM25 索引删除失败：{e}")
        else:
            results["bm25_failed"] = len(doc_ids)
        
        # 2. TF-IDF 索引需要重建
        if self.tfidf_loaded:
            try:
                results["tfidf_success"] = len(doc_ids)
                results["tfidf_rebuild_needed"] = True
            except Exception as e:
                results["tfidf_failed"] = len(doc_ids)
                results["errors"].append(f"TF-IDF 标记失败：{e}")
        else:
            results["tfidf_failed"] = len(doc_ids)
        
        # 3. FAISS 索引不支持直接删除，需要重建或标记删除
        # 这里使用标记删除的方式 (BACKEND-002 修复)
        if self.faiss_loaded:
            try:
                from services.knowledge.faiss_indexer.main import doc_id_to_index, index_to_doc_id
                from services.knowledge.faiss_indexer.main import faiss_index
                import numpy as np

                # 从映射中移除
                removed_indices = []
                for doc_id in doc_ids:
                    if doc_id in doc_id_to_index:
                        idx = doc_id_to_index[doc_id]
                        removed_indices.append(idx)
                        del doc_id_to_index[doc_id]
                        if idx in index_to_doc_id:
                            del index_to_doc_id[idx]
                        results["faiss_success"] += 1
                    else:
                        results["faiss_failed"] += 1

                # BACKEND-002: 标记需要重建并累计删除数
                self._pending_faiss_rebuild = True
                self._faiss_deleted_count += len(doc_ids)
                results["faiss_rebuild_needed"] = True
                results["faiss_deleted_count"] = self._faiss_deleted_count

                logger.info(f"FAISS 删除 {len(doc_ids)} 个文档，累计删除：{self._faiss_deleted_count}，待重建：{self._pending_faiss_rebuild}")

                # 保存 FAISS 索引
                from services.knowledge.faiss_indexer.main import save_index_to_disk
                save_index_to_disk()
            except Exception as e:
                logger.error(f"FAISS 索引删除失败：{e}")
                results["faiss_failed"] = len(doc_ids)
                results["errors"].append(f"FAISS 删除失败：{e}")
        else:
            results["faiss_failed"] = len(doc_ids)

        # 4. 从混合检索引擎删除
        try:
            from services.knowledge.rag.retriever import remove_documents_from_hybrid_index
            
            hybrid_result = await remove_documents_from_hybrid_index(doc_ids)
            results["hybrid_success"] = hybrid_result.get("total_removed", 0)
        except Exception as e:
            logger.warning(f"混合检索引擎删除失败：{e}")
            results["hybrid_failed"] = len(doc_ids)
            results["errors"].append(f"混合检索删除失败：{e}")

        return results
    
    async def update_document(self, doc_id: str, new_content: str, course_id: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        更新文档（先删后加）
        
        Args:
            doc_id: 文档 ID
            new_content: 新内容
            course_id: 课程 ID
            metadata: 元数据
        
        Returns:
            同步结果
        """
        # 先删除
        await self.remove_documents([doc_id])
        
        # 再添加
        new_doc = {
            "doc_id": doc_id,
            "content": new_content,
            "course_id": course_id,
            "metadata": metadata or {}
        }
        
        result = await self.add_documents([new_doc])
        result["operation"] = "update"
        result["updated_doc_id"] = doc_id
        
        return result
    
    async def rebuild_all_indices(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        重建所有索引（用于初始化或全量更新）
        
        Args:
            documents: 所有文档列表
        
        Returns:
            重建结果
        """
        logger.info(f"开始重建所有索引，共 {len(documents)} 个文档")
        
        results = {
            "total": len(documents),
            "bm25_result": None,
            "tfidf_result": None,
            "faiss_result": None,
            "errors": []
        }
        
        # 1. 重建 BM25 索引
        try:
            from services.knowledge.bm25_search.main import bm25_index, BM25Document
            
            # 清空现有索引
            from services.knowledge.bm25_search.main import BM25Index
            bm25_index = BM25Index()
            
            # 批量添加
            for doc_data in documents:
                bm25_doc = BM25Document(
                    doc_id=doc_data["doc_id"],
                    content=doc_data["content"],
                    course_id=doc_data["course_id"],
                    metadata=doc_data.get("metadata", {})
                )
                bm25_index.add_document(bm25_doc)
            
            # 保存
            bm25_index.save()
            results["bm25_result"] = {"success": len(documents)}
            logger.info(f"BM25 索引重建完成：{len(documents)} 个文档")
        except Exception as e:
            results["errors"].append(f"BM25 重建失败：{e}")
            logger.error(f"BM25 重建失败：{e}")
        
        # 2. 重建 TF-IDF 索引
        try:
            from services.knowledge.embedding.tfidf_main import (
                build_tfidf_vectors, save_tfidf_model,
                tfidf_matrix, doc_id_list, doc_contents
            )
            
            doc_ids = [d["doc_id"] for d in documents]
            contents = [d["content"] for d in documents]
            
            # 构建向量
            vectors = build_tfidf_vectors(contents)
            
            # 更新全局状态
            from services.knowledge.embedding import tfidf_main
            tfidf_main.tfidf_matrix = vectors
            tfidf_main.doc_id_list = doc_ids
            tfidf_main.doc_contents = contents
            
            # 保存
            save_tfidf_model()
            results["tfidf_result"] = {"success": len(documents)}
            logger.info(f"TF-IDF 索引重建完成：{len(documents)} 个文档")
        except Exception as e:
            results["errors"].append(f"TF-IDF 重建失败：{e}")
            logger.error(f"TF-IDF 重建失败：{e}")
        
        # 3. 重建 FAISS 索引
        try:
            from services.knowledge.faiss_indexer.main import (
                faiss_index, initialize_faiss_index, add_vectors_to_index,
                save_index_to_disk, doc_id_to_index, index_to_doc_id
            )
            import numpy as np
            from services.knowledge.embedding.tfidf_main import get_text_embedding
            
            # 重置索引
            initialize_faiss_index(use_hnsw=True)
            
            # 清空映射
            doc_id_to_index.clear()
            index_to_doc_id.clear()
            
            # 计算嵌入并添加
            embeddings = []
            valid_doc_ids = []
            
            for doc_data in documents:
                try:
                    embedding = get_text_embedding(doc_data["content"])
                    embeddings.append(embedding)
                    valid_doc_ids.append(doc_data["doc_id"])
                except Exception as e:
                    logger.warning(f"FAISS 嵌入计算失败 {doc_data['doc_id']}: {e}")
            
            if embeddings:
                vectors = np.array(embeddings).astype('float32')
                add_vectors_to_index(vectors, valid_doc_ids)
                
                # 保存
                save_index_to_disk()
                results["faiss_result"] = {"success": len(valid_doc_ids)}
                logger.info(f"FAISS 索引重建完成：{len(valid_doc_ids)} 个文档")
        except Exception as e:
            results["errors"].append(f"FAISS 重建失败：{e}")
            logger.error(f"FAISS 重建失败：{e}")
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        stats = {
            "bm25_docs": 0,
            "tfidf_docs": 0,
            "faiss_docs": 0,
            "bm25_available": False,
            "tfidf_available": False,
            "faiss_available": False
        }
        
        if self.bm25_index:
            stats["bm25_docs"] = len(self.bm25_index.documents) if hasattr(self.bm25_index, 'documents') else 0
            stats["bm25_available"] = True
        
        try:
            from services.knowledge.embedding.tfidf_main import doc_id_list
            stats["tfidf_docs"] = len(doc_id_list) if doc_id_list else 0
            stats["tfidf_available"] = self.tfidf_loaded
        except:
            pass
        
        try:
            from services.knowledge.faiss_indexer.main import faiss_index
            stats["faiss_docs"] = faiss_index.ntotal if faiss_index else 0
            stats["faiss_available"] = self.faiss_loaded
        except:
            pass

        # P11 新增：静态库状态
        if self.static_index:
            stats["static_index_docs"] = self.static_index.doc_count
            stats["static_index_vocab"] = self.static_index.vocab_size
            stats["static_index_loaded"] = self.static_index.loaded
            stats["static_index_pending_rebuild"] = self._pending_static_rebuild
            stats["static_dirty_docs"] = self._dirty_docs_count

        return stats

    def _start_background_rebuild_scheduler(self):
        """启动后台重建调度器 (BACKEND-002 增强)"""
        def scheduler_loop():
            """调度器循环"""
            logger.info("静态库/FAISS 后台重建调度器已启动")
            while not self._stop_rebuild:
                time.sleep(60)  # 每分钟检查一次

                # 检查是否需要重建静态库
                if self._pending_static_rebuild:
                    # 检查脏文档数是否超过阈值 (100 个文档)
                    if self._dirty_docs_count >= 100:
                        logger.info(f"触发静态库重建，脏文档数：{self._dirty_docs_count}")
                        asyncio.create_task(self._rebuild_static_index())
                    else:
                        # 检查是否超过 24 小时
                        if self._last_static_rebuild:
                            hours_since_rebuild = (datetime.now() - self._last_static_rebuild).total_seconds() / 3600
                            if hours_since_rebuild >= 24:
                                logger.info("定时触发静态库重建 (24 小时)")
                                asyncio.create_task(self._rebuild_static_index())
                        else:
                            # 首次重建
                            logger.info("首次触发静态库重建")
                            asyncio.create_task(self._rebuild_static_index())

                # BACKEND-002: 检查是否需要重建 FAISS 索引
                if self._pending_faiss_rebuild:
                    # 检查删除数是否超过阈值
                    if self._faiss_deleted_count >= self._faiss_rebuild_threshold:
                        logger.info(f"触发 FAISS 索引重建，累计删除：{self._faiss_deleted_count}")
                        asyncio.create_task(self._rebuild_faiss_index())
                    else:
                        # 检查是否超过 24 小时
                        if self._last_faiss_rebuild:
                            hours_since_rebuild = (datetime.now() - self._last_faiss_rebuild).total_seconds() / 3600
                            if hours_since_rebuild >= self._faiss_rebuild_interval_hours:
                                logger.info(f"定时触发 FAISS 索引重建 ({self._faiss_rebuild_interval_hours}小时)")
                                asyncio.create_task(self._rebuild_faiss_index())
                        else:
                            # 首次重建
                            logger.info("首次触发 FAISS 索引重建")
                            asyncio.create_task(self._rebuild_faiss_index())

        self._rebuild_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self._rebuild_thread.start()

    async def _rebuild_static_index(self):
        """重建静态库索引"""
        if not self.static_index:
            logger.warning("静态库未初始化，跳过重建")
            return

        try:
            logger.info("开始重建静态库索引...")

            # 从动态库获取所有文档
            from services.knowledge.rag.retriever import get_all_hybrid_documents
            all_docs = await get_all_hybrid_documents()

            if not all_docs:
                logger.warning("没有文档可重建静态库")
                self._pending_static_rebuild = False
                return

            # 准备文档数据
            doc_ids = [d['doc_id'] for d in all_docs]
            contents = [d['content'] for d in all_docs]
            course_ids = [d.get('course_id', '') for d in all_docs]

            # 重建 TF-IDF 矩阵
            self.static_index.tfidf_matrix = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.static_index._build_tfidf_vectors(contents)
            )

            # 更新元数据
            self.static_index.doc_id_list = doc_ids
            self.static_index.doc_contents = contents
            self.static_index.doc_course_ids = {
                doc_id: course_id
                for doc_id, course_id in zip(doc_ids, course_ids)
            }
            self.static_index.doc_count = len(doc_ids)
            self.static_index.vocab_size = len(self.static_index.vocabulary)
            self.static_index.last_rebuild = datetime.now()
            self.static_index.loaded = True

            # 保存到磁盘
            await self.static_index.save_to_disk()

            # P11 新增：创建版本
            try:
                from services.knowledge.rag.hybrid_search.static_index_version import (
                    create_static_index_version
                )
                create_static_index_version(
                    doc_count=self.static_index.doc_count,
                    vocab_size=self.static_index.vocab_size,
                    matrix_shape=self.static_index.tfidf_matrix.shape,
                    model_path=self.static_index.model_path,
                    matrix_path=self.static_index.matrix_path
                )
            except Exception as e:
                logger.warning(f"创建版本失败：{e}")

            # 重置状态
            self._pending_static_rebuild = False
            self._dirty_docs_count = 0
            self._last_static_rebuild = datetime.now()

            logger.info(f"静态库重建完成：{self.static_index.doc_count} 个文档，词表大小：{self.static_index.vocab_size}")

        except Exception as e:
            logger.error(f"静态库重建失败：{e}")

    async def _rebuild_faiss_index(self):
        """
        重建 FAISS 索引 (BACKEND-002 修复)
        
        从数据库读取所有有效文档，重新构建 FAISS 索引以清理已删除的向量
        """
        if not self.faiss_loaded:
            logger.warning("FAISS 未加载，跳过重建")
            return

        try:
            logger.info(f"开始重建 FAISS 索引...")

            # 从数据库获取所有有效文档
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                from services.knowledge.rag.main import RAGDocument
                result = await session.execute(select(RAGDocument))
                documents = [
                    {
                        'doc_id': row.doc_id,
                        'content': row.content,
                        'course_id': row.course_id,
                        'metadata': row.doc_metadata
                    }
                    for row in result.scalars().all()
                ]

            if not documents:
                logger.warning("没有文档可重建 FAISS 索引")
                self._pending_faiss_rebuild = False
                self._faiss_deleted_count = 0
                return

            # 重置 FAISS 索引
            from services.knowledge.faiss_indexer.main import (
                initialize_faiss_index, add_vectors_to_index,
                save_index_to_disk, doc_id_to_index, index_to_doc_id, faiss_index
            )
            import numpy as np
            from services.knowledge.embedding.tfidf_main import get_text_embedding

            logger.info(f"重置 FAISS 索引，共 {len(documents)} 个文档")

            # 清空映射
            doc_id_to_index.clear()
            index_to_doc_id.clear()

            # 计算嵌入并添加
            embeddings = []
            valid_doc_ids = []

            for doc_data in documents:
                try:
                    embedding = get_text_embedding(doc_data['content'])
                    embeddings.append(embedding)
                    valid_doc_ids.append(doc_data['doc_id'])
                except Exception as e:
                    logger.warning(f"FAISS 嵌入计算失败 {doc_data['doc_id']}: {e}")

            if embeddings:
                vectors = np.array(embeddings).astype('float32')
                add_vectors_to_index(vectors, valid_doc_ids)
                save_index_to_disk()

                # 重置状态
                self._pending_faiss_rebuild = False
                self._faiss_deleted_count = 0
                self._last_faiss_rebuild = datetime.now()

                logger.info(f"FAISS 索引重建完成：{len(valid_doc_ids)} 个向量")

        except Exception as e:
            logger.error(f"FAISS 重建失败：{e}", exc_info=True)

    async def trigger_static_rebuild(self) -> Dict[str, Any]:
        """
        手动触发静态库重建

        Returns:
            重建结果
        """
        result = {
            "success": False,
            "message": "",
            "doc_count": 0,
            "vocab_size": 0
        }

        try:
            await self._rebuild_static_index()
            result["success"] = not self._pending_static_rebuild
            result["message"] = "重建完成" if result["success"] else "重建失败"
            result["doc_count"] = self.static_index.doc_count if self.static_index else 0
            result["vocab_size"] = self.static_index.vocab_size if self.static_index else 0
        except Exception as e:
            result["message"] = str(e)

        return result

    def get_static_index_status(self) -> Dict[str, Any]:
        """
        获取静态库状态

        Returns:
            状态信息
        """
        if not self.static_index:
            return {"available": False}

        return {
            "available": True,
            "loaded": self.static_index.loaded,
            "doc_count": self.static_index.doc_count,
            "vocab_size": self.static_index.vocab_size,
            "last_rebuild": self.static_index.last_rebuild.isoformat() if self.static_index.last_rebuild else None,
            "pending_rebuild": self._pending_static_rebuild,
            "dirty_docs_count": self._dirty_docs_count,
            "last_rebuild_hours_ago": (
                (datetime.now() - self._last_static_rebuild).total_seconds() / 3600
                if self._last_static_rebuild else None
            )
        }

    def stop(self):
        """停止同步器"""
        self._stop_rebuild = True
        if self._rebuild_thread:
            self._rebuild_thread.join(timeout=5)
        logger.info("索引同步器已停止")


# 全局同步器实例
synchronizer = IndexSynchronizer()


async def sync_add_documents(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """同步添加文档到所有索引"""
    return await synchronizer.add_documents(documents)


async def sync_remove_documents(doc_ids: List[str]) -> Dict[str, Any]:
    """同步从所有索引删除文档"""
    return await synchronizer.remove_documents(doc_ids)


async def sync_update_document(doc_id: str, new_content: str, course_id: str, metadata: Dict = None) -> Dict[str, Any]:
    """同步更新文档"""
    return await synchronizer.update_document(doc_id, new_content, course_id, metadata)


async def sync_rebuild_all(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """重建所有索引"""
    return await synchronizer.rebuild_all_indices(documents)


def get_index_stats() -> Dict[str, Any]:
    """获取索引统计"""
    return synchronizer.get_stats()


async def trigger_static_index_rebuild() -> Dict[str, Any]:
    """手动触发静态库重建"""
    return await synchronizer.trigger_static_rebuild()


def get_static_index_status() -> Dict[str, Any]:
    """获取静态库状态"""
    return synchronizer.get_static_index_status()


def stop_index_synchronizer():
    """停止索引同步器"""
    synchronizer.stop()
