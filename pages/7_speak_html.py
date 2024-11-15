import streamlit as st
import os.path
from streamlit import session_state as ss
from pathlib import Path
from google.oauth2 import service_account
import vertexai
from dotenv import dotenv_values
import json
from src.files import (
    create_folders,
    open_table_htmls,
    create_urls_dataframe,
    load_parsed_documents,
    save_parsed_documents,
)
import logging
from src.utils import print_stack
from src.helpers import init_session_7, reset_session_7
from src.prompts import prompt_template_html
from src.work_nvidia import (
    get_llm,
    get_embeddings,
    get_tables_summary_llm,
    get_text_splitter,
    get_documents,
    generate_answer,
)
from src.vector import (
    add_documents_vector_store_speak_html,
    configure_vector_store_speak_html,
)
from src.html_utils import extract_html_content
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
pname, pname2, df_urls = open_table_htmls(ANSWERS_DIR)
onlyfiles = df_urls["url"].to_list()
if len(onlyfiles) == 0:
    pname, pname2, df_urls = create_urls_dataframe(ANSWERS_DIR)


def change_state_7(st, placeholder):
    """
    change state after leave conversation
    params:
    st (streamlit): streamlit object
    placeholder (streamlit.empty): placeholder

    """
    placeholder.empty()
    reset_session_7(st, ss)
    st.stop()
    del placeholder
    return


def main(
    col1,
    col2,
    placeholder,
    config,
):
    """
    main loop
    params:
    model (langchain_google_genai.ChatGoogleGenerativeAI): model
    embeddings_retriever: langchain_google_genai.GoogleGenerativeAIEmbeddings
    df_load: Faiss
    col1 (int): size col 1
    col2 (int): size col 2
    placeholder (streamlit.empty): placeholder
    config: Configuration Dictionary
    db_local_folder:str Path to serialize Faiss Dataset
    """
    # two columns

    if "vcol1doc7" in st.session_state and "vcol2doc7" in st.session_state:
        col1 = st.session_state["vcol1doc7"]
        col2 = st.session_state["vcol2doc7"]

    row1_1, row1_2 = st.columns((col1, col2))
    try:
        # Initialize Vars
        # Initialice state
        if "init_run_7" not in st.session_state:
            st.session_state["init_run_7"] = False
        if st.session_state["init_run_7"] == False:
            init_session_7(st, ss, col1, col2)

        with row1_1:

            # Access the uploaded ref via a key.
            if st.session_state.value7 >= 0 and st.session_state["salir_7"] == False:
                if len(df_urls) > 0:
                    st.text("Urls to analyze")
                    st.dataframe(df_urls, width=700, key="html_query_extract")

                if st.session_state["parse_html"] == 0 and (
                    int(st.session_state["index_rebuilt"]) == 1 or len(df_urls) == 0
                ):
                    my_file_path = Path(os.path.join(ANSWERS_DIR, "parsed_docs.pkl"))
                    my_file = Path(my_file_path)
                    if my_file.is_file():
                        data = load_parsed_documents(my_file_path)
                        st.session_state["documents"] = data.get("docs")
                    else:
                        logging.info(
                            f"Variable REBUILD_INDEX: {int(config.get('REBUILD_INDEX_7'))} length Dataframe: {len(df_urls)}"
                        )
                        st.session_state["parsed_htmls"] = extract_html_content(df_urls)
                        logging.info(
                            f"Speak with HTML Pages: Number of Pages Extracted {len(st.session_state['parsed_htmls'])}"
                        )
                        st.session_state["parsed_htmls"] = get_tables_summary_llm(
                            pages=st.session_state["parsed_htmls"],
                            llm=st.session_state["chat7"],
                        )
                        logging.info(
                            f"Speak with HTML Pages: Number of Pages tables summarized {len(st.session_state['parsed_htmls'])}"
                        )
                        st.session_state["documents"] = get_documents(
                            pages=st.session_state["parsed_htmls"],
                            splitter=st.session_state["text_splitter"],
                        )
                        save_parsed_documents(
                            my_file_path, {"docs": st.session_state["documents"]}
                        )
                        logging.info(
                            f"Speak with HTML Pages: Serializing parsed documents to {my_file_path}"
                        )
                    logging.info(
                        f"Speak with HTML Pages: Number of Documents {len(st.session_state['documents'])}"
                    )

                    st.session_state["parse_html"] = 1

                st.session_state.value7 = 1  # file uploaded

            # Now you can access "pdf_ref" anywhere in your app.
            if (
                len(st.session_state["documents"]) > 0
                and st.session_state["salir_7"] == False
            ) or (
                int(st.session_state["index_rebuilt"]) == 0
                and st.session_state["salir_7"] == False
            ):
                with row1_1:
                    if st.session_state.value7 >= 1:

                        if st.session_state["vcol1doc7"] == 50:
                            width = 900
                        elif st.session_state["vcol1doc7"] == 20:
                            width = 350
                        else:
                            width = 700

                if st.button(
                    "Add Documents to Vector Store",
                    disabled=st.session_state["chat_true7"] == "chat activo",
                ):
                    if (
                        st.session_state["vector_store7"] == None
                        and int(st.session_state["index_rebuilt"]) == 1
                    ) or (
                        int(st.session_state["index_rebuilt"]) == 1
                        and config["VECTOR_STORE_HTML"] == "elastic"
                    ):

                        db = add_documents_vector_store_speak_html(
                            config=config,
                            session=st,
                            db_load=st.session_state["vector_store7"],
                            db_local_folder=st.session_state["db_local_folder"],
                            embeddings=st.session_state["embeddings7"],
                        )
                        st.session_state["vector_store7"] = db
                        st.session_state["chat_true7"] = "chat activo"
                        st.session_state["index_rebuilt"] = 0
                        st.session_state.value7 = 2
                    else:
                        st.session_state["chat_true7"] = "chat activo"
                        st.session_state.value7 = 2
                logging.info(
                    f"Speak with HTML Pages: Status Chat {st.session_state['chat_true7']} Vector Store: {st.session_state['vector_store7'] != None}"
                )
                if (
                    st.session_state["vector_store7"] != None
                    and st.session_state["chat_true7"] == "chat activo"
                ):
                    input_prompt = st.text_input(
                        "Introduce initial query to the html documents 👇",
                        key="html_query",
                        # placeholder="Selecciona paginas seguidas por comas. Ejemplo 1,3,4,5",
                        # disabled=st.session_state["buttom_send_not_clicked"],
                    )
                    if input_prompt and st.session_state.value7 >= 1:
                        st.session_state.value7 = 2  # pages selected
                        st.session_state["upload_state7"] = (
                            f"Intial question to Model {input_prompt}"
                        )
                        st.session_state["prompt_introduced7"] = (
                            f"Intial question to Model {input_prompt}"
                        )
                        st.session_state["chat_true7"] = "chat activo"

                        result = generate_answer(
                            st.session_state["chat7"],
                            st.session_state["vector_store7"],
                            prompt_template_html,
                            input_prompt,
                        )
                        st.session_state["upload_state7"] = result
                        # add History
                        st.session_state["chat_history7"].append((input_prompt, result))
        with row1_2:
            if st.button("Salir", on_click=change_state_7, args=(st, placeholder)):
                logging.info("Salir and writing history")

            with st.expander(
                "���️ Instruccion to send to Model 👇👇",
                expanded=st.session_state["expander_7"],
            ):
                _ = st.text_area(
                    "Status selection", "", key="upload_state7", height=500
                )

    except:

        # get the sys stack and log to gcloud
        st.session_state["salir_7"] = True
        st.session_state["chat_true7"] = "chat no activo"
        placeholder.empty()
        text = print_stack()
        text = "Speak with HTML Pages" + text
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
    # Empty placeholder for session objects
    if "salir_7" not in st.session_state:
        st.session_state["salir_7"] = False

    if st.session_state["salir_7"] == False:
        placeholder_7 = st.empty()
        with placeholder_7.container():
            col1, col2 = 50, 50
            ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
            path_root_dir = Path(ROOT_DIR)
            config = dotenv_values(
                os.path.join(path_root_dir.parent.absolute(), "keys", ".env")
            )

            with open(
                os.path.join(
                    path_root_dir.parent.absolute(),
                    "keys",
                    "complete-tube-421007-208a4862c992.json",
                )
            ) as source:
                info = json.load(source)
            # setup credentials and INIT vertex AI and vars
            vertex_credentials = service_account.Credentials.from_service_account_info(
                info
            )
            google_api_key = config["GEMINI-API-KEY"]
            os.environ["GEMINI_API_KEY"] = google_api_key
            os.environ["NVIDIA_API_KEY"] = config.get("NVIDIA_API_KEY")
            # setup rebuild Elastic Index
            if "index_rebuilt" not in st.session_state:
                st.session_state["index_rebuilt"] = config.get("REBUILD_INDEX_7")
            if "parse_html" not in st.session_state:
                st.session_state["parse_html"] = 0
            vertexai.init(
                project=config["PROJECT"],
                location=config["REGION"],
                credentials=vertex_credentials,
            )
            # Initialize Model
            if "chat7" not in st.session_state:
                st.session_state["chat7"] = get_llm(model=config.get("NVIDIA_MODEL"))

            logging.info(f"Model {config.get('NVIDIA_MODEL')} initialized")

            if "embeddings7" not in st.session_state:
                st.session_state["embeddings7"] = get_embeddings(
                    model=config.get("NVIDIA_EMBEDDINGS")
                )
                logging.info(
                    f"Model Embeddings: {config.get('NVIDIA_EMBEDDINGS')} initialized"
                )
            if "text_splitter" not in st.session_state:
                st.session_state["text_splitter"] = get_text_splitter(
                    model=config.get("TEXT_SPLITTER_MODEL")
                )
                logging.info(
                    f"Splitter Model: {config.get('TEXT_SPLITTER_MODEL')} initialized"
                )
            #########################################################################################
            # VECTOR_STORE Faiss or Elastic
            if "db_local_folder" not in st.session_state:
                st.session_state["db_local_folder"] = ""
            # placeholder for multiple files
            if "db_local_file" not in st.session_state:
                st.session_state["db_local_file"] = ""
            if "vector_store7" not in st.session_state:

                (
                    st.session_state["vector_store7"],
                    st.session_state["db_local_folder"],
                    st.session_state["db_local_file"],
                ) = configure_vector_store_speak_html(
                    config=config,
                    path=path_root_dir,
                    embeddings=st.session_state["embeddings7"],
                )
            logging.info(f"Vector store: {config.get('VECTOR_STORE_HTML')} initialized")
            #########################################################################################

            main(
                col1=col1,
                col2=col2,
                placeholder=placeholder_7,
                config=config,
            )
