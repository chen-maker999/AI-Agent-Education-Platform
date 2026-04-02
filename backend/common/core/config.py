"""Application configuration management."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # App settings
    APP_NAME: str = "AI-Agent-Education-Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "edu_platform"
    POSTGRES_DATABASE_URL: Optional[str] = None

    # TimescaleDB (时序数据库)
    TIMESCALEDB_HOST: str = "localhost"
    TIMESCALEDB_PORT: int = 5433
    TIMESCALEDB_USER: str = "postgres"
    TIMESCALEDB_PASSWORD: str = "postgres"
    TIMESCALEDB_DB: str = "timeseries"

    def get_postgres_url(self, database: str = None) -> str:
        """Get PostgreSQL connection URL."""
        db = database or self.POSTGRES_DB
        if self.POSTGRES_DATABASE_URL:
            return self.POSTGRES_DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{db}"

    def get_postgres_sync_url(self, database: str = None) -> str:
        """Get PostgreSQL sync connection URL."""
        db = database or self.POSTGRES_DB
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{db}"

    def get_timescaledb_url(self) -> str:
        """Get TimescaleDB connection URL."""
        return f"postgresql://{self.TIMESCALEDB_USER}:{self.TIMESCALEDB_PASSWORD}@{self.TIMESCALEDB_HOST}:{self.TIMESCALEDB_PORT}/{self.TIMESCALEDB_DB}"

    def get_timescaledb_async_url(self) -> str:
        """Get TimescaleDB async connection URL."""
        return f"postgresql+asyncpg://{self.TIMESCALEDB_USER}:{self.TIMESCALEDB_PASSWORD}@{self.TIMESCALEDB_HOST}:{self.TIMESCALEDB_PORT}/{self.TIMESCALEDB_DB}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None

    def get_redis_url(self) -> str:
        """Get Redis connection URL."""
        if self.REDIS_URL:
            return self.REDIS_URL
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Neo4j
    NEO4J_HOST: str = "localhost"
    NEO4J_PORT: int = 7687
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j"
    NEO4J_DATABASE: str = "neo4j"

    def get_neo4j_url(self) -> str:
        """Get Neo4j connection URL."""
        return f"bolt://{self.NEO4J_HOST}:{self.NEO4J_PORT}"

    # TimescaleDB (PostgreSQL with TimescaleDB extension)
    TIMESCALEDB_HOST: str = "localhost"
    TIMESCALEDB_PORT: int = 5432
    TIMESCALEDB_USER: str = "postgres"
    TIMESCALEDB_PASSWORD: str = "postgres"
    TIMESCALEDB_DB: str = "timeseries"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_HOMEWORK: str = "edu-homework"
    MINIO_BUCKET_COURSEWARE: str = "edu-courseware"
    MINIO_BUCKET_LAKE: str = "edu-lake"

    # RabbitMQ
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"

    def get_rabbitmq_url(self) -> str:
        """Get RabbitMQ connection URL."""
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Kimi API (Moonshot)
    KIMI_API_KEY: Optional[str] = None
    KIMI_API_ENDPOINT: str = "https://api.moonshot.cn/v1"
    KIMI_MODEL: str = "kimi-k2.5"
    KIMI_TIMEOUT: int = 30

    # Tavily API (网络搜索)
    TAVILY_API_KEY: Optional[str] = None

    # Elasticsearch
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_INDEX: str = "edu_knowledge"
    ELASTICSEARCH_USERNAME: Optional[str] = None
    ELASTICSEARCH_PASSWORD: Optional[str] = None

    def get_elasticsearch_url(self) -> str:
        """Get Elasticsearch connection URL."""
        # 注意：ES 启用了 HTTPS
        if self.ELASTICSEARCH_USERNAME and self.ELASTICSEARCH_PASSWORD:
            return f"https://{self.ELASTICSEARCH_HOST}:{self.ELASTICSEARCH_PORT}"
        return f"https://{self.ELASTICSEARCH_HOST}:{self.ELASTICSEARCH_PORT}"

    # FAISS Vector Index
    FAISS_INDEX_TYPE: str = "IVF4096,PQ16"
    FAISS_DIMENSION: int = 384
    FAISS_NLIST: int = 4096
    FAISS_NPROBE: int = 32

    # Embedding Model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"  # cpu or cuda
    EMBEDDING_BATCH_SIZE: int = 64
    EMBEDDING_MAX_LENGTH: int = 512
    EMBEDDING_DIMENSION: int = 384  # all-MiniLM-L6-v2 outputs 384-dimensional vectors

    # Cross-Encoder for reranking
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # CORS
    CORS_ORIGINS: list = ["*"]

    # Consul
    CONSUL_HOST: str = "localhost"
    CONSUL_PORT: int = 8500

    # etcd (Config center)
    ETCD_HOST: str = "localhost"
    ETCD_PORT: int = 2379


@lru_cache()
def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


settings = get_settings()
