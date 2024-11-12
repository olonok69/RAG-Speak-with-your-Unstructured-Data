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
from src.pdf_utils import count_pdf_pages
from src.helpers import init_session_1, reset_session_1
from src.work_gemini import init_embeddings, init_llm
from src.vector import (
    create_db_store_from_file,
    create_elasticsearch_store,
    add_documents_vector_store,
)
from IPython import embed
from langchain.chains import ConversationalRetrievalChain

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


def change_state_1(st, placeholder):
    """
    change state after leave conversation
    params:
    st (streamlit): streamlit object
    placeholder (streamlit.empty): placeholder

    """
    placeholder.empty()
    reset_session_1(st, ss)
    st.stop()
    del placeholder
    return


def main(
    col1,
    col2,
    placeholder,
    config,
    db_load,
):
    """
    main loop
    params:

    col1 (int): size col 1
    col2 (int): size col 2
    placeholder (streamlit.empty): placeholder
    config: Configuration Dictionary
    """
    # two columns

    if "vcol1doc" in st.session_state and "vcol2doc" in st.session_state:
        col1 = st.session_state["vcol1doc"]
        col2 = st.session_state["vcol2doc"]

    row1_1, row1_2 = st.columns((col1, col2))
    try:
        # Initialize Vars
        # Initialice state
        if "init_run_1" not in st.session_state:
            st.session_state["init_run_1"] = False
        if st.session_state["init_run_1"] == False:
            init_session_1(st, ss, col1, col2)

        with row1_1:

            # Access the uploaded ref via a key.
            if st.session_state.value1 >= 0 and st.session_state["salir_1"] == False:
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
                        ss.pdf_ref1 = im_bytes
                    numpages = count_pdf_pages(file_path)
                    logging.info(
                        f"Numero de paginas del fichero {uploaded_files.name} : {numpages}"
                    )
                    st.session_state["file_name1"] = file_path
                    st.session_state["file_history1"] = uploaded_files.name
                    st.session_state["upload_state1"] = (
                        f"Numero de paginas del fichero {uploaded_files.name} : {numpages}"
                    )
                    # in ELastic we Initialize the state to None
                    if config.get("VECTOR_STORE") == "faiss":
                        st.session_state["vector_store1"] = db_load
                    else:
                        st.session_state["vector_store1"] = None

                    logging.info(
                        f"File path {file_path} File name {uploaded_files.name}"
                    )

                st.session_state.value1 = 1  # file uploaded

            # Now you can access "pdf_ref1" anywhere in your app.
            if ss.pdf_ref1:
                with row1_1:
                    if (
                        st.session_state.value1 >= 1
                        and st.session_state["salir_1"] == False
                    ):
                        binary_data = ss.pdf_ref1
                        if st.session_state["vcol1doc"] == 50:
                            width = 900
                        elif st.session_state["vcol1doc"] == 20:
                            width = 350
                        else:
                            width = 700
                        pdf_viewer(
                            input=binary_data, width=width, height=300, key="pdf_viewer"
                        )
                if st.button("Parse pdf"):
                    if (
                        not (st.session_state["file_history1"] in onlyfiles)
                        or st.session_state["vector_store1"] == None
                    ):

                        db = add_documents_vector_store(
                            config=config,
                            session=st,
                            embeddings=st.session_state["embeddings1"],
                            db_local_folder=st.session_state["db_local_folder1"],
                            df_pdfs=df_pdfs,
                            pname=pname,
                            db_load=db_load,
                            file_path=st.session_state["file_name1"],
                        )
                        st.session_state["vector_store1"] = db

                if (
                    st.session_state["vector_store1"] != None
                    and st.session_state["salir_1"] == False
                ):
                    st.session_state["retriever1"] = st.session_state[
                        "vector_store1"
                    ].as_retriever(
                        search_kwargs={"k": int(config.get("TOP_N_RETRIEVER"))},
                        filter={"filename": st.session_state["file_history1"]},
                    )
                    st.session_state["chat_true1"] = "chat activo"
                if (
                    st.session_state["retriever1"] != None
                    and st.session_state["salir_1"] == False
                ):
                    input_prompt = st.text_input(
                        "Introduce initial query to the document paginas a extraer 👇",
                        key="pdf_query",
                    )
                    if (
                        input_prompt
                        and st.session_state.value1 >= 1
                        and st.session_state["salir_1"] == False
                    ):
                        st.session_state.value1 = 2  # pages selected
                        st.session_state["upload_state1"] = (
                            f"Intial question to Model {input_prompt}"
                        )
                        st.session_state["prompt_introduced1"] = (
                            f"Intial question to Model {input_prompt}"
                        )
                        st.session_state["chat_true1"] = "chat activo"
                        chain = ConversationalRetrievalChain.from_llm(
                            st.session_state["chat1"],
                            retriever=st.session_state["retriever1"],
                            return_source_documents=True,
                        )

                        result = chain.invoke(
                            {
                                "question": input_prompt,
                                "chat_history": st.session_state["chat_history1"],
                            }
                        )
                        st.session_state["upload_state1"] = result["answer"]
                        # add History
                        st.session_state["chat_history1"].append(
                            (input_prompt, result["answer"])
                        )
        with row1_2:
            if st.button(
                "Leave Conversation", on_click=change_state_1, args=(st, placeholder)
            ):
                logging.info("Salir and writing history")

            with st.expander(
                "���️ Instruccion to send to Model 👇👇",
                expanded=st.session_state["expander_1"],
            ):
                _ = st.text_area(
                    "Status selection", "", key="upload_state1", height=500
                )

    except:

        # get the sys stack and log to gcloud
        st.session_state["salir_1"] = True
        placeholder.empty()
        text = print_stack()
        text = "Speak with PDF Page " + text
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
    if "salir_1" not in st.session_state:
        st.session_state["salir_1"] = False

    if st.session_state["salir_1"] == False:
        # Empty placeholder for session objects
        placeholder_1 = st.empty()
        with placeholder_1.container():
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
            if "chat1" not in st.session_state:
                st.session_state["chat1"] = init_llm(
                    model=config.get("MODEL"), credentials=vertex_credentials
                )
            # Initialize embeddings models
            logging.info(f"Model {config.get('MODEL')} initialized")

            if "embeddings1" not in st.session_state:
                st.session_state["embeddings1"] = init_embeddings(
                    credentials=vertex_credentials,
                    google_api_key=config["GEMINI-API-KEY"],
                    model=config["EMBEDDINGS2"],
                )
            logging.info(f"Model Embeddings: {config.get('EMBEDDINGS2')} initialized")
            # VECTOR_STORE Faiss or Elastic
            if "db_local_folder1" not in st.session_state:
                st.session_state["db_local_folder1"] = ""
            # placeholder for multiple files
            if "db_local_file1" not in st.session_state:
                st.session_state["db_local_file1"] = ""

            if config["VECTOR_STORE"] == "faiss":
                # path to save the faiss index
                st.session_state["db_local_folder1"] = os.path.join(
                    path.parent.absolute(), config["FOLDER_PATH"]
                )
                st.session_state["db_local_file1"] = os.path.join(
                    st.session_state["db_local_folder1"], config["INDEX_NAME_FILE"]
                )

                if os.path.isfile(st.session_state["db_local_file1"]):

                    db_load = create_db_store_from_file(
                        embeddings=st.session_state["embeddings1"],
                        index_name=config["INDEX_NAME"],
                        folder_path=st.session_state["db_local_folder1"],
                    )
                    logging.info(
                        f"Number of documents in Vector Store {db_load.index.ntotal}"
                    )
                else:
                    logging.info(
                        f"Faiss {st.session_state['db_local_file1']} not Initialized"
                    )
                    db_load = None
            elif config["VECTOR_STORE"] == "elastic":
                # in elastic we create the vector store always here
                USER = os.getenv("USER")
                if platform.system() == "Windows" or (
                    platform.system() == "Linux" and USER == "olonok"
                ):
                    url = "http://localhost:9200"
                else:
                    url = config.get("ELASTIC_URL")
                db_load = create_elasticsearch_store(
                    index_name="premcloud_demo_pdf",
                    embeddings=st.session_state["embeddings1"],
                    es_url=url,
                )
                st.session_state["db_local_folder1"] = None
                st.session_state["db_local_file1"] = None
            logging.info(f"Vector store: {config.get('VECTOR_STORE')} initialized")
            main(
                col1=col1,
                col2=col2,
                placeholder=placeholder_1,
                config=config,
                db_load=db_load,
            )
