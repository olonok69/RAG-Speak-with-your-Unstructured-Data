# test run and see that you can genreate a respond successfully
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
import os
from langchain.docstore.document import Document
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
import logging

TEXT_SPLITTER_CHUNCK_SIZE = 200
TEXT_SPLITTER_CHUNCK_OVERLAP = 50


def get_llm(model):
    return ChatNVIDIA(model=model, max_tokens=1024)


def get_embeddings(model):
    return NVIDIAEmbeddings(model=model, truncate="END")


def get_text_splitter(model):
    text_splitter = SentenceTransformersTokenTextSplitter(
        model_name=model,
        tokens_per_chunk=TEXT_SPLITTER_CHUNCK_SIZE,
        chunk_overlap=TEXT_SPLITTER_CHUNCK_OVERLAP,
    )
    return text_splitter


# summarize tables
def get_table_summary(table, title, llm):
    res = ""
    try:
        # table = markdownify.markdownify(table)
        prompt = f"""
                    [INST] You are a virtual assistant.  Your task is to understand the content of TABLE in the markdown format.
                    TABLE is from "{title}".  Summarize the information in TABLE into SUMMARY. SUMMARY MUST be concise. Return SUMMARY only and nothing else.
                    TABLE: ```{table}```
                    Summary:
                    [/INST]
                """
        result = llm.invoke(prompt)
        res = result.content
    except Exception as e:
        logging.error(f"Error: {e} while getting table summary from LLM")
        if not os.getenv("NVIDIA_API_KEY", False):
            logging.error("NVIDIA_API_KEY not set")
        pass
    finally:
        return res


def get_tables_summary_llm(pages, llm):
    """
    # summarize tables
    Args:
        pages: list of pages
        llm: llm model
    """
    for parsed_item in pages:
        title = parsed_item["title"]
        for idx, table in enumerate(parsed_item["tables"]):
            logging.info(f"parsing tables in {title}...")
            table = get_table_summary(table, title, llm)
            parsed_item["tables"][idx] = table
    return pages


def get_documents(pages, splitter):
    """
    Get Langchain Documents from pages using the setntence transformer model
    Args:
        pages: list of pages
        splitter: text splitter
    """
    documents = []

    for parsed_item in pages:
        title = parsed_item["title"]
        url = parsed_item["url"]
        text_content = parsed_item["content"]
        documents.append(
            Document(page_content=text_content, metadata={"title": title, "url": url})
        )

        for idx, table in enumerate(parsed_item["tables"]):
            table_content = table
            documents.append(
                Document(page_content=table, metadata={"title": title, "url": url})
            )

        documents = splitter.split_documents(documents)
        logging.info(f"obtain {len(documents)} chunks")
    return documents


def build_context(chunks):
    """
    build context
    Args:
        chunks: chunks
    """
    context = ""
    for chunk in chunks:
        context = (
            context
            + "\n  Content: "
            + chunk.page_content
            + " | Title: ("
            + chunk.metadata["title"]
            + ") | URL: ("
            + chunk.metadata.get("url", "source")
            + ")"
        )
    return context


def generate_answer(llm, vectorstore, prompt_template, question):
    """
    generate answer
    Args:
        llm: llm model
        vectorstore: vectorstore
        prompt_template: prompt template
        question: question
    """
    retrieved_chunks = vectorstore.similarity_search(question)
    context = build_context(retrieved_chunks)
    args = {"context": context, "question": question}
    prompt = prompt_template.format(**args)
    ans = llm.invoke(prompt)
    return ans.content
