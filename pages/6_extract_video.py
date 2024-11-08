import streamlit as st
import os.path
from streamlit import session_state as ss
from pathlib import Path
from google.oauth2 import service_account
import vertexai
from dotenv import dotenv_values
import json
from src.files import create_folders
import logging
from src.utils import print_stack
from src.helpers import init_session_6, reset_session_6
from src.work_gemini import init_model
from IPython import embed
from vertexai.generative_models import Part
import base64

# where I am
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Create folders
path = Path(ROOT_DIR)

OUT_FOLDER, TMP_FOLDER, ANSWERS_DIR, PROMPTS_DIR, DICTS_DIR = create_folders(
    path.parent.absolute()
)
logging.info(f"ROOT Folder {ROOT_DIR}")


def change_state_6(st):
    st.session_state["salir_6"] = True
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

    if "vcol1doc6" in st.session_state and "vcol2doc6" in st.session_state:
        col1 = st.session_state["vcol1doc6"]
        col2 = st.session_state["vcol2doc6"]

    row1_1, row1_2 = st.columns((col1, col2))
    try:
        # Initialize Vars
        # Initialice state
        if "init_run_6" not in st.session_state:
            st.session_state["init_run_6"] = False
        if st.session_state["init_run_6"] == False:
            init_session_6(st, ss, col1, col2)

        with row1_1:

            # Access the uploaded ref via a key.
            if st.session_state.value6 >= 0 and st.session_state["salir_6"] == False:
                uploaded_files = st.file_uploader(
                    "Upload Audio file",
                    type=["mp4", "wav", "mp3"],
                    key="video_loader",
                    accept_multiple_files=False,
                    disabled=st.session_state["buttom_send_not_clicked6"],
                )  # accept_multiple_files=True,
                if uploaded_files:
                    logging.info(f"Video file uploaded {uploaded_files.name}")
                if uploaded_files:
                    # To read file as bytes:
                    im_bytes = uploaded_files.getvalue()
                    file_path = f"{TMP_FOLDER}/{uploaded_files.name}"
                    with open(file_path, "wb") as f:
                        f.write(im_bytes)
                        f.close()
                    if ss.video_loader:
                        ss.pdf_ref6 = im_bytes

                    st.session_state["file_name6"] = file_path
                    st.session_state["file_history6"] = uploaded_files.name
                    st.session_state["upload_state6"] = (
                        f"Uploaded file: {uploaded_files.name}"
                    )

                st.session_state.value6 = 1  # file uploaded

            # Now you can access "pdf_ref" anywhere in your app.

            with row1_1:
                if (
                    st.session_state.value6 >= 1
                    and ss.pdf_ref6
                    and st.session_state["salir_6"] == False
                ):
                    binary_data = ss.pdf_ref6
                    if st.session_state["vcol1doc6"] == 50:
                        width = 700
                    elif st.session_state["vcol1doc6"] == 20:
                        width = 350
                    else:
                        width = 700
                    st.video(st.session_state["file_name6"])

                    input_prompt = st.text_input(
                        "Introduce Instruction: 👇👇",
                        key="input_video",
                    )
                    if input_prompt and st.session_state.value6 >= 1:

                        video1 = base64.b64encode(binary_data).decode("utf8")
                        video1 = Part.from_data(
                            mime_type="video/mp4",
                            data=video1,
                        )
                        contents = [video1, input_prompt]
                        # embed()
                        responses = st.session_state["chat6"].generate_content(contents)

                        st.session_state.value6 = 2  # pages selected
                        st.session_state["upload_state6"] = (
                            f"Question:\n {input_prompt} "
                            + "\n"
                            + "Response:"
                            + "\n"
                            + responses.text
                        )

        with row1_2:
            if st.button("Salir", on_click=change_state_6, args=(st,)):
                st.session_state["salir_6"] = True
                placeholder.empty()
                reset_session_6(st, ss)
                st.stop()
                del placeholder

            with st.expander(
                "���️ Instruction to send to Model 👇👇",
                expanded=st.session_state["expander_6"],
            ):
                _ = st.text_area(
                    "Status selection", "", key="upload_state6", height=500
                )

    except:

        # get the sys stack and log to gcloud
        st.session_state["salir_6"] = True
        placeholder.empty()
        text = print_stack()
        text = "Extract Video Page " + text
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
    if "salir_6" not in st.session_state:
        st.session_state["salir_6"] = False

    if st.session_state["salir_6"] == False:
        placeholder_6 = st.empty()
        with placeholder_6.container():
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
            if "chat6" not in st.session_state:
                st.session_state["chat6"] = init_model(config=config)
            logging.info(f"Model {config.get('MODEL')} initialized")
            main(
                col1=col1,
                col2=col2,
                placeholder=placeholder_6,
                config=config,
            )
