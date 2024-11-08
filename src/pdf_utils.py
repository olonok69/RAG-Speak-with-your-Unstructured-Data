import os
import pathlib
import fitz
from langchain_community.document_loaders import PyPDFLoader
import uuid
from typing import List
import pymupdf4llm
import pymupdf
from streamlit import session_state as ss


def extract_images_text_pdf(
    path: str, image_path: str, export_images: bool = True, image_format: str = "jpg"
):
    """
    Extract text and images from a pdf file
    """
    return pymupdf4llm.to_markdown(
        doc=path,
        write_images=export_images,
        image_path=image_path,
        image_format=image_format,
    )


def extract_tables_from_pdf(path: str):
    """
    Extract tables from a pdf file
    """
    doc = pymupdf.open(path)
    tables = {}
    for i, page in enumerate(doc):
        tabs = page.find_tables()
        if len(tabs.tables) > 0:
            tables[i] = tabs
    return tables


def extract_docs_from_pdf(
    session,
    path: str,
    image_path: str,
    export_images: bool = True,
    image_format: str = "jpg",
):
    """
    Extract documents from a pdf file
    """
    text_md = extract_images_text_pdf(
        path=path,
        export_images=export_images,
        image_format=image_format,
        image_path=image_path,
    )
    tables_dict = extract_tables_from_pdf(path)
    tables = list(tables_dict.values())
    loader = PyPDFLoader(path)
    docs = loader.load()

    texts = [d.page_content for d in docs]
    return texts, tables, text_md


def load_file(path):
    # load pdf file and transform into Langchain Documents
    loader = PyPDFLoader(path)
    pages = loader.load_and_split()
    return pages


def load_file_only(path):
    # load pdf file and transform into Langchain Documents
    loader = PyPDFLoader(path)
    pages = loader.load()
    return pages


def get_docs_to_add_vectorstore(pages, file, category="legal"):
    # get components to add to Faiis
    documents = []
    ids = []
    metadatas = []

    for page in pages:

        metadatas.append(
            {"page": page.metadata.get("page"), "filename": file, "category": category}
        )
        ids.append(uuid.uuid1().hex)
        documents.append(page.page_content)

    return documents, ids, metadatas


def create_documents_metadatas(files: List = [], category: str = "legal"):
    # add documents to Faiss
    documents_all = []
    metadatas_all = []
    ids_all = []

    for file in files:
        path = os.path.join("docs", file)
        pages = load_file(path)
        print(f" Loaded file {file} with {len(pages)} ")
        documents, ids, metadatas = get_docs_to_add_vectorstore(pages, file, category)
        # add documents to collection
        documents_all = documents_all + documents
        metadatas_all = metadatas_all + metadatas
        ids_all = ids_all + ids
    return documents_all, metadatas_all, ids_all


def count_pdf_pages(pdf_path):
    """
    count number of pages in a pdf file
    :param pdf_path: path to pdf file
    :return: number of pages
    """

    doc = fitz.open(pdf_path)

    num_pages = len(doc)

    return num_pages
