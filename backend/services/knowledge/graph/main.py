"""Graph knowledge service - Neo4j based knowledge graph."""

from uuid import uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from common.models.response import ResponseModel
from common.database.neo4j import neo4j_client

router = APIRouter(prefix="/knowledge/graph", tags=["Knowledge Graph"])

NEO4J_AVAILABLE = True


@router.get("/", response_model=ResponseModel)
async def get_graph_stats():
    """获取知识图谱统计信息"""
    stats = {
        "total_nodes": 0,
        "total_edges": 0,
        "node_types": [],
        "status": "connected" if NEO4J_AVAILABLE else "disconnected"
    }
    try:
        driver = await neo4j_client.connect()
        async with driver.session() as session:
            # Count nodes
            result = await session.run("MATCH (n) RETURN count(n) as count")
            record = await result.single()
            stats["total_nodes"] = record["count"] if record else 0

            # Count edges
            result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
            record = await result.single()
            stats["total_edges"] = record["count"] if record else 0
    except Exception as e:
        stats["status"] = f"error: {str(e)}"

    return ResponseModel(code=200, message="success", data=stats)


class NodeCreate(BaseModel):
    node_id: Optional[str] = None
    name: str
    node_type: str
    course_id: Optional[str] = None
    properties: Dict[str, Any] = {}


class EdgeCreate(BaseModel):
    source_id: str
    target_id: str
    edge_type: str
    weight: float = 1.0
    properties: Dict[str, Any] = {}


class GraphQuery(BaseModel):
    node_id: Optional[str] = None
    node_type: Optional[str] = None
    relation_type: Optional[str] = None
    depth: int = 2
    limit: int = 100


async def create_node_neo4j(node_data: dict) -> dict:
    """在Neo4j中创建节点"""
    try:
        driver = await neo4j_client.connect()
        async with driver.session() as session:
            props = node_data.get("properties", {})
            props["node_id"] = node_data.get("node_id")
            props["name"] = node_data.get("name")
            props["node_type"] = node_data.get("node_type")
            props["course_id"] = node_data.get("course_id")
            
            props_str = ", ".join([f"n.{k} = ${k}" for k in props.keys()])
            query = f"CREATE (n:Node {{{props_str}}}) RETURN n"
            result = await session.run(query, **props)
            record = await result.single()
            if record:
                return dict(record["n"])
    except Exception as e:
        print(f"Neo4j创建节点失败: {e}")
    return node_data


async def get_node_neo4j(node_id: str) -> Optional[dict]:
    """从Neo4j获取节点"""
    try:
        driver = await neo4j_client.connect()
        async with driver.session() as session:
            result = await session.run("MATCH (n:Node {node_id: $node_id}) RETURN n", node_id=node_id)
            record = await result.single()
            if record:
                return dict(record["n"])
    except Exception as e:
        print(f"Neo4j获取节点失败: {e}")
    return None


async def delete_node_neo4j(node_id: str) -> bool:
    """在Neo4j中删除节点及其关系"""
    try:
        driver = await neo4j_client.connect()
        async with driver.session() as session:
            await session.run("MATCH (n:Node {node_id: $node_id}) DETACH DELETE n", node_id=node_id)
            return True
    except Exception as e:
        print(f"Neo4j删除节点失败: {e}")
    return False


async def create_edge_neo4j(edge_data: dict) -> dict:
    """在Neo4j中创建关系"""
    try:
        driver = await neo4j_client.connect()
        async with driver.session() as session:
            query = """
            MATCH (a:Node {node_id: $source_id})
            MATCH (b:Node {node_id: $target_id})
            CREATE (a)-[r:RELATION {type: $edge_type, weight: $weight}]->(b)
            RETURN a, r, b
            """
            await session.run(query, 
                source_id=edge_data["source_id"], 
                target_id=edge_data["target_id"], 
                edge_type=edge_data["edge_type"], 
                weight=edge_data.get("weight", 1.0)
            )
    except Exception as e:
        print(f"Neo4j创建边失败: {e}")
    return edge_data


async def query_graph_neo4j(node_id: str, relation_type: str = None, depth: int = 2) -> Dict:
    """在Neo4j中查询图"""
    try:
        driver = await neo4j_client.connect()
        async with driver.session() as session:
            if relation_type:
                query = f"""
                MATCH (start:Node {{node_id: $node_id}})
                MATCH path = (start)-[r:RELATION {{{relation_type}}}]->(end)
                RETURN nodes(path) as nodes, relationships(path) as edges
                LIMIT 100
                """
            else:
                query = """
                MATCH (start:Node {node_id: $node_id})
                MATCH path = (start)-[r:RELATION*1..2]->(end)
                RETURN nodes(path) as nodes, relationships(path) as edges
                LIMIT 100
                """
            result = await session.run(query, node_id=node_id)
            records = await result.data()
            
            nodes = []
            edges = []
            for record in records:
                for n in record.get("nodes", []):
                    if n and n.element_id not in [x.get("element_id") for x in nodes]:
                        nodes.append({"node_id": n.get("node_id"), "name": n.get("name"), "node_type": n.get("node_type")})
                for e in record.get("edges", []):
                    edges.append({"source_id": e.start_node.element_id, "target_id": e.end_node.element_id, "edge_type": e.get("type"), "weight": e.get("weight")})
            
            return {"nodes": nodes, "edges": edges}
    except Exception as e:
        print(f"Neo4j查询图失败: {e}")
    return {"nodes": [], "edges": []}


async def get_neighbors_neo4j(node_id: str, relation_type: str = None, direction: str = "both") -> Dict:
    """在Neo4j中获取邻居节点"""
    try:
        driver = await neo4j_client.connect()
        async with driver.session() as session:
            if direction == "outgoing":
                if relation_type:
                    query = """
                    MATCH (n:Node {node_id: $node_id})-[r:RELATION {type: $relation_type}]->(neighbor)
                    RETURN neighbor
                    """
                    result = await session.run(query, node_id=node_id, relation_type=relation_type)
                else:
                    query = """
                    MATCH (n:Node {node_id: $node_id})-[r:RELATION]->(neighbor)
                    RETURN neighbor
                    """
                    result = await session.run(query, node_id=node_id)
            elif direction == "incoming":
                if relation_type:
                    query = """
                    MATCH (n:Node {node_id: $node_id})<-[r:RELATION {type: $relation_type}]-(neighbor)
                    RETURN neighbor
                    """
                    result = await session.run(query, node_id=node_id, relation_type=relation_type)
                else:
                    query = """
                    MATCH (n:Node {node_id: $node_id})<-[r:RELATION]-(neighbor)
                    RETURN neighbor
                    """
                    result = await session.run(query, node_id=node_id)
            else:
                if relation_type:
                    query = """
                    MATCH (n:Node {node_id: $node_id})-[r:RELATION {type: $relation_type}]-(neighbor)
                    RETURN neighbor
                    """
                    result = await session.run(query, node_id=node_id, relation_type=relation_type)
                else:
                    query = """
                    MATCH (n:Node {node_id: $node_id})-[r:RELATION]-(neighbor)
                    RETURN neighbor
                    """
                    result = await session.run(query, node_id=node_id)
            
            records = await result.data()
            neighbors = [dict(record["neighbor"]) for record in records]
            return {"incoming": neighbors if direction == "incoming" else [], "outgoing": neighbors if direction == "outgoing" else [], "all": neighbors if direction == "both" else []}
    except Exception as e:
        print(f"Neo4j获取邻居失败: {e}")
    return {"incoming": [], "outgoing": [], "all": []}


async def find_path_neo4j(source_id: str, target_id: str, max_depth: int = 5) -> Dict:
    """在Neo4j中查找最短路径"""
    try:
        driver = await neo4j_client.connect()
        async with driver.session() as session:
            query = f"""
            MATCH (a:Node {{node_id: $source_id}}), (b:Node {{node_id: $target_id}})
            MATCH path = shortestPath((a)-[r:RELATION*1..{max_depth}]->(b))
            RETURN path
            """
            result = await session.run(query, source_id=source_id, target_id=target_id)
            record = await result.single()
            if record and record["path"]:
                path = record["path"]
                path_nodes = [{"node_id": n.get("node_id"), "name": n.get("name")} for n in path.nodes]
                return {"found": True, "path": path_nodes, "length": len(path_nodes)}
    except Exception as e:
        print(f"Neo4j查找路径失败: {e}")
    return {"found": False, "path": [], "length": 0}


@router.post("/nodes", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def create_node(data: NodeCreate):
    """创建知识图谱节点"""
    node_id = data.node_id or str(uuid4())
    node = {
        "node_id": node_id,
        "name": data.name,
        "node_type": data.node_type,
        "course_id": data.course_id,
        "properties": data.properties,
        "created_at": datetime.utcnow().isoformat()
    }
    
    if NEO4J_AVAILABLE:
        await create_node_neo4j(node)
    
    return ResponseModel(code=200, message="success", data=node)


@router.get("/nodes/{node_id}", response_model=ResponseModel)
async def get_node(node_id: str):
    """获取节点"""
    if NEO4J_AVAILABLE:
        node = await get_node_neo4j(node_id)
        if node:
            return ResponseModel(code=200, message="success", data=node)
    raise HTTPException(status_code=404, detail="Node not found")


@router.delete("/nodes/{node_id}", response_model=ResponseModel)
async def delete_node(node_id: str):
    """删除节点及其关系"""
    if NEO4J_AVAILABLE:
        await delete_node_neo4j(node_id)
    return ResponseModel(code=200, message="删除成功")


@router.post("/edges", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def create_edge(data: EdgeCreate):
    """创建知识图谱边"""
    edge = {
        "source_id": data.source_id,
        "target_id": data.target_id,
        "edge_type": data.edge_type,
        "weight": data.weight,
        "properties": data.properties
    }
    
    if NEO4J_AVAILABLE:
        await create_edge_neo4j(edge)
    
    return ResponseModel(code=200, message="success", data=edge)


@router.delete("/edges", response_model=ResponseModel)
async def delete_edge(source_id: str = Query(...), target_id: str = Query(...), edge_type: str = Query(None)):
    """删除图边"""
    if NEO4J_AVAILABLE:
        try:
            driver = await neo4j_client.connect()
            async with driver.session() as session:
                if edge_type:
                    query = """
                    MATCH (a:Node {node_id: $source_id})-[r:RELATION {type: $edge_type}]->(b:Node {node_id: $target_id})
                    DELETE r
                    """
                    await session.run(query, source_id=source_id, target_id=target_id, edge_type=edge_type)
                else:
                    query = """
                    MATCH (a:Node {node_id: $source_id})-[r:RELATION]->(b:Node {node_id: $target_id})
                    DELETE r
                    """
                    await session.run(query, source_id=source_id, target_id=target_id)
        except Exception as e:
            print(f"Neo4j删除边失败: {e}")
    return ResponseModel(code=200, message="删除成功")


@router.post("/query", response_model=ResponseModel)
async def query_graph(data: GraphQuery):
    """查询知识图谱"""
    if not data.node_id:
        return ResponseModel(code=400, message="node_id is required", data={"nodes": [], "edges": []})
    
    if NEO4J_AVAILABLE:
        result = await query_graph_neo4j(data.node_id, data.relation_type, data.depth)
        return ResponseModel(code=200, message="success", data=result)
    
    return ResponseModel(code=200, message="success", data={"nodes": [], "edges": []})


@router.get("/nodes/{node_id}/neighbors", response_model=ResponseModel)
async def get_neighbors(node_id: str, relation_type: str = Query(None), direction: str = Query("both")):
    """获取相邻节点"""
    if NEO4J_AVAILABLE:
        result = await get_neighbors_neo4j(node_id, relation_type, direction)
        return ResponseModel(code=200, message="success", data=result)
    return ResponseModel(code=200, message="success", data={"incoming": [], "outgoing": []})


@router.get("/path", response_model=ResponseModel)
async def find_path(source_id: str = Query(...), target_id: str = Query(...), max_depth: int = Query(5)):
    """查找最短路径"""
    if NEO4J_AVAILABLE:
        result = await find_path_neo4j(source_id, target_id, max_depth)
        return ResponseModel(code=200, message="success", data=result)
    return ResponseModel(code=200, message="success", data={"found": False, "path": [], "length": 0})


@router.get("/stats", response_model=ResponseModel)
async def get_graph_stats():
    """获取图谱统计"""
    if NEO4J_AVAILABLE:
        try:
            driver = await neo4j_client.connect()
            async with driver.session() as session:
                node_result = await session.run("MATCH (n:Node) RETURN count(n) as count")
                node_record = await node_result.single()
                node_count = node_record["count"] if node_record else 0
                
                edge_result = await session.run("MATCH ()-[r:RELATION]->() RETURN count(r) as count")
                edge_record = await edge_result.single()
                edge_count = edge_record["count"] if edge_record else 0
                
                return ResponseModel(code=200, message="success", data={
                    "node_count": node_count, 
                    "edge_count": edge_count, 
                    "neo4j_available": True
                })
        except Exception as e:
            print(f"Neo4j统计失败: {e}")
    
    return ResponseModel(code=200, message="success", data={
        "node_count": 0, 
        "edge_count": 0, 
        "neo4j_available": NEO4J_AVAILABLE
    })
