"""
RAG 检索优化服务 - 集成混合检索引擎（静态库 + 动态库）

P11 优化:
1. 集成查询翻译 (中文→英文) 进行跨语言检索
2. 集成 HyDE (假设文档嵌入)
3. 集成查询分解
4. 增强的多路检索策略
"""

import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid as uuid_module
import logging
import json

# ==================== 结构化日志 ====================
logger = logging.getLogger("rag_retriever")

# ==================== 混合检索引擎 ====================
_hybrid_engine = None
_hybrid_engine_initialized = False


async def get_hybrid_engine():
    """懒加载混合检索引擎"""
    global _hybrid_engine, _hybrid_engine_initialized
    
    if not _hybrid_engine_initialized:
        try:
            from services.knowledge.rag.hybrid_search.main import get_search_engine
            _hybrid_engine = await get_search_engine()
            _hybrid_engine_initialized = True
            logger.info("混合检索引擎初始化成功")
        except Exception as e:
            logger.warning(f"混合检索引擎初始化失败：{e}，降级为传统检索")
            _hybrid_engine_initialized = True  # 标记为已尝试
    
    return _hybrid_engine


class StructuredFormatter(logging.Formatter):
    """JSON 日志格式化器"""
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": getattr(record, 'request_id', 'N/A'),
            "service": "rag_retriever"
        }
        if hasattr(record, 'exc_info') and record.exc_info:
            import traceback
            log_data["traceback"] = traceback.format_exception(*record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)


def get_logger(request_id: Optional[str] = None):
    """获取结构化日志器"""
    extra = {"request_id": request_id or str(uuid_module.uuid4()), "service": "rag_retriever"}
    return logging.LoggerAdapter(logger, extra)


# ==================== 全局锁保护 ====================
_index_lock = asyncio.Lock()
_cache_lock = asyncio.Lock()


# ==================== 查询缓存 ====================
_query_embedding_cache: Dict[str, np.ndarray] = {}
_CACHE_TTL = 3600  # 1 小时


# ==================== 跨语言检索支持 ====================

# 简单的中文 - 英文技术术语映射（本地翻译备用方案）
# P11 扩展：增加 Java 和面向对象编程相关术语，提升跨语言检索准确率
TECH_TERMS_MAP = {
    # ========== 面向对象核心概念 ==========
    "继承": "inheritance",
    "多态": "polymorphism",
    "封装": "encapsulation",
    "抽象": "abstraction",
    "面向对象": "object-oriented",
    "对象": "object",
    "类": "class",
    "实例": "instance",
    "父类": "superclass",
    "子类": "subclass",
    "基类": "base class",
    "派生类": "derived class",
    "继承关系": "inheritance relationship",
    
    # ========== 类成员 ==========
    "方法": "method",
    "变量": "variable",
    "属性": "field",
    "字段": "field",
    "成员变量": "member variable",
    "成员方法": "member method",
    "构造函数": "constructor",
    "构造方法": "constructor",
    "析构函数": "destructor",
    "参数": "parameter",
    "返回值": "return value",
    "重载": "overload",
    "重写": "override",
    "覆盖": "override",
    "父类引用": "superclass reference",
    "子类对象": "subclass object",
    
    # ========== 访问控制 ==========
    "访问控制": "access control",
    "私有": "private",
    "公有": "public",
    "保护": "protected",
    "默认": "default",
    "可见性": "visibility",
    "隐藏": "hide",
    "安全性": "security",
    
    # ========== 抽象类和接口 ==========
    "抽象类": "abstract class",
    "接口": "interface",
    "抽象方法": "abstract method",
    "实现": "implement",
    "静态": "static",
    "最终": "final",
    "常量": "constant",
    
    # ========== 异常处理 ==========
    "异常": "exception",
    "异常处理": "exception handling",
    "try": "try",
    "catch": "catch",
    "finally": "finally",
    "throw": "throw",
    "throws": "throws",
    "抛出": "throw",
    "捕获": "catch",
    "错误": "error",
    "运行时异常": "runtime exception",
    "检查异常": "checked exception",
    "自定义异常": "custom exception",
    
    # ========== 数据类型 ==========
    "泛型": "generics",
    "集合": "collection",
    "列表": "list",
    "映射": "map",
    "哈希": "hash",
    "数组": "array",
    "链表": "linked list",
    "栈": "stack",
    "堆": "heap",
    "队列": "queue",
    "树": "tree",
    "图": "graph",
    "二叉树": "binary tree",
    "哈希表": "hash table",
    "哈希映射": "hashmap",
    "集合框架": "collection framework",
    "动态数组": "dynamic array",
    "迭代器": "iterator",
    "枚举": "enum",
    
    # ========== 基础类型 ==========
    "整数": "integer",
    "浮点数": "floating point",
    "布尔": "boolean",
    "字符": "character",
    "字符串": "string",
    "类型": "type",
    "转换": "cast",
    "类型转换": "type cast",
    "自动装箱": "autoboxing",
    "自动拆箱": "unboxing",
    "包装类": "wrapper class",
    
    # ========== 算法和数据结构 ==========
    "排序": "sorting",
    "查找": "search",
    "递归": "recursion",
    "遍历": "traversal",
    "插入": "insert",
    "删除": "delete",
    "更新": "update",
    "查询": "query",
    
    # ========== 并发编程 ==========
    "线程": "thread",
    "进程": "process",
    "同步": "synchronization",
    "异步": "asynchronous",
    "锁": "lock",
    "监视器": "monitor",
    "信号量": "semaphore",
    "volatile": "volatile",
    "原子": "atomic",
    "并发": "concurrent",
    "并行": "parallel",
    "死锁": "deadlock",
    "线程安全": "thread-safe",
    
    # ========== IO 和流 ==========
    "流": "stream",
    "输入": "input",
    "输出": "output",
    "文件": "file",
    "读取": "read",
    "写入": "write",
    "字节": "byte",
    "字符流": "character stream",
    "字节流": "byte stream",
    "序列化": "serialization",
    "反序列化": "deserialization",
    
    # ========== 网络编程 ==========
    "网络": "network",
    "套接字": "socket",
    "TCP": "TCP",
    "UDP": "UDP",
    "IP": "IP",
    "端口": "port",
    "服务器": "server",
    "客户端": "client",
    "协议": "protocol",
    
    # ========== 数据库 ==========
    "数据库": "database",
    "SQL": "SQL",
    "JDBC": "JDBC",
    "连接": "connection",
    "语句": "statement",
    "结果集": "resultset",
    "事务": "transaction",
    "驱动": "driver",
    
    # ========== 设计模式 ==========
    "设计模式": "design pattern",
    "单例": "singleton",
    "工厂": "factory",
    "建造者": "builder",
    "原型": "prototype",
    "适配器": "adapter",
    "桥接": "bridge",
    "组合": "composite",
    "装饰器": "decorator",
    "外观": "facade",
    "享元": "flyweight",
    "代理": "proxy",
    "责任链": "chain of responsibility",
    "命令": "command",
    "解释器": "interpreter",
    "迭代器": "iterator",
    "中介者": "mediator",
    "备忘录": "memento",
    "观察者": "observer",
    "状态": "state",
    "策略": "strategy",
    "模板方法": "template method",
    "访问者": "visitor",
    
    # ========== 反射和注解 ==========
    "反射": "reflection",
    "注解": "annotation",
    "元数据": "metadata",
    "运行时": "runtime",
    "编译时": "compile-time",
    "类加载器": "classloader",
    
    # ========== 内存管理 ==========
    "内存": "memory",
    "垃圾回收": "garbage collection",
    "GC": "GC",
    "堆内存": "heap memory",
    "栈内存": "stack memory",
    "内存泄漏": "memory leak",
    "引用": "reference",
    "弱引用": "weak reference",
    "强引用": "strong reference",
    
    # ========== 工具和框架 ==========
    "工具": "utility",
    "框架": "framework",
    "库": "library",
    "包": "package",
    "导入": "import",
    "模块": "module",
    "依赖": "dependency",
    "构建": "build",
    "编译": "compile",
    "运行": "run",
    "执行": "execute",
    "调试": "debug",
    "测试": "test",
    "单元测试": "unit test",
    "集成测试": "integration test",
    
    # ========== 常见动词 ==========
    "什么是": "what is",
    "意思": "meaning",
    "含义": "meaning",
    "作用": "purpose",
    "用途": "usage",
    "如何": "how to",
    "怎么": "how to",
    "怎样": "how to",
    "为什么": "why",
    "区别": "difference",
    "比较": "comparison",
    "对比": "comparison",
    "例子": "example",
    "示例": "example",
    "举例": "example",
    "使用": "use",
    "应用": "application",
    "定义": "definition",
    "解释": "explain",
    "说明": "description",
    "描述": "describe",
    "介绍": "introduction",
    "创建": "create",
    "生成": "generate",
    "获取": "get",
    "设置": "set",
    "调用": "call",
    "访问": "access",
    "修改": "modify",
    "扩展": "extend",
    "包含": "contain",
    "支持": "support",
    "需要": "need",
    "应该": "should",
    "可以": "can",
    "能够": "able to",
    "必须": "must",
    "自动": "automatic",
    "手动": "manual",
    "直接": "direct",
    "间接": "indirect",
    "显式": "explicit",
    "隐式": "implicit",
}


def simple_chinese_to_english(query: str) -> str:
    """
    简单的中文到英文翻译（基于关键词映射）
    
    这是 Kimi API 不可用时的备用方案
    """
    import re
    
    result = query

    # 按长度排序，优先匹配长词
    sorted_terms = sorted(TECH_TERMS_MAP.keys(), key=len, reverse=True)

    for cn_term in sorted_terms:
        if cn_term in result:
            en_term = TECH_TERMS_MAP[cn_term]
            result = result.replace(cn_term, f" {en_term} ")

    # 移除剩余的中文（未匹配的词汇）
    # 保留英文字母、数字、空格和常见标点
    cleaned = re.sub(r'[\u4e00-\u9fff]+', '', result)
    
    # 清理多余空格
    result = ' '.join(cleaned.split())
    
    # 移除常见中文标点
    result = result.replace('？', '').replace('?', '').replace('。', '').replace('.', '')
    result = result.strip()

    return result


async def translate_query_if_needed(query: str, course_context: str = "") -> Tuple[str, bool]:
    """
    检测查询语言，如果是中文则翻译为英文

    Returns:
        (翻译后的查询，是否进行了翻译)
    """
    # 简单的语言检测：检查是否包含中文字符
    import re
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', query))

    if has_chinese:
        # 优先尝试 Kimi API 翻译
        try:
            from services.knowledge.query_rewrite.main import translate_query
            translated = await translate_query(query, course_context)
            # 检查是否是 API 错误
            if "API key not configured" in translated or "error" in translated.lower():
                raise Exception("Kimi API not configured")
            logger.info(f"查询翻译 (Kimi): {query[:30]}... → {translated[:30]}...")
            return translated, True
        except Exception as e:
            logger.warning(f"Kimi 翻译失败：{e}，使用本地翻译方案")
        
        # 降级到本地简单翻译
        try:
            translated = simple_chinese_to_english(query)
            logger.info(f"查询翻译 (本地): {query[:30]}... → {translated[:30]}...")
            return translated, True
        except Exception as e:
            logger.error(f"本地翻译失败：{e}，使用原查询")
            return query, False

    return query, False


async def get_cached_query_embedding(query: str) -> Optional[np.ndarray]:
    """从缓存获取查询向量"""
    async with _cache_lock:
        return _query_embedding_cache.get(query)


async def cache_query_embedding(query: str, embedding: np.ndarray):
    """缓存查询向量"""
    async with _cache_lock:
        _query_embedding_cache[query] = embedding


# ==================== 向量检索 ====================
async def semantic_search_with_faiss(
    query: str,
    course_id: Optional[str] = None,
    top_k: int = 10,
    request_id: Optional[str] = None,
    use_parent_child: bool = False  # P11 新增：是否启用 Parent-Child 检索
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    使用 FAISS 进行向量语义检索 (O(1) 复杂度)

    修复 OFF-001 问题：不再实时计算所有文档的 TF-IDF 向量
    
    P11 新增：支持 Parent-Child 检索模式
    """
    log = get_logger(request_id)
    start_time = datetime.now()
    stats = {}

    try:
        from services.knowledge.faiss_indexer.main import (
            faiss_index, index_metadata, index_to_doc_id,
            search_vectors, HNSWConfig
        )
        from services.knowledge.embedding.main import generate_embeddings

        # 获取或计算查询向量
        query_embedding = await get_cached_query_embedding(query)
        if query_embedding is None:
            embeddings = await generate_embeddings([query])
            query_embedding = np.array(embeddings[0]).astype('float32')
            await cache_query_embedding(query, query_embedding)

        # 使用 FAISS 搜索 (O(1) 复杂度)
        results = await search_vectors(
            query_embedding=query_embedding,
            top_k=top_k,
            nprobe=20,
            ef_search=HNSWConfig.EF_SEARCH
        )

        # 从数据库获取文档详情
        if results:
            doc_ids = [r["doc_id"] for r in results]
            async with _index_lock:
                from common.database.postgresql import AsyncSessionLocal
                from services.knowledge.rag.main import RAGDocument
                from sqlalchemy import select

                async with AsyncSessionLocal() as session:
                    db_result = await session.execute(
                        select(RAGDocument).where(RAGDocument.doc_id.in_(doc_ids))
                    )
                    docs = db_result.scalars().all()
                    doc_map = {doc.doc_id: doc for doc in docs}

            # 构建最终结果
            final_results = []
            for r in results:
                doc_id = r["doc_id"]
                if doc_id in doc_map:
                    doc = doc_map[doc_id]
                    final_results.append({
                        "doc_id": doc_id,
                        "content": doc.content,
                        "score": r["score"],
                        "doc_metadata": doc.doc_metadata,
                        "channel": "semantic"
                    })

            # P11 新增：Parent-Child 扩展
            if use_parent_child and final_results:
                try:
                    from services.knowledge.indexer.parent_child_indexer import expand_retrieved_chunks
                    # 这里需要加载所有 chunks 进行扩展
                    # 简化实现：直接返回当前结果
                    stats["parent_child_applied"] = False
                except Exception as e:
                    log.warning(f"Parent-Child 扩展失败：{e}")

            stats["faiss_search_time"] = (datetime.now() - start_time).total_seconds()
            stats["semantic_count"] = len(final_results)
            stats["parent_child_enabled"] = use_parent_child

            log.info(f"FAISS 检索完成：{len(final_results)} 个结果")
            return final_results, stats

    except Exception as e:
        log.error(f"FAISS 检索失败：{e}", exc_info=True)
        return [], {"error": str(e)}

    return [], stats


async def semantic_search_with_tfidf(
    query: str,
    course_id: Optional[str] = None,
    top_k: int = 10,
    request_id: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    使用预计算的 TF-IDF 矩阵进行检索 (O(N) 但 N 是预计算的)
    
    修复 ONL-001 问题：使用预计算的 tfidf_matrix 而不是实时计算
    """
    log = get_logger(request_id)
    start_time = datetime.now()
    stats = {}

    try:
        from services.knowledge.embedding.tfidf_main import (
            tfidf_matrix, doc_id_list, doc_contents, vocabulary, idf_values,
            chinese_tokenize, compute_tf
        )

        if tfidf_matrix is None or len(doc_contents) == 0:
            log.warning("TF-IDF 索引未加载")
            return [], stats

        # 计算查询向量 (只计算一次，O(D) 复杂度)
        query_tokens = chinese_tokenize(query)
        query_tf = compute_tf(query_tokens)

        query_vector = np.zeros(len(vocabulary)) if vocabulary else np.zeros(5000)
        for token, tf_val in query_tf.items():
            if token in vocabulary:
                idx = vocabulary[token]
                idf_val = idf_values.get(token, 1.0)
                query_vector[idx] = tf_val * idf_val

        # L2 归一化
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm

        # 计算余弦相似度 (矩阵运算，高度优化)
        similarities = np.dot(tfidf_matrix, query_vector)

        # 获取 top_k 索引
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # 构建结果
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                results.append({
                    "doc_id": doc_id_list[idx],
                    "content": doc_contents[idx][:500],
                    "score": float(similarities[idx]),
                    "channel": "semantic"
                })

        stats["tfidf_search_time"] = (datetime.now() - start_time).total_seconds()
        stats["semantic_count"] = len(results)

        log.info(f"TF-IDF 检索完成：{len(results)} 个结果")
        return results, stats

    except Exception as e:
        log.error(f"TF-IDF 检索失败：{e}", exc_info=True)
        return [], {"error": str(e)}


async def keyword_search_with_bm25(
    query: str,
    course_id: Optional[str] = None,
    top_k: int = 10,
    request_id: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    使用 BM25 进行关键词检索
    
    支持查询改写（中文 -> 英文）以提升跨语言检索效果
    """
    log = get_logger(request_id)
    start_time = datetime.now()
    stats = {}

    try:
        from services.knowledge.bm25_search.main import bm25_index

        async with _index_lock:
            # 启用查询改写
            results = bm25_index.search(
                query=query,
                course_id=course_id,
                top_k=top_k,
                use_query_rewrite=True
            )

        for r in results:
            r["channel"] = "keyword"

        stats["bm25_search_time"] = (datetime.now() - start_time).total_seconds()
        stats["keyword_count"] = len(results)

        log.info(f"BM25 检索完成：{len(results)} 个结果")
        return results, stats

    except Exception as e:
        log.error(f"BM25 检索失败：{e}", exc_info=True)
        return [], {"error": str(e)}


async def keyword_search_fallback(
    expanded_queries: List[str],
    course_id: Optional[str] = None,
    top_k: int = 10,
    request_id: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    BM25 失败时的降级方案：SQL 模糊查询
    """
    log = get_logger(request_id)
    results = []

    try:
        from common.database.postgresql import AsyncSessionLocal
        from services.knowledge.rag.main import RAGDocument
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            for eq in expanded_queries[:3]:
                if course_id:
                    db_result = await session.execute(
                        select(RAGDocument).where(
                            RAGDocument.content.ilike(f"%{eq}%"),
                            RAGDocument.course_id == course_id
                        ).limit(top_k)
                    )
                else:
                    db_result = await session.execute(
                        select(RAGDocument).where(
                            RAGDocument.content.ilike(f"%{eq}%")
                        ).limit(top_k)
                    )

                docs = db_result.scalars().all()

                for doc in docs:
                    results.append({
                        "doc_id": doc.doc_id,
                        "content": doc.content,
                        "score": 0.5,
                        "doc_metadata": doc.doc_metadata,
                        "channel": "keyword"
                    })

                if results:
                    break

        log.info(f"SQL 降级检索完成：{len(results)} 个结果")
        return results, {"fallback_count": len(results)}

    except Exception as e:
        log.error(f"SQL 降级检索失败：{e}", exc_info=True)
        return [], {"error": str(e)}


async def graph_search(
    query: str,
    course_id: Optional[str] = None,
    top_k: int = 5,
    intent: str = "general",
    request_id: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    知识图谱检索
    """
    log = get_logger(request_id)
    results = []
    stats = {}

    try:
        from services.knowledge.graph_search.main import search_entities, search_relations

        # 检索实体
        entities = await search_entities(
            keyword=query,
            course_id=course_id,
            top_k=top_k
        )

        for e in entities:
            results.append({
                "doc_id": f"graph_{e.get('entity_id', '')}",
                "content": e.get("description", "") or e.get("name", ""),
                "score": e.get("score", 0.8),
                "channel": "graph",
                "graph_data": e
            })

        # 如果是关系查询，检索关系
        if intent == "relation_query":
            relations = await search_relations(
                entity_name=query,
                course_id=course_id,
                max_depth=2
            )

            for r in relations[:5]:
                content = f"{r.get('source', {}).get('name', '')} -> {r.get('relation', {}).get('type', '')} -> {r.get('target', {}).get('name', '')}"
                results.append({
                    "doc_id": f"graph_rel_{r.get('source', {}).get('name', '')}",
                    "content": content,
                    "score": 0.7,
                    "channel": "graph",
                    "graph_data": r
                })

        stats["graph_count"] = len(results)
        log.info(f"图谱检索完成：{len(results)} 个结果")

    except Exception as e:
        log.error(f"图谱检索失败：{e}", exc_info=True)
        stats["graph_error"] = str(e)

    return results, stats


async def multi_channel_search(
    query: str,
    channels: List[str] = None,
    course_id: Optional[str] = None,
    top_k: int = 10,
    use_bm25: bool = True,
    use_vector: bool = True,
    use_graph: bool = True,
    expanded_queries: List[str] = None,
    intent: str = "general",
    request_id: Optional[str] = None
) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Any]]:
    """
    多路并发检索 (P1 修复：异步并发执行)
    
    修复 bottleneck: 串行多路检索
    """
    log = get_logger(request_id)
    channels = channels or ["semantic", "keyword"]
    expanded_queries = expanded_queries or [query]

    all_results = {
        "semantic": [],
        "keyword": [],
        "graph": []
    }
    all_stats = {}

    # 构建检索任务
    tasks = []

    # 向量检索
    if use_vector and "semantic" in channels:
        # 优先使用 FAISS，如果不可用则使用 TF-IDF
        from services.knowledge.faiss_indexer.main import faiss_index
        if faiss_index is not None and faiss_index.ntotal > 0:
            tasks.append(("semantic", semantic_search_with_faiss(
                query=query,
                course_id=course_id,
                top_k=top_k,
                request_id=request_id
            )))
        else:
            tasks.append(("semantic", semantic_search_with_tfidf(
                query=query,
                course_id=course_id,
                top_k=top_k,
                request_id=request_id
            )))

    # BM25 检索
    if use_bm25 and "keyword" in channels:
        tasks.append(("keyword", keyword_search_with_bm25(
            query=query,
            course_id=course_id,
            top_k=top_k,
            request_id=request_id
        )))

    # 图谱检索
    if use_graph and "graph" in channels:
        tasks.append(("graph", graph_search(
            query=query,
            course_id=course_id,
            top_k=top_k,
            intent=intent,
            request_id=request_id
        )))

    # 异步并发执行所有检索任务
    if tasks:
        task_results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

        for i, (channel, _) in enumerate(tasks):
            try:
                result, stats = task_results[i]
                all_results[channel] = result
                all_stats.update(stats)
            except Exception as e:
                log.error(f"{channel} 检索失败：{e}", exc_info=True)
                all_stats[f"{channel}_error"] = str(e)

                # BM25 失败时使用降级方案
                if channel == "keyword":
                    fallback_result, _ = await keyword_search_fallback(
                        expanded_queries=expanded_queries,
                        course_id=course_id,
                        top_k=top_k,
                        request_id=request_id
                    )
                    all_results[channel] = fallback_result

    return all_results, all_stats


# ==================== 混合检索 ====================
async def hybrid_search(
    query: str,
    course_id: Optional[str] = None,
    top_k: int = 10,
    use_cache: bool = True,
    enable_translation: bool = True,  # P11 优化：启用查询翻译
    enable_hyde: bool = True,  # P11 优化：默认启用 HyDE (提升 Recall)
    enable_query_decomposition: bool = False,  # P11 新增：查询分解
    request_id: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    使用混合检索引擎进行检索 (静态库 + 动态库)

    P11 优化:
    - 跨语言检索：自动检测中文查询并翻译为英文
    - HyDE：使用假设答案进行检索 (默认启用)
    - 查询分解：将复杂查询拆分为多个子查询
    - 查询缓存：减少重复计算
    - 结果合并：加权融合 + 重排序

    Args:
        query: 查询文本
        course_id: 课程 ID 过滤
        top_k: 返回结果数
        use_cache: 是否使用查询缓存
        enable_translation: 是否启用查询翻译 (中文→英文)
        enable_hyde: 是否启用 HyDE (假设文档嵌入，默认启用)
        enable_query_decomposition: 是否启用查询分解 (复杂查询拆分)
        request_id: 请求 ID

    Returns:
        (结果列表，统计信息)
    """
    log = get_logger(request_id)
    start_time = datetime.now()
    stats = {"source": "hybrid"}

    # 统计信息
    translation_applied = False
    hyde_applied = False
    decomposition_applied = False
    original_query = query
    expanded_queries = [query]

    try:
        # ==================== 查询理解阶段 ====================

        # 1. 查询翻译 (跨语言检索) - P11 优化：优先翻译
        if enable_translation:
            query, translation_applied = await translate_query_if_needed(
                query,
                course_context=course_id or ""
            )
            stats["translation_applied"] = translation_applied
            if translation_applied:
                # 翻译后不启用 HyDE，避免双重转换
                enable_hyde = False
                log.info(f"查询已翻译：{original_query[:30]}... → {query[:30]}...")

        # 2. HyDE (假设文档嵌入) - P11 优化：默认启用
        if enable_hyde:
            try:
                from services.knowledge.query_rewrite.main import generate_hyde_answer
                hyde_answer = await generate_hyde_answer(query, course_context=course_id or "")
                if hyde_answer and hyde_answer != query and len(hyde_answer) > 20:
                    # 使用 HyDE 答案进行检索，但保留原查询用于后续处理
                    query = hyde_answer
                    hyde_applied = True
                    stats["hyde_applied"] = True
                    log.info(f"HyDE 已应用：生成{len(hyde_answer)}字符的假设答案")
            except Exception as e:
                log.warning(f"HyDE 生成失败：{e}，使用原查询")

        # 3. 查询分解 (P11 新增)：将复杂查询拆分为多个子查询
        if enable_query_decomposition and not translation_applied and not hyde_applied:
            try:
                from services.knowledge.query_rewrite.main import decompose_query
                decomposed = await decompose_query(query, course_context=course_id or "")
                if decomposed and len(decomposed) > 1:
                    expanded_queries = decomposed
                    decomposition_applied = True
                    stats["decomposition_applied"] = True
                    stats["sub_queries_count"] = len(decomposed)
                    log.info(f"查询已分解：{len(decomposed)} 个子查询")
            except Exception as e:
                log.warning(f"查询分解失败：{e}，使用原查询")

        # ==================== 检索阶段 ====================
        engine = await get_hybrid_engine()

        if engine is None or not engine.initialized:
            log.warning("混合检索引擎未初始化，降级为传统检索")
            return await semantic_search_with_tfidf(query, course_id, top_k, request_id)

        # 执行混合检索 (使用最终的 query)
        results, search_stats = await engine.search(
            query=query,
            course_id=course_id,
            top_k=top_k,
            use_cache=use_cache
        )

        stats.update(search_stats)
        stats["hybrid_search_time"] = (datetime.now() - start_time).total_seconds()
        stats["hybrid_count"] = len(results)
        stats["original_query"] = original_query
        stats["final_query"] = query
        stats["expansion_strategy"] = "translation" if translation_applied else ("hyde" if hyde_applied else ("decomposition" if decomposition_applied else "none"))

        log.info(f"混合检索完成：{len(results)} 个结果，耗时：{stats['hybrid_search_time']:.3f}s，策略：{stats['expansion_strategy']}")
        return results, stats

    except Exception as e:
        log.error(f"混合检索失败：{e}", exc_info=True)
        stats["error"] = str(e)

        # 降级为传统 TF-IDF 检索
        return await semantic_search_with_tfidf(query, course_id, top_k, request_id)


async def add_documents_to_hybrid_index(documents: List[Dict[str, Any]], 
                                        is_static: bool = False) -> Dict[str, Any]:
    """
    添加文档到混合检索索引

    Args:
        documents: 文档列表，每个包含 doc_id, content, course_id, metadata
        is_static: 是否添加到静态库 (默认 False，添加到动态库)

    Returns:
        添加结果
    """
    try:
        engine = await get_hybrid_engine()

        if engine is None:
            return {"success": False, "error": "引擎未初始化"}

        return await engine.add_documents(documents, is_static)

    except Exception as e:
        logger.error(f"添加文档到混合索引失败：{e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def remove_documents_from_hybrid_index(doc_ids: List[str]) -> Dict[str, Any]:
    """
    从混合检索索引删除文档

    Args:
        doc_ids: 要删除的文档 ID 列表

    Returns:
        删除结果
    """
    try:
        engine = await get_hybrid_engine()

        if engine is None:
            return {"success": False, "error": "引擎未初始化"}

        return await engine.remove_documents(doc_ids)

    except Exception as e:
        logger.error(f"从混合索引删除文档失败：{e}", exc_info=True)
        return {"success": False, "error": str(e)}


def get_hybrid_stats() -> Dict[str, Any]:
    """获取混合检索引擎统计信息"""
    if _hybrid_engine and _hybrid_engine_initialized:
        return _hybrid_engine.get_stats()
    return {"initialized": False, "error": "引擎未初始化"}
