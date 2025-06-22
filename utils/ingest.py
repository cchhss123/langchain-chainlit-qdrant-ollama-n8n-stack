import os
from pathlib import Path

from docling.chunking import HybridChunker
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore

from config import EnvironmentVariables

EXPORT_TYPE = ExportType.DOC_CHUNKS


def load_documents_from_path(path: Path) -> list:
    """從單一文件或整個目錄載入文件。"""
    if path.is_dir():
        all_docs = []
        print(f"正在處理目錄中的所有文件: {path}")
        for filename in os.listdir(path):
            file_path = path / filename
            if file_path.is_file():
                try:
                    print(f"  - 正在載入文件: {filename}")
                    loader = DoclingLoader(
                        file_path=str(file_path),
                        export_type=EXPORT_TYPE,
                        chunker=HybridChunker(
                            tokenizer=EnvironmentVariables().EMBED_MODEL_ID
                        ),
                    )
                    all_docs.extend(loader.load())
                except Exception as e:
                    print(f"    [!] 載入 {filename} 失敗: {e}")
        return all_docs
    elif path.is_file():
        print(f"正在處理單一文件: {path}")
        loader = DoclingLoader(
            file_path=str(path),
            export_type=EXPORT_TYPE,
            chunker=HybridChunker(
                tokenizer=EnvironmentVariables().EMBED_MODEL_ID
            ),
        )
        return loader.load()
    else:
        print(f"路徑不存在或不是有效的文件/目錄: {path}")
        return []


def docling_document_ingestion_into_qdrant_database() -> None:
    """
    Docling 將 PDF, DOCX, PPTX, HTML 等多種格式的文件解析為包含佈局、表格等資訊的統一表示，
    使其適用於 RAG 等生成式 AI 工作流程。
    """
    data_location = Path(EnvironmentVariables().DATA_INGESTION_LOCATION)
    
    docling_documents = load_documents_from_path(data_location)

    # TEMPORARY: Print the first document chunk to inspect its structure
    if docling_documents:
        print("--- Document Chunk Structure Example ---")
        print(docling_documents[0])
        print("------------------------------------")

    if not docling_documents:
        print("沒有載入任何文件，程序結束。")
        return

    # 決定如何分割文件
    if EXPORT_TYPE == ExportType.DOC_CHUNKS:
        splits = docling_documents
    elif EXPORT_TYPE == ExportType.MARKDOWN:
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header_1"),
                ("##", "Header_2"),
                ("###", "Header_3"),
            ],
        )
        splits = [
            split
            for doc in docling_documents
            for split in splitter.split_text(doc.page_content)
        ]
    else:
        raise ValueError(f"未預期的導出類型: {EXPORT_TYPE}")

    # 初始化詞嵌入模型
    embedding = OllamaEmbeddings(
        model=EnvironmentVariables().OLLAMA_EMBED_MODEL,
        base_url=str(EnvironmentVariables().OLLAMA_URL),
    )

    print(f"正在將 {len(splits)} 個文件片段導入 Qdrant...")
    # 從分割後的文件創建並持久化 Qdrant 向量數據庫
    QdrantVectorStore.from_documents(
        documents=splits,
        embedding=embedding,
        url=str(EnvironmentVariables().QDRANT_DATABASE_URL),
        collection_name=EnvironmentVariables().QDRANT_COLLECTION_NAME,
    )
    print("導入完成。")


if __name__ == "__main__":
    docling_document_ingestion_into_qdrant_database()
