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
    load_sheet,
    get_sheetnames_xlsx,
    get_sheetnames_xls,
)
import logging
from src.utils import print_stack
from src.helpers import init_session_3, reset_session_3
from src.work_gemini import init_llm, create_pandas_agent
from IPython import embed


# where I am
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Create folders
path = Path(ROOT_DIR)

OUT_FOLDER, TMP_FOLDER, ANSWERS_DIR, PROMPTS_DIR, DICTS_DIR = create_folders(
    path.parent.absolute()
)
logging.info(f"ROOT Folder {ROOT_DIR}")


def change_state_3(st, placeholder):
    """
    change state after leave conversation
    params:
    st (streamlit): streamlit object
    placeholder (streamlit.empty): placeholder

    """

    st.session_state.value3 = 0
    placeholder.empty()
    reset_session_3(st, ss)
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

    if "vcol1doc3" in st.session_state and "vcol2doc3" in st.session_state:
        col1 = st.session_state["vcol1doc3"]
        col2 = st.session_state["vcol2doc3"]

    row1_1, row1_2 = st.columns((col1, col2))
    try:
        # Initialize Vars
        # Initialice state
        if "init_run_3" not in st.session_state:
            st.session_state["init_run_3"] = False
        if st.session_state["init_run_3"] == False:
            init_session_3(st, ss, col1, col2)

        with row1_1:

            # Access the uploaded ref via a key.
            if st.session_state.value3 >= 0 and st.session_state["salir_3"] == False:
                uploaded_files = st.file_uploader(
                    "Upload Excel or CSV file",
                    type=["csv", "xlsx", "xls"],
                    key="excel_loader",
                    accept_multiple_files=False,
                )  # accept_multiple_files=True,
                if uploaded_files:
                    logging.info(
                        f"Excel Extract Page: file uploaded {uploaded_files.name}"
                    )
                if uploaded_files:
                    # To read file as bytes:
                    im_bytes = uploaded_files.getvalue()
                    file_path = f"{TMP_FOLDER}/{uploaded_files.name}"
                    with open(file_path, "wb") as f:
                        f.write(im_bytes)
                        f.close()
                    if ss.excel_loader:
                        ss.pdf_ref3 = im_bytes

                    st.session_state["file_name3"] = file_path
                    st.session_state["file_history3"] = uploaded_files.name
                    st.session_state["upload_state3"] = (
                        f"Uploaded file: {uploaded_files.name}"
                    )

                st.session_state.value3 = 1  # file uploaded

            # Now you can access "pdf_ref" anywhere in your app.

            with row1_1:
                if (
                    st.session_state.value3 >= 1
                    and ss.pdf_ref3
                    and st.session_state["salir_3"] == False
                ):
                    if st.session_state["vcol1doc3"] == 50:
                        width = 700
                    elif st.session_state["vcol1doc3"] == 20:
                        width = 350
                    else:
                        width = 700
                    extension = st.session_state["file_name3"].split(".")[-1]
                    if extension == "xlsx":
                        sheet_names = get_sheetnames_xlsx(
                            st.session_state["file_name3"]
                        )
                    elif extension == "xls":
                        sheet_names = get_sheetnames_xls(st.session_state["file_name3"])
                    else:
                        filename = st.session_state["file_history3"].split(".")[0]
                        sheet_names = [filename]
                    selected_filename = st.selectbox(
                        "Select a sheet from excel file 👇",
                        sheet_names,
                        placeholder="Select a file",
                        index=None,
                        key="select_sheet",
                    )

                    if selected_filename and st.session_state["salir_3"] == False:
                        # load Dataframe to table
                        if extension in ["csv"]:
                            real_selected_filename = selected_filename + ".csv"
                        else:
                            real_selected_filename = selected_filename
                        df = load_sheet(
                            st.session_state["file_name3"],
                            real_selected_filename,
                            extension,
                        )
                        logging.info(
                            f"File: {st.session_state['file_name3']} Sheet: {real_selected_filename} contains: {len(df)} rows"
                        )
                        st.session_state["upload_state3"] = (
                            f"File: {st.session_state['file_name3']} Sheet: {real_selected_filename} contains: {len(df)} rows"
                        )
                        st.dataframe(df, width=900, key="dataframe_query_extract")
                        input_prompt = st.text_input(
                            "Introduce Name of Company to extract Information 👇",
                            key="dataframe_query_extract",
                        )
                        if (
                            input_prompt
                            and st.session_state.value3 >= 1
                            and st.session_state["salir_3"] == False
                        ):
                            pandas_df_agent = create_pandas_agent(
                                llm=st.session_state["chat3"], df=df
                            )

                            results = pandas_df_agent.invoke(input_prompt)

                            st.session_state.value3 = 2  # pages selected
                            st.session_state["upload_state3"] = (
                                f"Question:\n {input_prompt} "
                                + "\n"
                                + "Response:"
                                + "\n"
                                + results["output"]
                            )

        with row1_2:
            if st.button(
                "Leave Conversation", on_click=change_state_3, args=(st, placeholder)
            ):
                logging.info("Salir and writing history")

            with st.expander(
                "���️ Instruccion to send to Model 👇👇",
                expanded=st.session_state["expander_3"],
            ):
                _ = st.text_area(
                    "Status selection", "", key="upload_state3", height=500
                )

    except:

        # get the sys stack and log to gcloud
        st.session_state["salir_3"] = True
        placeholder.empty()
        text = print_stack()
        text = "Extract Excel Page " + text
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
    if "salir_3" not in st.session_state:
        st.session_state["salir_3"] = False

    if st.session_state["salir_3"] == False:
        placeholder_3 = st.empty()
        with placeholder_3.container():
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
            if "chat3" not in st.session_state:
                st.session_state["chat3"] = init_llm(
                    model=config.get("MODEL"), credentials=vertex_credentials
                )
            logging.info(f"Model {config.get('MODEL')} initialized")
            main(
                col1=col1,
                col2=col2,
                placeholder=placeholder_3,
                config=config,
            )
