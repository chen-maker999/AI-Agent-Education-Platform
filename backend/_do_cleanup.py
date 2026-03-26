"""清理 rag_documents 表的脚本"""
import psycopg2
from psycopg2 import sql

# 数据库连接配置
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "postgre",
    "dbname": "edu_platform"
}

def main():
    conn = None
    try:
        # 连接数据库
        print("正在连接 PostgreSQL 数据库...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("连接成功！\n")

        # 1. 查询删除前的记录数
        cur.execute("SELECT COUNT(*) FROM rag_documents;")
        count_before = cur.fetchone()[0]
        print(f"【删除前】rag_documents 表中的记录数: {count_before}")

        # 2. 执行删除操作
        print("\n正在执行 DELETE FROM rag_documents; ...")
        cur.execute("DELETE FROM rag_documents;")
        conn.commit()
        print("删除操作已完成！")

        # 3. 查询删除后的记录数
        cur.execute("SELECT COUNT(*) FROM rag_documents;")
        count_after = cur.fetchone()[0]
        print(f"\n【删除后】rag_documents 表中的记录数: {count_after}")

        # 4. 报告总结
        print("\n" + "=" * 50)
        print("操作总结:")
        print(f"  删除前记录数: {count_before}")
        print(f"  删除记录数:   {count_before - count_after}")
        print(f"  删除后记录数: {count_after}")
        print("=" * 50)

        # 验证删除后是否为 0
        if count_after == 0:
            print("\n[OK] 确认: 删除后记录数为 0，清理成功！")
        else:
            print(f"\n[WARN] 警告: 删除后仍有 {count_after} 条记录")

        cur.close()

    except psycopg2.Error as e:
        print(f"\n数据库错误: {e}")
        raise
    finally:
        if conn:
            conn.close()
            print("\n数据库连接已关闭。")

if __name__ == "__main__":
    main()
