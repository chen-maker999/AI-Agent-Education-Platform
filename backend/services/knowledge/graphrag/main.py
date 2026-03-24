"""
GraphRAG 服务 - 图结构增强向量表示

P11 优化:
1. 图结构增强向量表示
2. 图 + 向量联合索引
3. 关系推理增强检索
4. 子图匹配
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graphrag", tags=["GraphRAG"])


# ==================== 数据模型 ====================

class GraphRAGRequest(BaseModel):
    """GraphRAG 请求"""
    query: str
    course_id: Optional[str] = None
    top_k: int = 10
    use_graph_enhancement: bool = True
    graph_weight: float = 0.3  # 图谱增强权重
    max_hops: int = 2  # 最大跳数


class GraphRAGResponse(BaseModel):
    """GraphRAG 响应"""
    query: str
    results: List[Dict[str, Any]]
    total: int
    graph_enhanced: bool
    graph_stats: Dict[str, Any]
    processing_time_ms: float


class GraphNode:
    """图节点"""
    def __init__(self, node_id: str, name: str, node_type: str, embedding: Optional[np.ndarray] = None):
        self.node_id = node_id
        self.name = name
        self.node_type = node_type
        self.embedding = embedding
        self.neighbors: List[GraphNode] = []
        self.relations: List[GraphRelation] = []


class GraphRelation:
    """图关系"""
    def __init__(self, source: str, target: str, relation_type: str, weight: float = 1.0):
        self.source = source
        self.target = target
        self.relation_type = relation_type
        self.weight = weight


# ==================== GraphRAG 核心逻辑 ====================

class GraphRAGEngine:
    """
    GraphRAG 引擎
    
    将知识图谱结构与向量检索融合:
    1. 使用图结构增强文档向量表示
    2. 通过关系传播更新节点嵌入
    3. 联合检索向量相似度和图相关性
    """
    
    def __init__(self, graph_weight: float = 0.3):
        self.graph_weight = graph_weight
        self.nodes: Dict[str, GraphNode] = {}
        self.relations: List[GraphRelation] = []
        self.initialized = False
    
    def add_node(self, node_id: str, name: str, node_type: str, 
                 embedding: Optional[np.ndarray] = None):
        """添加图节点"""
        node = GraphNode(node_id, name, node_type, embedding)
        self.nodes[node_id] = node
    
    def add_relation(self, source: str, target: str, relation_type: str, 
                     weight: float = 1.0):
        """添加图关系"""
        relation = GraphRelation(source, target, relation_type, weight)
        self.relations.append(relation)
        
        # 更新邻居关系
        if source in self.nodes and target in self.nodes:
            self.nodes[source].neighbors.append(self.nodes[target])
            self.nodes[target].neighbors.append(self.nodes[source])
            self.nodes[source].relations.append(relation)
    
    def propagate_embeddings(self, iterations: int = 2):
        """
        传播嵌入：使用图结构增强节点向量表示
        
        通过图神经网络思想，将邻居节点的信息聚合到当前节点
        """
        for _ in range(iterations):
            for node_id, node in self.nodes.items():
                if node.embedding is None:
                    continue
                
                # 收集邻居嵌入
                neighbor_embeddings = []
                neighbor_weights = []
                
                for neighbor in node.neighbors:
                    if neighbor.embedding is not None:
                        neighbor_embeddings.append(neighbor.embedding)
                        # 找到对应的关系权重
                        for rel in node.relations:
                            if rel.target == neighbor.node_id or rel.source == neighbor.node_id:
                                neighbor_weights.append(rel.weight)
                                break
                        else:
                            neighbor_weights.append(1.0)
                
                if neighbor_embeddings:
                    # 加权平均邻居嵌入
                    neighbor_embeddings = np.array(neighbor_embeddings)
                    neighbor_weights = np.array(neighbor_weights)
                    neighbor_weights = neighbor_weights / (neighbor_weights.sum() + 1e-8)
                    
                    aggregated_embedding = np.average(neighbor_embeddings, axis=0, weights=neighbor_weights)
                    
                    # 融合原始嵌入和聚合嵌入
                    node.enhanced_embedding = (
                        (1 - self.graph_weight) * node.embedding + 
                        self.graph_weight * aggregated_embedding
                    )
                else:
                    node.enhanced_embedding = node.embedding
        
        self.initialized = True
        logger.info(f"GraphRAG 嵌入传播完成，节点数：{len(self.nodes)}")
    
    def graphrag_search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        max_hops: int = 2
    ) -> List[Dict[str, Any]]:
        """
        GraphRAG 联合检索
        
        1. 计算查询向量与所有节点的相似度
        2. 添加图结构增强分数 (基于邻居关系)
        3. 返回融合后的 Top-K 结果
        """
        if not self.initialized:
            self.propagate_embeddings()
        
        scores = []
        
        for node_id, node in self.nodes.items():
            # 1. 向量相似度
            if node.enhanced_embedding is not None:
                vector_score = self._cosine_similarity(query_embedding, node.enhanced_embedding)
            elif node.embedding is not None:
                vector_score = self._cosine_similarity(query_embedding, node.embedding)
            else:
                vector_score = 0.0
            
            # 2. 图结构增强分数
            graph_score = self._calculate_graph_score(node, max_hops)
            
            # 3. 融合分数
            final_score = (1 - self.graph_weight) * vector_score + self.graph_weight * graph_score
            
            scores.append({
                "node_id": node_id,
                "name": node.name,
                "node_type": node.node_type,
                "vector_score": vector_score,
                "graph_score": graph_score,
                "final_score": final_score,
                "neighbor_count": len(node.neighbors),
                "relation_count": len(node.relations)
            })
        
        # 按最终分数排序
        scores.sort(key=lambda x: x["final_score"], reverse=True)
        
        return scores[:top_k]
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def _calculate_graph_score(self, node: GraphNode, max_hops: int) -> float:
        """
        计算图结构分数
        
        基于:
        1. 节点度 (邻居数量)
        2. 关系数量
        3. 多跳可达性
        """
        # 1. 度分数
        degree_score = len(node.neighbors) / max(1, max(len(n.neighbors) for n in self.nodes.values()))
        
        # 2. 关系分数
        relation_score = len(node.relations) / max(1, max(len(n.relations) for n in self.nodes.values()))
        
        # 3. 多跳可达性分数
        reachable_nodes = self._get_reachable_nodes(node, max_hops)
        reachable_score = len(reachable_nodes) / len(self.nodes)
        
        # 加权平均
        graph_score = 0.4 * degree_score + 0.3 * relation_score + 0.3 * reachable_score
        
        return graph_score
    
    def _get_reachable_nodes(self, start_node: GraphNode, max_hops: int) -> set:
        """获取从起始节点 max_hops 跳内可达的所有节点"""
        visited = {start_node.node_id}
        current_level = {start_node}
        
        for _ in range(max_hops):
            next_level = set()
            for node in current_level:
                for neighbor in node.neighbors:
                    if neighbor.node_id not in visited:
                        visited.add(neighbor.node_id)
                        next_level.add(neighbor)
            current_level = next_level
            if not current_level:
                break
        
        return visited
    
    def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        return {
            "node_count": len(self.nodes),
            "relation_count": len(self.relations),
            "initialized": self.initialized,
            "graph_weight": self.graph_weight,
            "avg_neighbors": sum(len(n.neighbors) for n in self.nodes.values()) / max(1, len(self.nodes)),
            "avg_relations": sum(len(n.relations) for n in self.nodes.values()) / max(1, len(self.nodes))
        }


# ==================== 全局引擎实例 ====================

_graphrag_engine: Optional[GraphRAGEngine] = None


def get_graphrag_engine() -> GraphRAGEngine:
    """获取或创建 GraphRAG 引擎实例"""
    global _graphrag_engine
    
    if _graphrag_engine is None:
        _graphrag_engine = GraphRAGEngine(graph_weight=0.3)
    
    return _graphrag_engine


# ==================== 与 Neo4j 集成 ====================

async def build_graphrag_from_neo4j(course_id: Optional[str] = None) -> GraphRAGEngine:
    """
    从 Neo4j 构建 GraphRAG 引擎
    
    读取图谱中的实体和关系，构建增强索引
    """
    engine = get_graphrag_engine()
    
    try:
        from services.knowledge.graph_search.main import neo4j_driver, neo4j_available
        
        if not neo4j_available:
            logger.warning("Neo4j 不可用，使用空 GraphRAG 引擎")
            return engine
        
        from neo4j import GraphDatabase
        
        with neo4j_driver.session() as session:
            # 1. 读取所有实体
            if course_id:
                query = """
                MATCH (n:KnowledgePoint {course_id: $course_id})
                RETURN n.node_id as node_id, n.name as name, n.node_type as node_type
                """
                result = session.run(query, course_id=course_id)
            else:
                query = """
                MATCH (n:KnowledgePoint)
                RETURN n.node_id as node_id, n.name as name, n.node_type as node_type
                """
                result = session.run(query)
            
            entities = list(result.data())
            
            # 2. 读取所有关系
            if course_id:
                rel_query = """
                MATCH (s)-[r]->(t)
                WHERE s.course_id = $course_id
                RETURN s.node_id as source, t.node_id as target, type(r) as relation_type
                """
                rel_result = session.run(rel_query, course_id=course_id)
            else:
                rel_query = """
                MATCH (s)-[r]->(t)
                RETURN s.node_id as source, t.node_id as target, type(r) as relation_type
                """
                rel_result = session.run(rel_query)
            
            relations = list(rel_result.data())
            
            # 3. 添加到引擎
            for entity in entities:
                # 获取实体嵌入
                embedding = await _get_entity_embedding(entity["node_id"])
                
                engine.add_node(
                    node_id=entity["node_id"],
                    name=entity["name"],
                    node_type=entity["node_type"],
                    embedding=embedding
                )
            
            for rel in relations:
                engine.add_relation(
                    source=rel["source"],
                    target=rel["target"],
                    relation_type=rel["relation_type"]
                )
            
            # 4. 传播嵌入
            engine.propagate_embeddings()
            
            logger.info(f"GraphRAG 引擎构建完成：{len(entities)} 个实体，{len(relations)} 个关系")
    
    except Exception as e:
        logger.error(f"从 Neo4j 构建 GraphRAG 失败：{e}")
    
    return engine


async def _get_entity_embedding(node_id: str) -> Optional[np.ndarray]:
    """获取实体的向量嵌入"""
    try:
        from services.knowledge.embedding.main import generate_embeddings
        
        # 从数据库获取实体名称
        from services.knowledge.graph_search.main import neo4j_driver
        
        with neo4j_driver.session() as session:
            result = session.run(
                "MATCH (n {node_id: $node_id}) RETURN n.name as name",
                node_id=node_id
            )
            record = result.single()
            
            if record:
                embeddings = await generate_embeddings([record["name"]])
                return np.array(embeddings[0]).astype('float32')
    
    except Exception as e:
        logger.error(f"获取实体嵌入失败：{e}")
    
    return None


# ==================== GraphRAG 检索接口 ====================

async def graphrag_search(
    query: str,
    course_id: Optional[str] = None,
    top_k: int = 10,
    use_graph_enhancement: bool = True
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    GraphRAG 检索
    
    融合向量检索和图结构检索
    """
    start_time = datetime.now()
    stats = {}
    
    # 1. 获取查询向量
    try:
        from services.knowledge.embedding.main import generate_embeddings
        embeddings = await generate_embeddings([query])
        query_embedding = np.array(embeddings[0]).astype('float32')
    except Exception as e:
        logger.error(f"获取查询向量失败：{e}")
        return [], {"error": str(e)}
    
    # 2. 获取/构建 GraphRAG 引擎
    engine = get_graphrag_engine()
    
    if not engine.initialized:
        logger.info("GraphRAG 引擎未初始化，尝试从 Neo4j 构建...")
        engine = await build_graphrag_from_neo4j(course_id)
    
    # 3. 执行 GraphRAG 检索
    if use_graph_enhancement and engine.initialized:
        results = engine.graphrag_search(
            query_embedding=query_embedding,
            top_k=top_k
        )
        stats["graph_enhanced"] = True
    else:
        # 降级为普通向量检索
        results = engine.graphrag_search(
            query_embedding=query_embedding,
            top_k=top_k
        )
        stats["graph_enhanced"] = False
    
    stats["engine_stats"] = engine.get_stats()
    stats["search_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000
    
    return results, stats


# ==================== API 端点 ====================

@router.post("/search", response_model=GraphRAGResponse)
async def graphrag_search_endpoint(request: GraphRAGRequest):
    """
    GraphRAG 检索接口
    
    融合知识图谱结构和向量检索
    """
    start_time = datetime.now()
    
    results, stats = await graphrag_search(
        query=request.query,
        course_id=request.course_id,
        top_k=request.top_k,
        use_graph_enhancement=request.use_graph_enhancement
    )
    
    processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    return GraphRAGResponse(
        query=request.query,
        results=results,
        total=len(results),
        graph_enhanced=stats.get("graph_enhanced", False),
        graph_stats=stats.get("engine_stats", {}),
        processing_time_ms=processing_time_ms
    )


@router.post("/build")
async def build_graphrag_index(course_id: Optional[str] = None):
    """从 Neo4j 构建 GraphRAG 索引"""
    engine = await build_graphrag_from_neo4j(course_id)
    
    return {
        "code": 200,
        "data": {
            "status": "success",
            "stats": engine.get_stats()
        }
    }


@router.get("/stats")
async def get_graphrag_stats():
    """获取 GraphRAG 引擎统计"""
    engine = get_graphrag_engine()
    
    return {
        "code": 200,
        "data": engine.get_stats()
    }


@router.post("/propagate")
async def propagate_embeddings(iterations: int = 2):
    """手动触发嵌入传播"""
    engine = get_graphrag_engine()
    engine.propagate_embeddings(iterations)
    
    return {
        "code": 200,
        "data": {
            "status": "success",
            "iterations": iterations,
            "stats": engine.get_stats()
        }
    }


# ==================== 便捷函数 ====================

async def search_with_graphrag(
    query: str,
    course_id: Optional[str] = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    便捷函数：GraphRAG 检索
    
    用于在其他服务中直接调用
    """
    results, _ = await graphrag_search(
        query=query,
        course_id=course_id,
        top_k=top_k,
        use_graph_enhancement=True
    )
    return results
