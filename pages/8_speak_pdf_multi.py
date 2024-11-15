import streamlit as st
import os.path
from streamlit_pdf_viewer import pdf_viewer
from streamlit import session_state as ss
from pathlib import Path
from google.oauth2 import service_account
import vertexai
from dotenv import dotenv_values
import json
from src.files import create_folders, open_table_pdfs
import logging
import platform
from src.utils import print_stack
from src.pdf_utils import (
    count_pdf_pages,
    extract_docs_from_pdf,
)
from src.helpers import init_session_8, reset_session_8
from src.work_gemini import (
    init_embeddings,
    init_llm,
    generate_text_summaries,
    generate_img_summaries,
    multi_modal_rag_chain,
)
from src.vector import (
    create_multi_vectorstore,
    create_multivector_retriever,
    add_docs_multi_vector_retriever,
)
from IPython import embed


# where I am
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Create folders
path = Path(ROOT_DIR)

OUT_FOLDER, TMP_FOLDER, ANSWERS_DIR, PROMPTS_DIR, DICTS_DIR = create_folders(
    path.parent.absolute()
)
logging.info(f"ROOT Folder {ROOT_DIR}")
# open table with all prompts
pname, pname2, df_pdfs = open_table_pdfs(ANSWERS_DIR)
onlyfiles = df_pdfs["filename"].to_list()


def change_state_8(st, placeholder):
    """
    change state after leave conversation
    params:
    st (streamlit): streamlit object
    placeholder (streamlit.empty): placeholder

    """
    placeholder.empty()
    reset_session_8(st, ss)
    st.stop()
    del placeholder
    return


def click_button_parse(st):
    st.session_state["click_button_parse8"] = True
    return


def main(col1, col2, placeholder, config, credentials):
    """
    main loop
    params:

    col1 (int): size col 1
    col2 (int): size col 2
    placeholder (streamlit.empty): placeholder
    config: Configuration Dictionary
    credentials: vertexai credentials
    """
    # two columns

    if "vcol1doc" in st.session_state and "vcol2doc" in st.session_state:
        col1 = st.session_state["vcol1doc"]
        col2 = st.session_state["vcol2doc"]

    row1_1, row1_2 = st.columns((col1, col2))
    try:
        # Initialize Vars
        # Initialice state
        if "init_run_8" not in st.session_state:
            st.session_state["init_run_8"] = False
        if st.session_state["init_run_8"] == False:
            init_session_8(st, ss, col1, col2)

        with row1_1:

            # Access the uploaded ref via a key.
            if st.session_state.value8 >= 0 and st.session_state["salir_8"] == False:
                uploaded_files = st.file_uploader(
                    "Upload PDF file",
                    type=("pdf"),
                    key="pdf",
                    accept_multiple_files=False,
                )  # accept_multiple_files=True,
                if uploaded_files:
                    logging.info(
                        f"Speak with PDF Page: file uploaded {uploaded_files.name}"
                    )
                if uploaded_files:
                    # To read file as bytes:
                    im_bytes = uploaded_files.getvalue()
                    file_path = f"{TMP_FOLDER}/{uploaded_files.name}"
                    with open(file_path, "wb") as f:
                        f.write(im_bytes)
                        f.close()
                    if ss.pdf:
                        ss.pdf_ref8 = im_bytes
                    numpages = count_pdf_pages(file_path)
                    logging.info(
                        f"Numero de paginas del fichero {uploaded_files.name} : {numpages}"
                    )
                    st.session_state["file_name8"] = file_path
                    st.session_state["file_history8"] = uploaded_files.name
                    st.session_state["upload_state8"] = (
                        f"Numero de paginas del fichero {uploaded_files.name} : {numpages}"
                    )
                    # in ELastic we Initialize the state to None

                    logging.info(
                        f"File path {file_path} File name {uploaded_files.name}"
                    )

                st.session_state.value8 = 1  # file uploaded

            # Now you can access "pdf_ref1" anywhere in your app.
            if ss.pdf_ref8:
                with row1_1:
                    if (
                        st.session_state.value8 >= 1
                        and st.session_state["salir_8"] == False
                    ):
                        binary_data = ss.pdf_ref8
                        if st.session_state["vcol1doc"] == 50:
                            width = 900
                        elif st.session_state["vcol1doc"] == 20:
                            width = 350
                        else:
                            width = 700
                        pdf_viewer(
                            input=binary_data, width=width, height=300, key="pdf_viewer"
                        )
                    if st.button("Parse pdf", on_click=click_button_parse, args=(st,)):
                        if (
                            not (st.session_state["file_history8"] in onlyfiles)
                            or st.session_state["vector_store8"] == None
                        ):
                            if st.session_state["fill_retriever8"] == False:
                                # Extract text and images
                                (
                                    st.session_state["pymupdfllm_text"],
                                    st.session_state["pymupdfllm_tables"],
                                    st.session_state["pymupdfllm_md"],
                                ) = extract_docs_from_pdf(
                                    session=ss,
                                    path=st.session_state["file_name8"],
                                    export_images=True,
                                    image_format="jpg",
                                    image_path=os.path.join(TMP_FOLDER, "images"),
                                )

                                if (
                                    len(st.session_state["pymupdfllm_text"]) > 0
                                    and st.session_state["salir_8"] == False
                                    and len(st.session_state["pymupdfllm_md"]) > 0
                                ):
                                    config.get("MODEL")
                                    # Text summaries
                                    (
                                        st.session_state["text_summaries"],
                                        st.session_state["table_summaries"],
                                    ) = generate_text_summaries(
                                        model=config.get("MODEL"),
                                        credentials=credentials,
                                        texts=st.session_state["pymupdfllm_text"],
                                        tables=st.session_state["pymupdfllm_tables"],
                                        summarize_texts=False,
                                    )
                                    # Image summaries
                                    (
                                        st.session_state["img_base64_list"],
                                        st.session_state["image_summaries"],
                                    ) = generate_img_summaries(
                                        path=os.path.join(TMP_FOLDER, "images"),
                                        model=config.get("MODEL"),
                                        credentials=credentials,
                                        type_image="jpg",
                                    )

                                    # add documents and Images to Vector Store
                                    st.session_state["retriever8"] = (
                                        add_docs_multi_vector_retriever(
                                            retriever=st.session_state["retriever8"],
                                            text_summaries=st.session_state[
                                                "text_summaries"
                                            ],
                                            texts=st.session_state["pymupdfllm_text"],
                                            tables=st.session_state[
                                                "pymupdfllm_tables"
                                            ],
                                            table_summaries=st.session_state[
                                                "table_summaries"
                                            ],
                                            image_summaries=st.session_state[
                                                "image_summaries"
                                            ],
                                            images=st.session_state["img_base64_list"],
                                            id_key=config.get(
                                                "MULTIVECTOR_RETRIEVER_KEY"
                                            ),
                                        )
                                    )
                                    st.session_state["upload_state8"] = (
                                        "Documents added to Vector Store"
                                    )
                                    st.session_state["fill_retriever8"] = True
                    if (
                        st.session_state["click_button_parse8"] == True
                        and st.session_state["fill_retriever8"] == True
                    ):
                        if (
                            len(
                                st.session_state["retriever8"].vectorstore.get()[
                                    "documents"
                                ]
                            )
                            > 0
                            and st.session_state["salir_8"] == False
                        ):
                            input_prompt = st.text_input(
                                "Introduce query to the document  👇👇",
                                key="multi_query",
                            )
                            st.session_state["chat_true8"] = "chat activo"

                            if (
                                input_prompt
                                and st.session_state.value8 >= 1
                                and st.session_state["salir_8"] == False
                            ):
                                # retriever, model_name, credentials
                                chain_multimodal_rag = multi_modal_rag_chain(
                                    retriever=st.session_state["retriever8"],
                                    model_name=config.get("MODEL"),
                                    credentials=credentials,
                                )

                                result = chain_multimodal_rag.invoke(input_prompt)
                                st.session_state.value8 = 2  # pages selected
                                st.session_state["upload_state8"] = (
                                    f"Intial question to Model {input_prompt}"
                                )
                                st.session_state["prompt_introduced8"] = (
                                    f"Intial question to Model {input_prompt}"
                                )
                                st.session_state["chat_true8"] = "chat activo"

                                st.session_state["upload_state8"] = result
                                # add History
                                st.session_state["chat_history8"].append(
                                    (input_prompt, result)
                                )
        with row1_2:
            if st.button("Salir", on_click=change_state_8, args=(st, placeholder)):
                logging.info("Salir and writing history")

            with st.expander(
                "���️ Instruccion to send to Model 👇👇",
                expanded=st.session_state["expander_8"],
            ):
                _ = st.text_area(
                    "Status selection", "", key="upload_state8", height=500
                )

    except:

        # get the sys stack and log to gcloud
        st.session_state["salir_8"] = True
        placeholder.empty()
        text = print_stack()
        text = "Speak with PDF Multi Page " + text
        logging.error(text)
    return


if __name__ == "__main__":
    global col1, col2
    st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
    # go to login page if not authenticated
    if (
        st.session_state["authentication_status"] == None
        or st.session_state["authentication_status"] == False
    ):
        st.session_state.runpage = "pages.py"
        st.switch_page("pages.py")
    if "salir_8" not in st.session_state:
        st.session_state["salir_8"] = False

    if st.session_state["salir_8"] == False:
        # Empty placeholder for session objects
        placeholder_8 = st.empty()
        with placeholder_8.container():
            col1, col2 = 50, 50
            ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
            path = Path(ROOT_DIR)
            config = dotenv_values(os.path.join(path.parent.absolute(), "keys", ".env"))

            with open(
                os.path.join(
                    path.parent.absolute(),
                    "keys",
                    "complete-tube-421007-208a4862c992.json",
                )
            ) as source:
                info = json.load(source)
            # setup credential
            vertex_credentials = service_account.Credentials.from_service_account_info(
                info
            )
            google_api_key = config["GEMINI-API-KEY"]
            os.environ["GEMINI_API_KEY"] = google_api_key
            # setup rebuild Elastic Index

            vertexai.init(
                project=config["PROJECT"],
                location=config["REGION"],
                credentials=vertex_credentials,
            )
            # Initialize Model
            if "chat8" not in st.session_state:
                st.session_state["chat8"] = init_llm(
                    model=config.get("MODEL"), credentials=vertex_credentials
                )
            # Initialize embeddings models
            logging.info(f"Model {config.get('MODEL')} initialized")

            if "embeddings8" not in st.session_state:
                st.session_state["embeddings8"] = init_embeddings(
                    credentials=vertex_credentials,
                    google_api_key=config["GEMINI-API-KEY"],
                    model=config["EMBEDDINGS2"],
                )
            logging.info(f"Model Embeddings: {config.get('EMBEDDINGS2')} initialized")
            # VECTOR_STORE Faiss or Elastic
            if "db_local_folder8" not in st.session_state:
                st.session_state["db_local_folder8"] = ""
            # placeholder for multiple files
            if "db_local_file8" not in st.session_state:
                st.session_state["db_local_file8"] = ""

            if config["VECTOR_STORE_MULTI"] == "chroma":
                # path to save the faiss index
                st.session_state["vector_store8"] = create_multi_vectorstore(
                    collection_name=config.get("MULTIVECTOR_COLLECTION_NAME"),
                    embeddings_model=config.get("MULTIVECTOR_EMBEDDINGS"),
                    credentials=vertex_credentials,
                )
            logging.info(
                f"Vector store: {config.get('VECTOR_STORE_MULTI')} initialized. Embeddings: {config.get('MULTIVECTOR_EMBEDDINGS')}"
            )
            if "retriever8" not in st.session_state:
                st.session_state["retriever8"] = create_multivector_retriever(
                    key=config.get("MULTIVECTOR_RETRIEVER_KEY"),
                    vectorstore=st.session_state["vector_store8"],
                )
            logging.info("Multivector Retriever initialized.")
            main(
                col1=col1,
                col2=col2,
                placeholder=placeholder_8,
                config=config,
                credentials=vertex_credentials,
            )
