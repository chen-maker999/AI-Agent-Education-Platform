#!/usr/bin/env python3
"""
MinIO 初始化脚本
创建 RAG 系统所需的存储桶
"""

import os
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

load_dotenv()

# MinIO 配置
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

import json

# 需要创建的存储桶
BUCKETS = [
    {
        "name": "edu-courseware",
        "description": "课程课件存储",
        "policy": json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": ["arn:aws:s3:::edu-courseware/*"]
                }
            ]
        })
    },
    {
        "name": "edu-homework",
        "description": "学生作业存储",
        "policy": None  # 私有桶，不需要公开访问
    },
    {
        "name": "edu-lake",
        "description": "数据湖存储",
        "policy": None
    },
    {
        "name": "edu-backup",
        "description": "数据备份存储",
        "policy": None
    },
    {
        "name": "faiss-indexes",
        "description": "FAISS 向量索引备份",
        "policy": None
    },
    {
        "name": "edu-rag-cache",
        "description": "RAG 缓存存储",
        "policy": None
    }
]


def init_minio_buckets():
    """初始化 MinIO 存储桶"""
    
    print(f"连接到 MinIO: {MINIO_ENDPOINT}")
    
    # 创建客户端
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    
    try:
        # 检查连接
        buckets = client.list_buckets()
        print(f"当前已有 {len(buckets)} 个存储桶")
        for bucket in buckets:
            print(f"  - {bucket.name}")
        print()
        
        # 创建存储桶
        for bucket_info in BUCKETS:
            bucket_name = bucket_info["name"]
            try:
                # 检查桶是否存在
                if not client.bucket_exists(bucket_name):
                    client.make_bucket(bucket_name)
                    print(f"[创建] {bucket_name} - {bucket_info['description']}")
                else:
                    print(f"[存在] {bucket_name} - {bucket_info['description']}")
                
                # 设置桶策略（如果有）
                if bucket_info.get("policy"):
                    client.set_bucket_policy(bucket_name, bucket_info["policy"])
                    print(f"       └─ 已设置公开读取策略")
                    
            except S3Error as e:
                print(f"[失败] {bucket_name} - {e}")
        
        # 验证结果
        print()
        print("存储桶列表:")
        buckets = client.list_buckets()
        for bucket in buckets:
            print(f"  ✓ {bucket.name}")
            
        # 创建测试文件
        print()
        print("创建测试文件...")
        from io import BytesIO
        test_content = b"RAG Education Platform - MinIO Test File"
        client.put_object(
            "edu-rag-cache",
            "test/welcome.txt",
            data=BytesIO(test_content),
            length=len(test_content)
        )
        print("  ✓ edu-rag-cache/test/welcome.txt")
        
        # 验证测试文件
        obj = client.get_object("edu-rag-cache", "test/welcome.txt")
        content = obj.read()
        print(f"  验证内容：{content.decode()}")
        
    except S3Error as e:
        print(f"MinIO 错误：{e}")
        raise
    except Exception as e:
        print(f"错误：{e}")
        raise


if __name__ == "__main__":
    init_minio_buckets()
    print("\nMinIO 存储桶初始化完成!")
