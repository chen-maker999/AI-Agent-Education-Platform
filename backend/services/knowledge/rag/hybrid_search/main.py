"""
混合检索引擎 - 统一入口

流程:
1. 接收查询
2. 获取/计算查询向量
3. 并发检索静态库 + 动态库
4. 合并结果
5. 返回最终 Top-K
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .static_index import StaticIndex
from .dynamic_index import DynamicIndex
from .cache_manager import QueryCacheManager
from .merger import ResultMerger

logger = logging.getLogger("hybrid_search")


class HybridSearchEngine:
    """
    混合检索引擎
    
    结合静态库 (预计算 TF-IDF) 和动态库 (实时计算 TF-IDF) 的优势
    提供快速、准确的检索服务
    """
    
    def __init__(self,
                 static_weight: float = 0.6,
                 dynamic_weight: float = 0.4,
                 cache_max_size: int = 10000,  # P11 优化：最大缓存 10000 个查询
                 cache_ttl: int = 7200,  # P11 优化：从 3600 提升至 7200 (2 小时)
                 use_diversity: bool = False):
        """
        Args:
            static_weight: 静态库结果权重
            dynamic_weight: 动态库结果权重
            cache_max_size: 查询缓存最大大小 (P11 优化：10000)
            cache_ttl: 查询缓存 TTL (秒) (P11 优化：从 3600 提升至 7200)
            use_diversity: 是否启用多样性保护
        """
        # 初始化组件
        self.static_index = StaticIndex()
        self.dynamic_index = DynamicIndex()
        self.cache_manager = QueryCacheManager(
            max_size=cache_max_size,
            ttl=cache_ttl
        )
        self.merger = ResultMerger(
            static_weight=static_weight,
            dynamic_weight=dynamic_weight,
            use_diversity=use_diversity
        )
        
        # 状态
        self.initialized = False
        self._background_rebuild_task: Optional[asyncio.Task] = None
        
        # 配置
        self.auto_promotion_enabled = True
        self.rebuild_threshold = 100  # 动态库文档数达到此值触发后台重建
    
    async def initialize(self):
        """启动时加载静态库"""
        logger.info("正在初始化混合检索引擎...")
        
        # 加载静态库
        static_loaded = await self.static_index.load_from_disk()
        if static_loaded:
            logger.info(f"静态库加载成功：{self.static_index.doc_count} 个文档")
        else:
            logger.warning("静态库加载失败或不存在")
        
        # 启动缓存清理任务
        await self.cache_manager.start_cleanup_task()
        
        self.initialized = True
        logger.info("混合检索引擎初始化完成")
    
    async def shutdown(self):
        """关闭时清理资源"""
        logger.info("正在关闭混合检索引擎...")
        
        # 停止缓存清理任务
        await self.cache_manager.stop_cleanup_task()
        
        # 取消后台重建任务
        if self._background_rebuild_task:
            self._background_rebuild_task.cancel()
            try:
                await self._background_rebuild_task
            except asyncio.CancelledError:
                pass
        
        logger.info("混合检索引擎已关闭")
    
    async def _get_query_vector(self, query: str, 
                                course_id: Optional[str] = None,
                                use_cache: bool = True) -> Optional[Any]:
        """
        获取查询向量 (优先从缓存获取)
        
        Args:
            query: 查询文本
            course_id: 课程 ID
            use_cache: 是否使用缓存
        
        Returns:
            查询向量，如果失败则返回 None
        """
        # 尝试从缓存获取
        if use_cache:
            cached_vector = await self.cache_manager.get(query, course_id)
            if cached_vector is not None:
                logger.debug(f"查询缓存命中：{query[:20]}...")
                return cached_vector
        
        # 从静态库计算 (如果已加载)
        if self.static_index.loaded and self.static_index.vocab_size > 0:
            try:
                vector = self.static_index.get_query_vector(query)
                
                # 缓存向量
                if use_cache:
                    await self.cache_manager.set(query, vector, course_id)
                
                return vector
            except Exception as e:
                logger.error(f"静态库计算查询向量失败：{e}")
        
        # 从动态库计算
        if self.dynamic_index.doc_count > 0:
            try:
                vector = self.dynamic_index._compute_vector(query)
                
                # 缓存向量
                if use_cache:
                    await self.cache_manager.set(query, vector, course_id)
                
                return vector
            except Exception as e:
                logger.error(f"动态库计算查询向量失败：{e}")
        
        return None
    
    async def search(self,
                     query: str,
                     course_id: Optional[str] = None,
                     top_k: int = 10,
                     use_cache: bool = True,
                     use_static: bool = True,
                     use_dynamic: bool = True) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        混合检索入口
        
        Args:
            query: 查询文本
            course_id: 课程 ID 过滤 (可选)
            top_k: 返回结果数
            use_cache: 是否使用查询缓存
            use_static: 是否使用静态库
            use_dynamic: 是否使用动态库
        
        Returns:
            (合并后的结果列表，检索统计信息)
        """
        start_time = datetime.now()
        stats = {
            "query": query[:50],
            "course_id": course_id,
            "top_k": top_k
        }
        
        if not self.initialized:
            logger.warning("混合检索引擎未初始化")
            return [], stats
        
        # 1. 获取查询向量
        query_vector = await self._get_query_vector(query, course_id, use_cache)
        stats["cache_hit"] = query_vector is not None
        
        # 2. 并发检索静态库 + 动态库
        static_results = []
        dynamic_results = []
        
        tasks = []
        
        if use_static and self.static_index.loaded:
            tasks.append(self._search_static(query_vector, top_k, course_id))
        
        if use_dynamic and self.dynamic_index.doc_count > 0:
            tasks.append(self._search_dynamic(query, top_k, course_id))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"检索任务失败：{result}")
                elif isinstance(result, tuple):
                    if "static" in str(result[1].get("source", "")):
                        static_results = result[0]
                        stats.update(result[1])
                    else:
                        dynamic_results = result[0]
                        stats.update(result[1])
        
        # 3. 合并结果
        merged_results = self.merger.merge(
            static_results,
            dynamic_results,
            top_k
        )
        
        # 4. 添加统计信息
        stats.update(self.merger.get_stats(static_results, dynamic_results, merged_results))
        stats["total_time"] = (datetime.now() - start_time).total_seconds()
        stats["static_loaded"] = self.static_index.loaded
        stats["dynamic_docs"] = self.dynamic_index.doc_count
        
        logger.info(f"混合检索完成：{len(merged_results)}个结果，耗时：{stats['total_time']:.3f}s")
        
        return merged_results, stats
    
    async def _search_static(self, 
                             query_vector: Optional[Any],
                             top_k: int,
                             course_id: Optional[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """检索静态库"""
        if query_vector is None:
            return [], {"source": "static", "error": "query_vector is None"}
        
        return await self.static_index.search(query_vector, top_k, course_id)
    
    async def _search_dynamic(self,
                              query: str,
                              top_k: int,
                              course_id: Optional[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """检索动态库"""
        return await self.dynamic_index.search(query, top_k, course_id)
    
    async def add_documents(self, 
                           documents: List[Dict[str, Any]],
                           is_static: bool = False) -> Dict[str, Any]:
        """
        添加文档到对应库
        
        Args:
            documents: 文档列表
            is_static: 是否添加到静态库
        
        Returns:
            添加结果
        """
        if is_static:
            # 添加到静态库 (需要重建)
            success = await self.static_index.rebuild(documents)
            return {
                "added": len(documents) if success else 0,
                "target": "static",
                "success": success
            }
        else:
            # 添加到动态库
            count = await self.dynamic_index.add_documents(documents)
            
            # 检查是否需要触发后台重建
            if (self.auto_promotion_enabled and 
                self.dynamic_index.doc_count >= self.rebuild_threshold):
                await self._trigger_background_rebuild()
            
            return {
                "added": count,
                "target": "dynamic",
                "success": True
            }
    
    async def remove_documents(self, doc_ids: List[str]) -> Dict[str, Any]:
        """
        从两个库删除文档 (BACKEND-004 修复)

        Args:
            doc_ids: 要删除的文档 ID 列表

        Returns:
            删除结果
        """
        # 从静态库删除 (标记需要重建)
        static_removed = 0
        if self.static_index.loaded:
            # 静态库不支持直接删除，标记需要重建
            # 这里标记静态库需要重建，实际删除在重建时进行
            from services.knowledge.rag.retriever import get_hybrid_engine
            synchronizer = None
            try:
                from services.knowledge.index_sync import synchronizer
                if synchronizer:
                    synchronizer._pending_static_rebuild = True
                    synchronizer._dirty_docs_count += len(doc_ids)
                    static_removed = len(doc_ids)
                    logger.info(f"静态库标记为需要重建 (删除操作)，脏文档数：{synchronizer._dirty_docs_count}")
            except Exception as e:
                logger.warning(f"标记静态库重建失败：{e}")

        # 从动态库删除
        dynamic_removed = await self.dynamic_index.remove_documents(doc_ids)

        return {
            "static_removed": static_removed,
            "dynamic_removed": dynamic_removed,
            "total_removed": static_removed + dynamic_removed,
            "static_rebuild_pending": self.static_index.loaded and static_removed > 0
        }
    
    async def _trigger_background_rebuild(self):
        """触发后台重建静态库"""
        if self._background_rebuild_task and not self._background_rebuild_task.done():
            logger.debug("后台重建任务已在运行")
            return
        
        self._background_rebuild_task = asyncio.create_task(
            self._background_rebuild(),
            name="static_index_rebuild"
        )
        logger.info(f"触发后台重建静态库 (动态库文档数：{self.dynamic_index.doc_count})")
    
    async def _background_rebuild(self):
        """后台重建静态库 (将动态库的稳定文档晋升)"""
        try:
            # 获取可晋升的文档
            stable_doc_ids = await self.dynamic_index.get_stable_documents()
            
            if not stable_doc_ids:
                logger.debug("没有可晋升的文档")
                return
            
            # 晋升文档
            documents_data = await self.dynamic_index.promote_to_static(stable_doc_ids)
            
            if not documents_data:
                return
            
            # 合并到静态库
            # 注意：这里需要合并到现有静态库，而不是重建
            # TODO: 实现静态库增量更新
            
            logger.info(f"后台重建完成：晋升{len(documents_data)}个文档到静态库")
        
        except asyncio.CancelledError:
            logger.info("后台重建任务已取消")
        except Exception as e:
            logger.error(f"后台重建失败：{e}", exc_info=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        return {
            "initialized": self.initialized,
            "static_index": self.static_index.get_stats(),
            "dynamic_index": self.dynamic_index.get_stats(),
            "cache": self.cache_manager.get_stats(),
            "auto_promotion_enabled": self.auto_promotion_enabled,
            "background_rebuild_running": (
                self._background_rebuild_task is not None and 
                not self._background_rebuild_task.done()
            )
        }


# 全局引擎实例
_engine: Optional[HybridSearchEngine] = None


async def get_search_engine() -> HybridSearchEngine:
    """获取或创建全局搜索引擎实例"""
    global _engine
    
    if _engine is None:
        _engine = HybridSearchEngine()
        await _engine.initialize()
    
    return _engine


async def shutdown_search_engine():
    """关闭全局搜索引擎实例"""
    global _engine
    
    if _engine is not None:
        await _engine.shutdown()
        _engine = None


async def hybrid_search(query: str,
                        course_id: Optional[str] = None,
                        top_k: int = 10,
                        use_cache: bool = True) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    便捷函数：执行混合检索
    
    Args:
        query: 查询文本
        course_id: 课程 ID
        top_k: 返回结果数
        use_cache: 是否使用缓存
    
    Returns:
        (结果列表，统计信息)
    """
    engine = await get_search_engine()
    return await engine.search(query, course_id, top_k, use_cache)
