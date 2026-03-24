"""知识图谱检索服务 - Neo4j 图谱查询"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import os


router = APIRouter(prefix="/graph/search", tags=["Knowledge Graph Search"])


# Neo4j 客户端
neo4j_driver = None
neo4j_available = False


class GraphSearchRequest(BaseModel):
    """图谱搜索请求"""
    query: str
    course_id: Optional[str] = None
    search_type: str = "entity"  # entity, relation, path
    top_k: int = 10


class GraphSearchResponse(BaseModel):
    """图谱搜索响应"""
    query: str
    results: List[Dict[str, Any]]
    total: int
    search_type: str
    search_time: float


class GraphEntityRequest(BaseModel):
    """实体搜索请求"""
    entity_name: str
    entity_type: Optional[str] = "KnowledgePoint"
    course_id: Optional[str] = None
    top_k: int = 10


class GraphRelationRequest(BaseModel):
    """关系查询请求"""
    entity_name: str
    relation_types: Optional[List[str]] = None
    max_depth: int = 2
    course_id: Optional[str] = None


class GraphPathRequest(BaseModel):
    """路径查询请求"""
    from_entity: str
    to_entity: str
    max_depth: int = 5
    course_id: Optional[str] = None


def init_neo4j():
    """初始化 Neo4j 连接"""
    global neo4j_driver, neo4j_available
    
    try:
        from neo4j import GraphDatabase
        from common.core.config import settings
        
        uri = settings.get_neo4j_url()
        user = settings.NEO4J_USER
        password = settings.NEO4J_PASSWORD
        
        neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # 测试连接
        with neo4j_driver.session() as session:
            session.run("MATCH (n) RETURN count(n) LIMIT 1")
        
        neo4j_available = True
        print("Neo4j 连接成功")
        return True
    except Exception as e:
        print(f"Neo4j 初始化失败：{e}")
        neo4j_available = False
        return False


def close_neo4j():
    """关闭 Neo4j 连接"""
    global neo4j_driver
    if neo4j_driver:
        neo4j_driver.close()


async def search_entities(
    keyword: str,
    entity_type: str = "KnowledgePoint",
    course_id: Optional[str] = None,
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    实体搜索
    
    Args:
        keyword: 实体名称关键词
        entity_type: 实体类型
        course_id: 课程 ID 过滤
        top_k: 返回数量
    
    Returns:
        实体列表
    """
    if not neo4j_available:
        return []
    
    try:
        with neo4j_driver.session() as session:
            # 构建查询
            if course_id:
                # 按课程过滤
                query = """
                MATCH (k:%s)
                WHERE k.name CONTAINS $keyword OR k.description CONTAINS $keyword
                OPTIONAL MATCH (c:Course {id: $course_id})-[:CONTAINS]->(k)
                WHERE c IS NOT NULL OR $course_id IS NULL
                RETURN k, 1.0 as score
                LIMIT $limit
                """ % entity_type
                result = session.run(
                    query,
                    keyword=keyword,
                    course_id=course_id,
                    limit=top_k
                )
            else:
                query = """
                MATCH (k:%s)
                WHERE k.name CONTAINS $keyword OR k.description CONTAINS $keyword
                RETURN k, 1.0 as score
                LIMIT $limit
                """ % entity_type
                result = session.run(query, keyword=keyword, limit=top_k)
            
            results = []
            for record in result:
                node = record["k"]
                results.append({
                    "type": "entity",
                    "entity_id": node.id,
                    "entity_type": list(node.labels)[0] if node.labels else "Unknown",
                    "name": node.get("name", ""),
                    "description": node.get("description", ""),
                    "score": record["score"],
                    "properties": dict(node)
                })
            
            return results
    except Exception as e:
        print(f"图谱实体搜索失败：{e}")
        return []


async def search_relations(
    entity_name: str,
    relation_types: Optional[List[str]] = None,
    max_depth: int = 2,
    course_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    关系查询 - 查找实体的关联节点
    
    Args:
        entity_name: 实体名称
        relation_types: 关系类型过滤
        max_depth: 最大深度
        course_id: 课程 ID 过滤
    
    Returns:
        关系列表
    """
    if not neo4j_available:
        return []
    
    try:
        with neo4j_driver.session() as session:
            # 构建关系类型过滤
            rel_filter = ""
            if relation_types:
                rel_types_str = "|".join(relation_types)
                rel_filter = f"-[r:{rel_types_str}]"
            else:
                rel_filter = "-[r]"
            
            # 查询关系
            query = f"""
            MATCH (k:KnowledgePoint {{name: $entity_name}})
            MATCH (k){rel_filter}*(..{max_depth})-(related)
            RETURN k, r, related
            LIMIT $limit
            """
            
            result = session.run(query, entity_name=entity_name, limit=50)
            
            results = []
            for record in result:
                source = record["k"]
                rel = record.get("r")
                target = record["related"]
                
                results.append({
                    "type": "relation",
                    "source": {
                        "name": source.get("name", ""),
                        "type": list(source.labels)[0] if source.labels else "Unknown"
                    },
                    "relation": {
                        "type": list(rel.types)[0] if rel and rel.types else "UNKNOWN",
                        "properties": dict(rel) if rel else {}
                    },
                    "target": {
                        "name": target.get("name", ""),
                        "type": list(target.labels)[0] if target.labels else "Unknown",
                        "properties": dict(target)
                    }
                })
            
            return results
    except Exception as e:
        print(f"图谱关系搜索失败：{e}")
        return []


async def search_path(
    from_entity: str,
    to_entity: str,
    max_depth: int = 5
) -> List[Dict[str, Any]]:
    """
    路径查询 - 查找两个实体之间的最短路径
    
    Args:
        from_entity: 起始实体
        to_entity: 目标实体
        max_depth: 最大深度
    
    Returns:
        路径列表
    """
    if not neo4j_available:
        return []
    
    try:
        with neo4j_driver.session() as session:
            query = """
            MATCH path = shortestPath(
                (k1:KnowledgePoint {name: $from})-[*..$max_depth]-(k2:KnowledgePoint {name: $to})
            )
            RETURN path
            LIMIT 10
            """
            
            result = session.run(
                query,
                from_=from_entity,
                to=to_entity,
                max_depth=max_depth
            )
            
            results = []
            for record in result:
                path = record["path"]
                nodes = path.nodes
                rels = path.relationships
                
                results.append({
                    "type": "path",
                    "nodes": [
                        {
                            "name": n.get("name", ""),
                            "type": list(n.labels)[0] if n.labels else "Unknown"
                        }
                        for n in nodes
                    ],
                    "relationships": [
                        {
                            "type": list(r.types)[0] if r and r.types else "UNKNOWN"
                        }
                        for r in rels
                    ]
                })
            
            return results
    except Exception as e:
        print(f"图谱路径搜索失败：{e}")
        return []


async def get_prerequisites(knowledge_point: str, max_depth: int = 3) -> List[Dict]:
    """获取知识点的前置知识"""
    if not neo4j_available:
        return []
    
    try:
        with neo4j_driver.session() as session:
            query = """
            MATCH (k:KnowledgePoint {name: $kp_name})-[:PREREQUISITE*1..$max_depth]->(prereq)
            RETURN prereq, length(prereq) as depth
            ORDER BY depth
            LIMIT 20
            """
            
            result = session.run(query, kp_name=knowledge_point, max_depth=max_depth)
            
            return [
                {
                    "name": record["prereq"].get("name", ""),
                    "description": record["prereq"].get("description", ""),
                    "depth": record["depth"]
                }
                for record in result
            ]
    except Exception as e:
        print(f"获取前置知识失败：{e}")
        return []


async def get_related_knowledge(knowledge_point: str, max_depth: int = 2) -> List[Dict]:
    """获取相关知识点的"""
    if not neo4j_available:
        return []
    
    try:
        with neo4j_driver.session() as session:
            query = """
            MATCH (k:KnowledgePoint {name: $kp_name})-[:RELATED_TO]-(related)
            RETURN related
            LIMIT 20
            """
            
            result = session.run(query, kp_name=knowledge_point)
            
            return [
                {
                    "name": record["related"].get("name", ""),
                    "description": record["related"].get("description", ""),
                    "category": record["related"].get("category", "")
                }
                for record in result
            ]
    except Exception as e:
        print(f"获取相关知识失败：{e}")
        return []


async def get_course_knowledge_map(course_id: str) -> Dict[str, Any]:
    """获取课程知识图谱"""
    if not neo4j_available:
        return {"nodes": [], "links": []}
    
    try:
        with neo4j_driver.session() as session:
            query = """
            MATCH (c:Course {id: $course_id})-[:CONTAINS]->(k:KnowledgePoint)
            OPTIONAL MATCH (k)-[r]-(related:KnowledgePoint)
            RETURN k, r, related
            LIMIT 200
            """
            
            result = session.run(query, course_id=course_id)
            
            nodes = {}
            links = []
            
            for record in result:
                # 添加节点
                k = record["k"]
                if k.id not in nodes:
                    nodes[k.id] = {
                        "id": k.id,
                        "name": k.get("name", ""),
                        "type": "KnowledgePoint",
                        "properties": dict(k)
                    }
                
                related = record.get("related")
                if related and related.id not in nodes:
                    nodes[related.id] = {
                        "id": related.id,
                        "name": related.get("name", ""),
                        "type": "KnowledgePoint",
                        "properties": dict(related)
                    }
                
                # 添加关系
                r = record.get("r")
                if r:
                    links.append({
                        "source": k.id,
                        "target": related.id if related else k.id,
                        "type": list(r.types)[0] if r.types else "UNKNOWN"
                    })
            
            return {
                "nodes": list(nodes.values()),
                "links": links
            }
    except Exception as e:
        print(f"获取课程知识图谱失败：{e}")
        return {"nodes": [], "links": []}


@router.post("/search", response_model=GraphSearchResponse)
async def graph_search(request: GraphSearchRequest):
    """知识图谱搜索"""
    start_time = datetime.now()
    
    results = []
    
    if request.search_type == "entity":
        results = await search_entities(
            keyword=request.query,
            course_id=request.course_id,
            top_k=request.top_k
        )
    elif request.search_type == "relation":
        results = await search_relations(
            entity_name=request.query,
            course_id=request.course_id
        )
    elif request.search_type == "path":
        # 路径查询需要解析 query 为 from 和 to
        parts = request.query.split("到")
        if len(parts) == 2:
            results = await search_path(
                from_entity=parts[0].strip(),
                to_entity=parts[1].strip()
            )
    
    search_time = (datetime.now() - start_time).total_seconds()
    
    return GraphSearchResponse(
        query=request.query,
        results=results,
        total=len(results),
        search_type=request.search_type,
        search_time=round(search_time, 3)
    )


@router.post("/entity")
async def search_entity(request: GraphEntityRequest):
    """实体搜索接口"""
    results = await search_entities(
        keyword=request.entity_name,
        entity_type=request.entity_type,
        course_id=request.course_id,
        top_k=request.top_k
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "query": request.entity_name,
            "results": results,
            "total": len(results)
        }
    }


@router.post("/relation")
async def search_relation(request: GraphRelationRequest):
    """关系查询接口"""
    results = await search_relations(
        entity_name=request.entity_name,
        relation_types=request.relation_types,
        max_depth=request.max_depth,
        course_id=request.course_id
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "entity": request.entity_name,
            "relations": results,
            "total": len(results)
        }
    }


@router.post("/path")
async def search_path(request: GraphPathRequest):
    """路径查询接口"""
    results = await search_path(
        from_entity=request.from_entity,
        to_entity=request.to_entity,
        max_depth=request.max_depth
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "from": request.from_entity,
            "to": request.to_entity,
            "paths": results,
            "total": len(results)
        }
    }


@router.get("/prerequisites/{knowledge_point}")
async def get_prereqs(knowledge_point: str, max_depth: int = 3):
    """获取前置知识"""
    results = await get_prerequisites(knowledge_point, max_depth)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "knowledge_point": knowledge_point,
            "prerequisites": results
        }
    }


@router.get("/related/{knowledge_point}")
async def get_related(knowledge_point: str, max_depth: int = 2):
    """获取相关知识"""
    results = await get_related_knowledge(knowledge_point, max_depth)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "knowledge_point": knowledge_point,
            "related": results
        }
    }


@router.get("/course/{course_id}")
async def get_course_map(course_id: str):
    """获取课程知识图谱"""
    graph = await get_course_knowledge_map(course_id)
    
    return {
        "code": 200,
        "message": "success",
        "data": graph
    }


@router.get("/status")
async def get_status():
    """获取 Neo4j 状态"""
    return {
        "code": 200,
        "data": {
            "available": neo4j_available,
            "connected": neo4j_driver is not None
        }
    }


@router.on_event("startup")
async def startup_event():
    """启动时初始化"""
    init_neo4j()


@router.on_event("shutdown")
async def shutdown_event():
    """关闭时清理"""
    close_neo4j()
