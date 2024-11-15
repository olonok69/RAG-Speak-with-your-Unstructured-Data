import streamlit as st
import os.path
from streamlit_pdf_viewer import pdf_viewer
from streamlit import session_state as ss
from pathlib import Path
from google.oauth2 import service_account
import vertexai
from dotenv import dotenv_values
import json
from src.files import create_folders
import logging
from src.utils import print_stack
from src.pdf_utils import count_pdf_pages, load_file_only
from src.helpers import init_session_2, reset_session_2
from src.work_gemini import init_llm
from IPython import embed
from src.prompts import parser, prompt_epd

# where I am
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Create folders
path = Path(ROOT_DIR)

OUT_FOLDER, TMP_FOLDER, ANSWERS_DIR, PROMPTS_DIR, DICTS_DIR = create_folders(
    path.parent.absolute()
)
logging.info(f"ROOT Folder {ROOT_DIR}")


def change_state_2(st, placeholder):
    """
    change state after leave conversation
    params:
    st (streamlit): streamlit object
    placeholder (streamlit.empty): placeholder

    """
    placeholder.empty()
    reset_session_2(st, ss)
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
    col1 (int): size col 1
    col2 (int): size col 2
    placeholder (streamlit.empty): placeholder
    config: Configuration Dictionary
    """
    # two columns

    if "vcol1doc2" in st.session_state and "vcol2doc2" in st.session_state:
        col1 = st.session_state["vcol1doc2"]
        col2 = st.session_state["vcol2doc2"]

    row1_1, row1_2 = st.columns((col1, col2))
    try:
        # Initialize Vars
        # Initialice state
        if "init_run_2" not in st.session_state:
            st.session_state["init_run_2"] = False
        if st.session_state["init_run_2"] == False:
            init_session_2(st, ss, col1, col2)

        with row1_1:

            # Access the uploaded ref via a key.
            if st.session_state.value2 >= 0 and st.session_state["salir_2"] == False:
                uploaded_files = st.file_uploader(
                    "Upload PDF file",
                    type=("pdf"),
                    key="uploader_pdf",
                    accept_multiple_files=False,
                )  # accept_multiple_files=True,
                if uploaded_files:
                    logging.info(f"Gemini 1 Page: file uploaded {uploaded_files.name}")
                if uploaded_files:
                    # To read file as bytes:
                    im_bytes = uploaded_files.getvalue()
                    file_path = f"{TMP_FOLDER}/{uploaded_files.name}"
                    with open(file_path, "wb") as f:
                        f.write(im_bytes)
                        f.close()
                    if ss.uploader_pdf:
                        ss.pdf_ref2 = im_bytes
                    numpages = count_pdf_pages(file_path)
                    logging.info(
                        f"Numero de paginas del fichero {uploaded_files.name} : {numpages}"
                    )
                    st.session_state["file_name2"] = file_path
                    st.session_state["file_history2"] = uploaded_files.name
                    st.session_state["upload_state2"] = (
                        f"Numero de paginas del fichero {uploaded_files.name} : {numpages}"
                    )

                st.session_state.value2 = 1  # file uploaded

            # Now you can access "pdf_ref" anywhere in your app.
            if ss.pdf_ref2 and st.session_state["salir_2"] == False:
                with row1_1:
                    if st.session_state.value2 >= 1:

                        binary_data = ss.pdf_ref2
                        if st.session_state["vcol1doc2"] == 50:
                            width = 800
                        elif st.session_state["vcol1doc2"] == 20:
                            width = 350
                        else:
                            width = 800
                            # Visualize PDF
                        pdf_viewer(
                            input=binary_data,
                            width=width,
                            height=300,
                            key="pdf_viewer2",
                        )

                        pages = load_file_only(st.session_state["file_name2"])
                        input_prompt = st.text_input(
                            "Introduce Name of Company to extract Information 👇",
                            key="pdf_query_extract2",
                        )
                        if (
                            input_prompt
                            and st.session_state.value2 >= 1
                            and st.session_state["salir_2"] == False
                        ):
                            document_query = (
                                f"Extract information of company {input_prompt} from this document report: "
                                + pages[0].page_content
                            )

                            _input = prompt_epd.format_prompt(question=document_query)
                            output = st.session_state["chat2"].invoke(
                                _input.to_messages()
                            )
                            parsed = parser.parse(output.content)

                            st.session_state.value2 = 2  # pages selected
                            st.session_state["upload_state2"] = (
                                f"Extract information of company {input_prompt} from this document report: "
                                + "\n"
                                + "Response:"
                                + "\n"
                                + parsed.model_dump_json()
                            )

        with row1_2:
            if st.button("Salir", on_click=change_state_2, args=(st, placeholder)):
                logging.info("Salir and writing history")

            with st.expander(
                "���️ Instruccion to send to Model 👇👇",
                expanded=st.session_state["expander_2"],
            ):
                _ = st.text_area(
                    "Status selection", "", key="upload_state2", height=500
                )

    except:

        # get the sys stack and log to gcloud
        st.session_state["salir_2"] = True
        placeholder_2.empty()
        text = print_stack()
        text = "Gemini 1 Page " + text
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
    if "salir_2" not in st.session_state:
        st.session_state["salir_2"] = False

    if st.session_state["salir_2"] == False:
        placeholder_2 = st.empty()
        with placeholder_2.container():
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
            vertexai.init(
                project=config["PROJECT"],
                location=config["REGION"],
                credentials=vertex_credentials,
            )
            # Initialize Model
            if "chat2" not in st.session_state:
                st.session_state["chat2"] = init_llm(
                    model=config.get("MODEL"), credentials=vertex_credentials
                )
            logging.info(f"Model {config.get('MODEL')} initialized")

            main(
                col1=col1,
                col2=col2,
                placeholder=placeholder_2,
                config=config,
            )
