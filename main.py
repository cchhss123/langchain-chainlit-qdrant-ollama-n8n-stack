import chainlit as cl
from langchain.callbacks.base import BaseCallbackHandler
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableConfig
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_qdrant import QdrantVectorStore
import subprocess
import asyncio

from config import EnvironmentVariables


@cl.on_chat_start
async def on_chat_start():
    template = """Answer the question based only on the following context:

    {context}

    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    def format_docs(docs):
        return "\n\n".join([d.page_content for d in docs])

    embedding = HuggingFaceEmbeddings(
        model_name=EnvironmentVariables().EMBED_MODEL_ID,
        model_kwargs={"trust_remote_code": True},
    )

    vectorstore = QdrantVectorStore.from_existing_collection(
        embedding=embedding,
        collection_name=EnvironmentVariables().QDRANT_COLLECTION_NAME,
        url=str(EnvironmentVariables().QDRANT_DATABASE_URL),
    )

    retriever = vectorstore.as_retriever()

    runnable = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | OllamaLLM(
            base_url=str(EnvironmentVariables().OLLAMA_URL),
            model=EnvironmentVariables().OLLAMA_LLM_MODEL,
        )
        | StrOutputParser()
    )

    cl.user_session.set("runnable", runnable)


@cl.on_message
async def on_message(message: cl.Message):
    # API-like endpoint for ingestion
    if message.content == "__INGEST_TRIGGER__":
        ingest_msg = cl.Message(content="Starting ingestion process...\n\n", author="IngestionBot")
        await ingest_msg.send()

        try:
            process = await asyncio.create_subprocess_exec(
                "python", "-m", "utils.ingest",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if stdout:
                await ingest_msg.stream_token(f"STDOUT:\n{stdout.decode()}\n")
            if stderr:
                await ingest_msg.stream_token(f"STDERR:\n{stderr.decode()}\n")
            
            if process.returncode == 0:
                 await ingest_msg.stream_token("\nIngestion process completed successfully.")
            else:
                 await ingest_msg.stream_token(f"\nIngestion process failed with return code {process.returncode}.")

        except Exception as e:
            await ingest_msg.stream_token(f"\nAn error occurred: {str(e)}")
        
        await ingest_msg.update()
        return

    # Regular chat logic
    runnable = cl.user_session.get("runnable")  # type: Runnable
    msg = cl.Message(content="")

    class PostMessageHandler(BaseCallbackHandler):
        """
        Callback handler for handling the retriever and LLM processes.
        Used to post the sources of the retrieved documents as a Chainlit element.
        """

        def __init__(self, msg: cl.Message):
            BaseCallbackHandler.__init__(self)
            self.msg = msg
            self.sources = set()

        def on_retriever_end(self, documents, *, run_id, parent_run_id, **kwargs):
            for d in documents:
                source_page_pair = (d.metadata["source"], d.metadata["page"])
                self.sources.add(source_page_pair)

        def on_llm_end(self, response, *, run_id, parent_run_id, **kwargs):
            if len(self.sources):
                sources_text = "\n".join(
                    [f"{source}#page={page}" for source, page in self.sources]
                )
                self.msg.elements.append(
                    cl.Text(name="Sources", content=sources_text, display="inline")
                )

    async for chunk in runnable.astream(
        message.content,
        config=RunnableConfig(
            callbacks=[cl.LangchainCallbackHandler(), PostMessageHandler(msg)]
        ),
    ):
        await msg.stream_token(chunk)

    await msg.send()
