from langchain_community.vectorstores import FAISS
from langchain_elasticsearch import ElasticsearchStore
from src.pdf_utils import create_documents_metadatas, load_file
from src.helpers import save_df_pdf
from uuid import uuid4
import logging
import os
import platform
from langchain_milvus import Milvus
from langchain_chroma import Chroma
from langchain_google_vertexai import VertexAIEmbeddings
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.storage import InMemoryStore
from langchain_core.documents import Document
import uuid


def create_multi_vectorstore(
    collection_name: str, embeddings_model: str, credentials: str
):
    """
    Create a multi vector store.
    Args:
        collection_name (str): The name of the collection.
        embeddings_model (str): The name of the embeddings model.
        credentials (str): The credentials for the embeddings model.
    Returns:
        _type_: Chroma   The created Chroma object.
    """
    return Chroma(
        collection_name=collection_name,
        embedding_function=VertexAIEmbeddings(
            model_name=embeddings_model, credentials=credentials
        ),
    )


def create_multivector_retriever(key: str, vectorstore):
    """
    Create multi-vector retriever.
    Args:
        key (str): The key for the multi-vector retriever.
        vectorstore (object): The vector store to be used.
    """
    # Initialize the storage layer
    store = InMemoryStore()
    id_key = key

    # Create the multi-vector retriever
    retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        docstore=store,
        id_key=id_key,
    )
    return retriever


def add_docs_multi_vector_retriever(
    retriever,
    text_summaries,
    texts,
    table_summaries,
    tables,
    image_summaries,
    images,
    id_key,
):
    """
    Add Documents to retriever that indexes summaries, but returns raw images or texts
    Args:
        retriever (object): The retriever object to which documents will be added.
        text_summaries (list of str): A list of text summaries.
        texts (list of str): A list of text documents.
        table_summaries (list of str): A list of table summaries.
        tables (list of str): A list of table documents.
        image_summaries (list of str): A list of image summaries.
        images (list of str): A list of image documents.
        id_key (str): The key for the document ID.
    """

    # Helper function to add documents to the vectorstore and docstore
    def add_documents(retriever, doc_summaries, doc_contents):
        doc_ids = [str(uuid.uuid4()) for _ in doc_contents]
        summary_docs = [
            Document(page_content=s, metadata={id_key: doc_ids[i]})
            for i, s in enumerate(doc_summaries)
        ]
        retriever.vectorstore.add_documents(summary_docs)
        retriever.docstore.mset(list(zip(doc_ids, doc_contents)))

    # Add texts, tables, and images
    # Check that text_summaries is not empty before adding
    if text_summaries:
        add_documents(retriever, text_summaries, texts)
    # Check that table_summaries is not empty before adding
    if table_summaries:
        add_documents(retriever, table_summaries, tables)
    # Check that image_summaries is not empty before adding
    if image_summaries:
        add_documents(retriever, image_summaries, images)

    return retriever


def create_db_store_from_file(embeddings, index_name, folder_path: str = "./faiss/"):
    """
    Load a Faiss index from a file.

    Args:
        embeddings (Any): The embeddings object used for the Faiss index.
        index_name (str): The name of the index to load.
        folder_path (str, optional): The path to the folder containing the Faiss index file. Defaults to "./faiss/".

    Returns:
        _type_: Faiss   The loaded Faiss index.
    """
    return FAISS.load_local(
        folder_path=folder_path,
        embeddings=embeddings,
        index_name=index_name,
        allow_dangerous_deserialization=True,
    )


def create_db_from_documents(texts, embedding, metadatas, ids):
    """
    Create a FAISS database from documents.
    Params:
        texts (list of str): A list of document texts.
        embedding (Embedding): The embedding model to use for vectorizing the texts.
        metadatas (list of dict): A list of metadata dictionaries corresponding to each document.
        ids (list of str): A list of unique identifiers for each document.
    return:
        FAISS: A FAISS index created from the provided documents.
    """
    return FAISS.from_texts(
        texts=texts, embedding=embedding, metadatas=metadatas, ids=ids
    )


def create_elasticsearch_store(index_name, embeddings, es_url):
    """
    Create a vector store in Elasticsearch.

        index_name (str): Name of the index in Elasticsearch.
        embeddings (object): Embeddings model to be used.
        es_url (str): URL to the Elasticsearch instance (e.g., "http://localhost:9200").

    Returns:
        ElasticsearchStore: An instance of the ElasticsearchStore class.
    """

    return ElasticsearchStore(
        index_name=index_name,
        embedding=embeddings,
        es_url=es_url,
    )


def add_documents_vector_store(
    config,
    session,
    embeddings,
    db_local_folder,
    df_pdfs,
    pname,
    db_load,
    file_path: str = "",
):
    """
    Adds documents to a vector store based on the specified type (Faiss or Elastic).
    Parameters:
    - config (dict): Configuration dictionary containing settings for the vector store.
    - session (Streamlit): Streamlit session state object.
    - embeddings (object): Embeddings retriever object used for creating document embeddings.
    - db_local_folder (str): Path to the local folder where the database will be saved.
    - df_pdfs (DataFrame): DataFrame containing PDF information.
    - pname (str): Name of the dataframe file.
    - db_load (object): Vector Database object to which documents will be added.
    - file_path (str): Path to the file to be added to the vector store.
    Returns:
    - db_load (object): Updated database object after adding documents.

    """

    if config.get("VECTOR_STORE") == "faiss":
        # Add documents to Faiss and save database to local
        documents_all, metadatas_all, ids_all = create_documents_metadatas(
            files=[session.session_state["file_name"]],
            category=config.get("INDEX_NAME"),
        )

        db_load = create_db_from_documents(
            texts=documents_all,
            embedding=embeddings,
            metadatas=metadatas_all,
            ids=ids_all,
        )

        # save faiss vectorstore to disk
        db_load.save_local(db_local_folder, index_name=config.get("INDEX_NAME"))

        if db_load.index.ntotal > 0:
            print(
                f"Number of documents added to Faiss vector store {db_load.index.ntotal}"
            )
            save_df_pdf(
                df=df_pdfs,
                fname=pname,
                filename=session.session_state["file_history"],
            )
    elif config.get("VECTOR_STORE") == "elastic":
        ## add documents to Elastic
        pages = load_file(file_path)
        logging.info(f"Loaded file {file_path} with {len(pages)} ")
        # create an ID per Langchain Document
        uuids = [str(uuid4()) for _ in range(len(pages))]

        ids = db_load.add_documents(documents=pages, ids=uuids)
        logging.info(f"Number of documents added to Elastic vector store {len(ids)}")

        return db_load


def add_documents_vector_store_speak_html(
    config, session, db_load, db_local_folder, embeddings
):
    """
    Adds documents to a vector store based on the specified type (Faiss or Elastic).
    Parameters:
    - config (dict): Configuration dictionary containing settings for the vector store.
    - session (Streamlit): Streamlit session state object.
    - embeddings (object): Embeddings retriever object used for creating document embeddings.
    - db_local_folder (str): Path to the local folder where the database will be saved.

    - db_load (object): Vector Database object to which documents will be added.
    Returns:
    - db_load (object): Updated database object after adding documents.

    """

    ## add documents to
    if config.get("VECTOR_STORE_HTML") == "elastic":
        logging.info(
            f"{len(session.session_state['documents'])} Documents to upload to Vector Store"
        )
        # create an ID per Langchain Document
        uuids = [str(uuid4()) for _ in range(len(session.session_state["documents"]))]

        ids = db_load.add_documents(
            documents=session.session_state["documents"], ids=uuids
        )
        logging.info(f"Number of documents added to  vector store {len(ids)}")
    elif config.get("VECTOR_STORE_HTML") == "milvus":
        # in db_local_folder in Milvus case come the URI
        logging.info(
            f"{len(session.session_state['documents'])} Documents to upload to Vector Store"
        )
        db_load = Milvus.from_documents(
            session.session_state["documents"],
            embeddings,
            collection_name="NVIDIA_Finance",
            connection_args={
                "uri": db_local_folder
            },  # replace this with the ip of the workstation where milvus is running
            drop_old=True,
        )

    return db_load


def configure_vector_store_speak_html(config: dict, path: str, embeddings: object):
    """
    Configure the vector store for the Speak and HTML pages.
    Parameters:
    - config (dict): Configuration dictionary containing settings for the vector store.
    - path (str): Path to the current file.
    - embeddings_retriever (object): Embeddings retriever object used for creating document embeddings.
    Returns:
    - db_load (object): Vector Database object to which documents will be added.
    - db_local_folder (str): Path to the local folder where the database will be saved.
    - db_local_file (str): Path to the file where the database will be saved.
    """

    if config["VECTOR_STORE_HTML"] == "milvus":
        db_local_folder = os.path.join(path.parent.absolute(), config["FOLDER_PATH"])
        URI = "milvus_example.db"
        db_local_file = os.path.join(db_local_folder, URI)
        db_local_folder = os.path.join(db_local_folder, URI)
        db_load = None

    elif config["VECTOR_STORE_HTML"] == "elastic":
        USER = os.getenv("USER")
        if platform.system() == "Windows" or (
            platform.system() == "Linux" and USER == "olonok"
        ):
            url = "http://localhost:9200"
        else:
            url = config.get("ELASTIC_URL")
        db_load = create_elasticsearch_store(
            index_name="premcloud_demo_html",
            embeddings=embeddings,
            es_url=url,
        )
        db_local_folder = None
        db_local_file = None
    return db_load, db_local_folder, db_local_file
