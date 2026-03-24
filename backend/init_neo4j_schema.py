#!/usr/bin/env python3
"""
Neo4j 知识图谱 Schema 初始化脚本
创建知识图谱的节点标签、关系类型和索引
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Neo4j 配置
NEO4J_URI = os.getenv("NEO4J_HOST", "localhost")
NEO4J_PORT = int(os.getenv("NEO4J_PORT", "7687"))
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4jpassword123")

# Cypher 语句定义
SCHEMA_QUERIES = [
    # 创建约束（确保唯一性）
    """
    CREATE CONSTRAINT IF NOT EXISTS FOR (k:KnowledgePoint) REQUIRE k.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT IF NOT EXISTS FOR (k:KnowledgePoint) REQUIRE k.name IS UNIQUE
    """,
    """
    CREATE CONSTRAINT IF NOT EXISTS FOR (c:Course) REQUIRE c.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT IF NOT EXISTS FOR (e:Example) REQUIRE e.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT IF NOT EXISTS FOR (ex:Exercise) REQUIRE ex.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT IF NOT EXISTS FOR (s:Student) REQUIRE s.id IS UNIQUE
    """,
    
    # 创建索引（加速查询）
    """
    CREATE INDEX IF NOT EXISTS FOR (k:KnowledgePoint) ON (k.category)
    """,
    """
    CREATE INDEX IF NOT EXISTS FOR (k:KnowledgePoint) ON (k.difficulty)
    """,
    """
    CREATE INDEX IF NOT EXISTS FOR (k:KnowledgePoint) ON (k.course_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS FOR (k:KnowledgePoint) ON (k.name)
    """,
    """
    CREATE INDEX IF NOT EXISTS FOR (c:Course) ON (c.name)
    """,
    """
    CREATE INDEX IF NOT EXISTS FOR (ex:Exercise) ON (ex.knowledge_point_ids)
    """,
    """
    CREATE INDEX IF NOT EXISTS FOR (ex:Exercise) ON (ex.difficulty)
    """,
    
    # 创建示例课程
    """
    MERGE (c:Course {
        id: 'cs-programming-101',
        name: '程序设计基础',
        department: '计算机科学与技术',
        level: '本科一年级',
        description: 'Python 程序设计入门课程'
    })
    """,
    
    # 创建示例知识点
    """
    MERGE (k1:KnowledgePoint {
        id: 'kp-python-variable',
        name: '变量与数据类型',
        category: '编程基础',
        difficulty: 1,
        importance: 5,
        course_id: 'cs-programming-101',
        description: 'Python 变量的定义、命名规则和基本数据类型'
    })
    """,
    """
    MERGE (k2:KnowledgePoint {
        id: 'kp-python-loop',
        name: '循环结构',
        category: '流程控制',
        difficulty: 2,
        importance: 5,
        course_id: 'cs-programming-101',
        description: 'for 循环和 while 循环的使用'
    })
    """,
    """
    MERGE (k3:KnowledgePoint {
        id: 'kp-python-function',
        name: '函数定义',
        category: '代码组织',
        difficulty: 3,
        importance: 5,
        course_id: 'cs-programming-101',
        description: '函数的定义、参数传递和返回值'
    })
    """,
    """
    MERGE (k4:KnowledgePoint {
        id: 'kp-python-list',
        name: '列表与数组',
        category: '数据结构',
        difficulty: 2,
        importance: 4,
        course_id: 'cs-programming-101',
        description: '列表的创建、访问和常用操作'
    })
    """,
    """
    MERGE (k5:KnowledgePoint {
        id: 'kp-python-dict',
        name: '字典与映射',
        category: '数据结构',
        difficulty: 3,
        importance: 4,
        course_id: 'cs-programming-101',
        description: '字典的创建、访问和遍历方法'
    })
    """,
    
    # 创建知识点之间的关系
    """
    MATCH (k1:KnowledgePoint {name: '变量与数据类型'}), (k2:KnowledgePoint {name: '循环结构'})
    MERGE (k1)-[:PREREQUISITE {weight: 0.8}]->(k2)
    """,
    """
    MATCH (k2:KnowledgePoint {name: '循环结构'}), (k3:KnowledgePoint {name: '函数定义'})
    MERGE (k2)-[:PREREQUISITE {weight: 0.7}]->(k3)
    """,
    """
    MATCH (k1:KnowledgePoint {name: '变量与数据类型'}), (k4:KnowledgePoint {name: '列表与数组'})
    MERGE (k1)-[:PREREQUISITE {weight: 0.9}]->(k4)
    """,
    """
    MATCH (k4:KnowledgePoint {name: '列表与数组'}), (k5:KnowledgePoint {name: '字典与映射'})
    MERGE (k4)-[:RELATED_TO {weight: 0.6}]->(k5)
    """,
    """
    MATCH (k1:KnowledgePoint {name: '变量与数据类型'}), (k5:KnowledgePoint {name: '字典与映射'})
    MERGE (k1)-[:PREREQUISITE {weight: 0.8}]->(k5)
    """,
    
    # 创建课程与知识点的关系
    """
    MATCH (c:Course {id: 'cs-programming-101'}), (k:KnowledgePoint)
    WHERE k.course_id = c.id
    MERGE (c)-[:CONTAINS]->(k)
    """,
    
    # 创建示例
    """
    MERGE (e1:Example {
        id: 'ex-variable-001',
        title: '变量定义示例',
        content: 'name = "张三"\\nage = 20\\nscore = 95.5',
        knowledge_point: '变量与数据类型',
        difficulty: 1
    })
    """,
    """
    MERGE (e2:Example {
        id: 'ex-loop-001',
        title: 'for 循环示例',
        content: 'for i in range(5):\\n    print(f"Hello {i}")',
        knowledge_point: '循环结构',
        difficulty: 2
    })
    """,
    """
    MERGE (e3:Example {
        id: 'ex-function-001',
        title: '函数定义示例',
        content: 'def greet(name):\\n    return f"Hello, {name}!"\\n\\nprint(greet("World"))',
        knowledge_point: '函数定义',
        difficulty: 3
    })
    """,
    
    # 创建示例与知识点的关系
    """
    MATCH (e:Example), (k:KnowledgePoint)
    WHERE e.knowledge_point = k.name
    MERGE (k)-[:HAS_EXAMPLE]->(e)
    """,
    
    # 创建练习题
    """
    MERGE (ex1:Exercise {
        id: 'exercise-001',
        title: '变量练习',
        question: '定义一个变量存储学生姓名，并打印出来',
        answer: 'student_name = "李华"\\nprint(student_name)',
        knowledge_point_ids: ["kp-python-variable"],
        difficulty: 1,
        question_type: 'coding'
    })
    """,
    """
    MERGE (ex2:Exercise {
        id: 'exercise-002',
        title: '循环练习',
        question: '使用 for 循环计算 1 到 100 的和',
        answer: 'total = 0\\nfor i in range(1, 101):\\n    total += i\\nprint(total)',
        knowledge_point_ids: ["kp-python-loop"],
        difficulty: 2,
        question_type: 'coding'
    })
    """,
    
    # 创建练习与知识点的关系
    """
    MATCH (ex:Exercise), (k:KnowledgePoint)
    WHERE k.id IN ex.knowledge_point_ids
    MERGE (k)-[:HAS_EXERCISE]->(ex)
    """
]


def init_neo4j_schema():
    """初始化 Neo4j 知识图谱 Schema"""
    
    uri = f"bolt://{NEO4J_URI}:{NEO4J_PORT}"
    
    print(f"连接到 Neo4j: {uri}")
    driver = GraphDatabase.driver(uri, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        # 测试连接
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
            print(f"当前图谱中有 {count} 个节点")
        
        # 执行 Schema 语句
        print("\\n开始初始化 Schema...")
        for i, query in enumerate(SCHEMA_QUERIES, 1):
            with driver.session() as session:
                try:
                    session.run(query)
                    print(f"[{i}/{len(SCHEMA_QUERIES)}] 执行成功")
                except Exception as e:
                    print(f"[{i}/{len(SCHEMA_QUERIES)}] 执行失败：{e}")
        
        # 验证结果
        with driver.session() as session:
            # 统计节点
            result = session.run("""
                MATCH (k:KnowledgePoint) RETURN count(k) as count
            """)
            kp_count = result.single()["count"]
            
            result = session.run("""
                MATCH ()-[r]->() RETURN count(r) as count
            """)
            rel_count = result.single()["count"]
            
            print(f"\\n初始化完成!")
            print(f"知识点数量：{kp_count}")
            print(f"关系数量：{rel_count}")
            
            # 显示示例查询
            print("\\n示例查询 - 查找'函数定义'的前置知识:")
            result = session.run("""
                MATCH (k:KnowledgePoint {name: '函数定义'})<-[:PREREQUISITE*1..3]-(prereq)
                RETURN prereq.name as prerequisite, prereq.difficulty as difficulty
                ORDER BY prereq.difficulty
            """)
            for record in result:
                print(f"  - {record['prerequisite']} (难度：{record['difficulty']})")
                
    except Exception as e:
        print(f"错误：{e}")
        raise
    finally:
        driver.close()


if __name__ == "__main__":
    init_neo4j_schema()
    print("\\nNeo4j 知识图谱初始化完成!")
