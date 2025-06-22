# RAG 應用程式範例

這是一個使用多種開源框架搭建的 Retrieval-Augmented Generation (RAG) 應用程式範例。

## 1. 技術框架說明

本專案整合了以下主流的 AI 與資料處理框架，以實現一個完整的 RAG 應用：

*   **LangChain**: 作為核心框架，用於串連大型語言模型（LLM）與各種外部資料源，建構複雜的 LLM 工作流程。
*   **LlamaIndex**: 作為數據框架，專門處理和索引非結構化與結構化數據，並為 RAG 應用提供高效的數據檢索能力。
*   **Chainlit**: 用於快速開發與部署 LLM 應用的前端介面，提供了一個友善的聊天機器人 UI。
*   **Ollama**: 讓您可以在本地端輕鬆運行大型語言模型，例如 Llama 3、Mistral 等。
*   **Qdrant**: 一個高效能的向量資料庫，用於儲存由文件中產生的向量嵌入（Embeddings），並提供快速的相似度搜尋。
*   **n8n**: 一個工作流程自動化工具，可用於擴展應用程式的功能，例如自動化數據處理或觸發其他服務。

## 2. 部署與執行流程

請依照以下步驟使用 Docker 啟動並運行本專案。

### 步驟一：啟動所有服務

在專案的根目錄下，執行以下指令來啟動所有在 `docker-compose.yaml` 中定義的服務。

```shell
docker compose up -d
```

### 步驟二：下載語言模型

進入 `ollama` 容器，下載應用程式所需的語言模型和嵌入模型。

```shell
ollama pull deepseek-r1:1.5b
ollama pull nomic-embed-text
```

### 步驟三：資料內嵌 (Ingestion)

進入 `chainlit` 容器，執行資料內嵌腳本。此腳本會讀取 `data/` 目錄下的文件，將其轉換為向量並存入 Qdrant 向量資料庫中。

```shell
cd /code/app
python -m utils.ingest
```

### 步驟四：驗證與使用服務

所有服務啟動並完成資料內嵌後，您可以透過以下網址存取各個服務：

*   **Chainlit 應用程式**: [http://localhost:8000](http://localhost:8000)
    *   這是主要的聊天應用程式介面。
*   **Qdrant 儀表板**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)
    *   您可以在這裡查看 Qdrant 中的 collection 是否成功建立以及數據量。
*   **n8n 工作流程**: [http://localhost:5678](http://localhost:5678)
    *   n8n 的儀表板，您可以在此設計與管理自動化工作流程。

## 3. 環境變數說明

本專案透過環境變數進行設定，您可以在 `.env.example` 檔案中找到所有可用的變數。複製一份並命名為 `.env` 即可進行客製化。

| 環境變數                  | 描述                                     | 預設值 (在 docker-compose.yaml 中設定) |
| --------------------------- | ---------------------------------------- | -------------------------------------- |
| `QDRANT_DATABASE_URL`       | Qdrant 資料庫的連線 URL。                | `http://qdrantdb:6333`                 |
| `QDRANT_COLLECTION_NAME`    | 在 Qdrant 中儲存向量的 collection 名稱。 | `template`                             |
| `OLLAMA_URL`                | Ollama 服務的連線 URL。                  | `http://ollama:11434`                  |
| `OLLAMA_LLM_MODEL`          | 指定要使用的 Ollama 語言模型。           | `deepseek-r1:1.5b`                     |
| `DATA_INGESTION_LOCATION`   | 指定要進行內嵌的資料來源路徑。           | `/data`                                |
