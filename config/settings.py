import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = "enterprise-secret-key-ai-platform-2026-super-secure-token"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Vector DB (Pinecone)
    VECTOR_STORE_BACKEND: str = "memory"  # 'memory', 'pinecone'
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: str = "us-east-1"
    PINECONE_INDEX_NAME: str = "enterprise-knowledge-index"
    PINECONE_DIMENSION: int = 768

    # Embeddings & Vertex AI
    EMBEDDING_BACKEND: str = "local"  # 'local', 'vertex', 'sentence_transformers'
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    GCP_PROJECT_ID: str = "enterprise-intelligence-prod"
    GCP_LOCATION: str = "us-central1"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    # LLM & Multi-Agent Engine
    LLM_BACKEND: str = "simulation"  # 'simulation', 'gemini', 'vertex', 'openai'
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Warehouse & ERP
    WAREHOUSE_BACKEND: str = "local_warehouse"  # 'local_warehouse', 'bigquery'
    BIGQUERY_DATASET: str = "enterprise_analytics"
    ERP_DATABASE_URL: str = "sqlite:///./data/erp/erp_system.db"

    # Event-Driven Pub/Sub
    PUBSUB_BACKEND: str = "local_async"  # 'local_async', 'pubsub'
    PUBSUB_TOPIC_INGESTION: str = "projects/enterprise-intelligence-prod/topics/data-ingestion"
    PUBSUB_TOPIC_WORKFLOW: str = "projects/enterprise-intelligence-prod/topics/workflow-execution"
    PUBSUB_SUBSCRIPTION_NAME: str = "projects/enterprise-intelligence-prod/subscriptions/workflow-sub"
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_INITIAL_DELAY_SEC: float = 1.0
    RETRY_BACKOFF_FACTOR: float = 2.0

    # Observability & Eval Cost Model (USD per 1000 tokens)
    ENABLE_EXECUTION_TRACING: bool = True
    TRACING_EXPORTER: str = "internal"
    EVALUATION_COST_PER_1K_PROMPT_TOKENS: float = 0.000125
    EVALUATION_COST_PER_1K_COMPLETION_TOKENS: float = 0.000375

settings = Settings()
