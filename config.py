from pydantic import Field
from pydantic_core import Url
from pydantic_settings import BaseSettings


class EnvironmentVariables(BaseSettings):
    QDRANT_DATABASE_URL: Url = Field(
        description="The Qdrant Database URL", default="http://localhost:6333"
    )
    QDRANT_COLLECTION_NAME: str = Field(
        description="The of the Qdrant collection name", default="template"
    )
    OLLAMA_URL: Url = Field(
        description="The Ollama host URL", default="http://localhost:11434"
    )
    OLLAMA_LLM_MODEL: str = Field(
        description="The Ollama model to use", default="deepseek-r1:1.5b"
    )
    OLLAMA_EMBED_MODEL: str = Field(
        description="The Ollama embeddings model to use", default="nomic-embed-text"
    )
    DATA_INGESTION_LOCATION: str = Field(
        description="The file path for data to be ingested",
    )
    EMBED_MODEL_ID: str = Field(
        description="model ID to use for the tokenizer during chunking",
        default="nomic-ai/nomic-embed-text-v1.5",
    )
