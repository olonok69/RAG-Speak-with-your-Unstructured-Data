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
from src.helpers import init_session_5, reset_session_5
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


def change_state_5(st, placeholder):
    """
    change state after leave conversation
    params:
    st (streamlit): streamlit object
    placeholder (streamlit.empty): placeholder

    """

    placeholder.empty()
    reset_session_5(st, ss)
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

    if "vcol1doc5" in st.session_state and "vcol2doc5" in st.session_state:
        col1 = st.session_state["vcol1doc5"]
        col2 = st.session_state["vcol2doc5"]

    row1_1, row1_2 = st.columns((col1, col2))
    try:
        # Initialize Vars
        # Initialice state
        if "init_run_5" not in st.session_state:
            st.session_state["init_run_5"] = False
        if st.session_state["init_run_5"] == False:
            init_session_5(st, ss, col1, col2)

        with row1_1:

            # Access the uploaded ref via a key.
            if st.session_state.value5 >= 0 and st.session_state["salir_5"] == False:
                uploaded_files = st.file_uploader(
                    "Upload Audio file",
                    type=["mp3", "wav", "m4a", "flac"],
                    key="audio_loader",
                    accept_multiple_files=False,
                )  # accept_multiple_files=True,
                if uploaded_files:
                    logging.info(f"Audio Page: file uploaded {uploaded_files.name}")
                if uploaded_files:
                    # To read file as bytes:
                    im_bytes = uploaded_files.getvalue()
                    file_path = f"{TMP_FOLDER}/{uploaded_files.name}"
                    with open(file_path, "wb") as f:
                        f.write(im_bytes)
                        f.close()
                    if ss.audio_loader:
                        ss.pdf_ref5 = im_bytes

                    st.session_state["file_name5"] = file_path
                    st.session_state["file_history5"] = uploaded_files.name
                    st.session_state["upload_state5"] = (
                        f"Uploaded file: {uploaded_files.name}"
                    )

                st.session_state.value5 = 1  # file uploaded

            # Now you can access "pdf_ref" anywhere in your app.

            with row1_1:
                if (
                    st.session_state.value5 >= 1
                    and ss.pdf_ref5
                    and st.session_state["salir_5"] == False
                ):
                    binary_data = ss.pdf_ref5
                    if st.session_state["vcol1doc5"] == 50:
                        width = 700
                    elif st.session_state["vcol1doc5"] == 20:
                        width = 350
                    else:
                        width = 700
                    st.audio(st.session_state["file_name5"])

                    input_prompt = st.text_input(
                        "Introduce Instruction 👇👇",
                        key="input_audio",
                    )
                    if (
                        input_prompt
                        and st.session_state.value5 >= 1
                        and st.session_state["salir_5"] == False
                    ):

                        audio1 = base64.b64encode(binary_data).decode("utf8")
                        audio = Part.from_data(
                            mime_type="audio/wav",
                            data=audio1,
                        )

                        contents = [audio, input_prompt]

                        responses = st.session_state["chat5"].generate_content(contents)

                        st.session_state.value5 = 2  # pages selected
                        st.session_state["upload_state5"] = (
                            f"Question:\n {input_prompt} "
                            + "\n"
                            + "Response:"
                            + "\n"
                            + str(responses.text)
                        )

        with row1_2:
            if st.button("Salir", on_click=change_state_5, args=(st, placeholder)):
                logging.info("Salir and writing history")

            with st.expander(
                "���️ Instruction to send to Model 👇",
                expanded=st.session_state["expander_5"],
            ):
                _ = st.text_area("Status selection", key="upload_state5", height=500)

    except:

        # get the sys stack and log to gcloud
        st.session_state["salir_5"] = True
        placeholder.empty()
        text = print_stack()
        text = "Extract Audio Page " + text
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
    if "salir_5" not in st.session_state:
        st.session_state["salir_5"] = False

    if st.session_state["salir_5"] == False:
        placeholder_5 = st.empty()
        with placeholder_5.container():
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
            if "chat5" not in st.session_state:
                st.session_state["chat5"] = init_model(config=config)
                logging.info(f"Model {config.get('MODEL')} initialized")
            main(
                col1=col1,
                col2=col2,
                placeholder=placeholder_5,
                config=config,
            )
