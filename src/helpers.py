import copy
import datetime
import pandas as pd
import uuid
import datetime
from typing import List
from src.work_gemini import start_chat
from pathlib import Path


def write_history_1(st):
    """
    Write history to file 1 doc
    param: st  session
    """
    text = ""
    list1 = copy.deepcopy(st.session_state["chat_answers_history"])
    list2 = copy.deepcopy(st.session_state["user_prompt_history"])

    if len(st.session_state["chat_answers_history"]) > 1:
        list1.reverse()

    if len(st.session_state["user_prompt_history"]) > 1:
        list2.reverse()

    for i, j in zip(list1, list2):
        text = text + "user :" + j + "\n"
        text = text + "assistant :" + i + "\n"

    now = datetime.datetime.now()
    now = now.strftime("%Y-%m-%d_%H-%M-%S")

    with open(
        f"answers/{st.session_state['file_history']}_{now}_history.txt",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(text)
        f.close()
    return


def write_history_multi(st):
    """
    Write history to multi files option
    param: st  session
    """
    text = ""
    list1 = copy.deepcopy(st.session_state["chat_answers_history"])
    list2 = copy.deepcopy(st.session_state["user_prompt_history"])

    if len(st.session_state["chat_answers_history"]) > 1:
        list1.reverse()

    if len(st.session_state["user_prompt_history"]) > 1:
        list2.reverse()

    for i, j in zip(list1, list2):
        text = text + "user : " + j + "\n"
        text = text + "assistant : " + i + "\n"
    text0 = ""
    for file in st.session_state["multi_file_name"]:
        text0 = text0 + file.replace(".pdf", "") + "_"
    text0 = text0[:-1]
    now = datetime.datetime.now()
    now = now.strftime("%Y-%m-%d_%H-%M-%S")
    with open(f"answers/{text0}_{now}_history.txt", "w", encoding="utf-8") as f:
        f.write(text)
        f.close()
    return


def open_popup(st):
    """
    Open popup to save content
    """
    if st.session_state["buttom_popup"] != "no_buttom":
        with st.popover("Open popover"):
            st.markdown("Pega Contenido a Salvar de este fichero 👇")
            txt = st.text_input("Paste here the content you want to save")
        if len(txt) > 0:
            with open(f"answers/test.txt", "w") as f:
                f.write(txt)
                f.close()


def init_session_1(st, ss, col1, col2):
    """
    initialize session state for multiple files option
    param: st  session
    param: ss  session state
    param: model  chat (gemini model)
    """

    if "chat_history1" not in st.session_state:
        st.session_state["chat_history1"] = []
    if "vector_store1" not in st.session_state:
        st.session_state["vector_store1"] = None
    if "retriever1" not in st.session_state:
        st.session_state["retriever1"] = None
    # placeholder for multiple files
    if "file_name1" not in st.session_state:
        st.session_state["file_name1"] = "no file"
    if "upload_state1" not in st.session_state:
        st.session_state["upload_state1"] = ""
    if "file_history1" not in st.session_state:
        st.session_state["file_history1"] = "no file"
    if "prompt_introduced1" not in st.session_state:
        st.session_state["prompt_introduced1"] = ""
    if "chat_true1" not in st.session_state:
        st.session_state["chat_true1"] = "no_chat"
    if "pdf_ref1" not in ss:
        ss.pdf_ref1 = None
    if "value1" not in st.session_state:
        st.session_state.value1 = 0
    # buttom send to gemini
    if "vcol1doc" not in st.session_state:
        st.session_state["vcol1doc"] = col1
    if "vcol2doc" not in st.session_state:
        st.session_state["vcol2doc"] = col2
    if "expander_1" not in st.session_state:
        st.session_state["expander_1"] = True
    st.session_state["init_run_1"] = True
    return


def reset_session_1(st, ss):
    """
    Delete session state for multiple files option
    param: st  session
    param: ss  session state
    param: model  chat (gemini model)
    """

    del st.session_state["chat_history1"]

    del st.session_state["chat1"]
    del st.session_state["vector_store1"]
    del st.session_state["embeddings1"]
    del st.session_state["retriever1"]
    # placeholder for multiple files
    del st.session_state["file_name1"]
    del st.session_state["file_history1"]
    del st.session_state["prompt_introduced1"]
    del st.session_state["chat_true1"]
    del ss.pdf_ref
    del st.session_state.value
    # buttom send to gemini
    del st.session_state["vcol1doc"]
    del st.session_state["vcol2doc"]
    del st.session_state["expander_1"]
    del st.session_state["init_run_1"]
    # delete objects
    del st.session_state["pdf"]
    del st.session_state["pdf_viewer"]
    del st.session_state["pdf_query"]
    del st.session_state["upload_state1"]
    del st.session_state["salir_1"]

    return


def init_session_4(st, ss, col1, col2):
    """
    initialize session state for multiple files option
    params:
    param: st  session
    param: ss  session state
    param: col1  size col 1
    param: col2  size col 2
    """

    if "chat4" not in st.session_state:
        st.session_state["chat4"] = None
    # placeholder for multiple files
    if "file_name4" not in st.session_state:
        st.session_state["file_name4"] = "no file"
    if "file_history4" not in st.session_state:
        st.session_state["file_history4"] = "no file"
    if "upload_state4" not in st.session_state:
        st.session_state["upload_state4"] = ""
    if "prompt4" not in st.session_state:
        st.session_state["prompt4"] = ""
    if "pdf_ref4" not in ss:
        ss.pdf_ref4 = None
    if "value4" not in st.session_state:
        st.session_state.value4 = 0
    # buttom send to gemini
    if "vcol1doc4" not in st.session_state:
        st.session_state["vcol1doc4"] = col1
    if "vcol2doc4" not in st.session_state:
        st.session_state["vcol2doc4"] = col2
    if "expander_4" not in st.session_state:
        st.session_state["expander_4"] = True
    st.session_state["init_run_4"] = True
    return


def reset_session_4(st, ss):
    """
    Reset session
    param: st  session
    param: ss  session state
    """

    del st.session_state["chat4"]
    # placeholder for multiple files
    del st.session_state["file_name4"]
    del st.session_state["file_history4"]
    del st.session_state["upload_state4"]
    del st.session_state["prompt4"]
    del ss.pdf_ref4
    del st.session_state.value4
    del st.session_state["vcol1doc4"]
    del st.session_state["vcol2doc4"]
    del st.session_state["expander_4"]
    del st.session_state["init_run_4"]
    # objects
    del st.session_state["image_loader"]
    del st.session_state["image_input4"]
    return


def init_session_2(st, ss, col1, col2):
    """
    initialize session state for multiple files option
    params:
    param: st  session
    param: ss  session state
    param: col1  size col 1
    param: col2  size col 2
    """

    if "chat2" not in st.session_state:
        st.session_state["chat2"] = None

    # placeholder for multiple files
    if "file_name2" not in st.session_state:
        st.session_state["file_name2"] = "no file"
    if "file_history2" not in st.session_state:
        st.session_state["file_history2"] = "no file"

    if "upload_state2" not in st.session_state:
        st.session_state["upload_state2"] = ""

    if "pdf_ref2" not in ss:
        ss.pdf_ref2 = None
    if "value2" not in st.session_state:
        st.session_state.value2 = 0

    if "vcol1doc2" not in st.session_state:
        st.session_state["vcol1doc2"] = col1
    if "vcol2doc2" not in st.session_state:
        st.session_state["vcol2doc2"] = col2
    if "expander_2" not in st.session_state:
        st.session_state["expander_2"] = True
    st.session_state["init_run_2"] = True
    return


def reset_session_2(st, ss):
    """
    Reset session
    param: st  session
    param: ss  session state
    """

    del st.session_state["chat2"]
    # placeholder for multiple files
    del st.session_state["file_name2"]
    del st.session_state["file_history2"]
    del st.session_state["upload_state2"]
    del ss.pdf_ref2
    del st.session_state.value2
    # buttom send to gemini
    del st.session_state["vcol1doc2"]
    del st.session_state["vcol2doc2"]
    del st.session_state["expander_2"]
    del st.session_state["init_run_2"]
    # objects
    del st.session_state["pdf_query_extract2"]
    del st.session_state["pdf_viewer2"]
    del st.session_state["uploader_pdf"]

    return


def init_session_3(st, ss, col1, col2):
    """
    initialize session state for multiple files option
    params:
    param: st  session
    param: ss  session state
    param: col1  size col 1
    param: col2  size col 2
    """

    if "chat3" not in st.session_state:
        st.session_state["chat3"] = None
    # placeholder for multiple files
    if "file_name3" not in st.session_state:
        st.session_state["file_name3"] = "no file"
    if "file_history3" not in st.session_state:
        st.session_state["file_history3"] = "no file"
    if "upload_state3" not in st.session_state:
        st.session_state["upload_state3"] = ""
    if "pdf_ref3" not in ss:
        ss.pdf_ref3 = None
    if "value3" not in st.session_state:
        st.session_state.value3 = 0
    # buttom send to gemini
    if "vcol1doc3" not in st.session_state:
        st.session_state["vcol1doc3"] = col1
    if "vcol2doc3" not in st.session_state:
        st.session_state["vcol2doc3"] = col2
    if "expander_3" not in st.session_state:
        st.session_state["expander_3"] = True
    st.session_state["init_run_3"] = True
    return


def reset_session_3(st, ss):
    """
    Reset session
    param: st  session
    param: ss  session state
    """

    del st.session_state["chat3"]
    # placeholder for multiple files
    del st.session_state["file_name3"]
    del st.session_state["file_history3"]
    del st.session_state["upload_state3"]
    del ss.pdf_ref3
    del st.session_state.value3
    # buttom send to gemini
    del st.session_state["vcol1doc3"]
    del st.session_state["vcol2doc3"]
    del st.session_state["expander_3"]
    del st.session_state["init_run_3"]
    # objects
    del st.session_state["excel_loader"]
    del st.session_state["select_sheet"]
    del st.session_state["dataframe_query_extract"]
    return


def init_session_5(st, ss, col1, col2):
    """
    initialize session Page AUDIO
    params:
    param: st  session
    param: ss  session state
    param: col1  size col 1
    param: col2  size col 2
    """
    if "chat5" not in st.session_state:
        st.session_state["chat5"] = None
    # placeholder for multiple files
    if "file_name5" not in st.session_state:
        st.session_state["file_name5"] = "no file"
    if "file_history5" not in st.session_state:
        st.session_state["file_history5"] = "no file"
    if "upload_state5" not in st.session_state:
        st.session_state["upload_state5"] = ""
    if "pdf_ref5" not in ss:
        ss.pdf_ref5 = None
    if "value5" not in st.session_state:
        st.session_state.value5 = 0
    if "vcol1doc5" not in st.session_state:
        st.session_state["vcol1doc5"] = col1
    if "vcol2doc5" not in st.session_state:
        st.session_state["vcol2doc5"] = col2
    if "expander_5" not in st.session_state:
        st.session_state["expander_5"] = True
    st.session_state["init_run_5"] = True
    return


def reset_session_5(st, ss):
    """
    Reset session Page AUDIO
    param: st  session
    param: ss  session state
    """

    del st.session_state["chat5"]
    # placeholder for multiple files
    del st.session_state["file_name5"]
    del st.session_state["file_history5"]
    del st.session_state["upload_state5"]
    del ss.pdf_ref5
    del st.session_state.value5
    del st.session_state["vcol1doc5"]
    del st.session_state["vcol2doc5"]
    del st.session_state["expander_5"]
    del st.session_state["init_run_5"]
    # objects
    del st.session_state["audio_loader"]
    del st.session_state["input_audio"]
    del st.session_state["salir_5"]

    return


def init_session_6(st, ss, col1, col2):
    """
    initialize session Page Video
    params:
    param: st  session
    param: ss  session state
    param: col1  size col 1
    param: col2  size col 2
    """

    # placeholder for multiple files
    if "file_name6" not in st.session_state:
        st.session_state["file_name6"] = "no file"
    if "file_history6" not in st.session_state:
        st.session_state["file_history6"] = "no file"
    if "upload_state6" not in st.session_state:
        st.session_state["upload_state6"] = ""
    if "pdf_ref6" not in ss:
        ss.pdf_ref6 = None
    if "value6" not in st.session_state:
        st.session_state.value6 = 0
    # buttom send to gemini
    if "buttom_send_not_clicked6" not in st.session_state:
        st.session_state["buttom_send_not_clicked6"] = False
    if "vcol1doc6" not in st.session_state:
        st.session_state["vcol1doc6"] = col1
    if "vcol2doc6" not in st.session_state:
        st.session_state["vcol2doc6"] = col2
    if "expander_6" not in st.session_state:
        st.session_state["expander_6"] = True
    st.session_state["init_run_6"] = True
    return


def reset_session_6(st, ss):
    """
    Reset session Page Video
    param: st  session
    param: ss  session state
    """
    del st.session_state["chat6"]
    del st.session_state["file_name6"]
    del st.session_state["file_history6"]
    del st.session_state["upload_state6"]
    del ss.pdf_ref6
    del st.session_state.value6
    # buttom send to gemini
    del st.session_state["buttom_send_not_clicked6"]
    del st.session_state["vcol1doc6"]
    del st.session_state["vcol2doc6"]
    del st.session_state["expander_6"]
    del st.session_state["init_run_6"]
    # objects
    del st.session_state["video_loader"]
    del st.session_state["input_video"]
    del st.session_state["salir_6"]
    return


def init_session_7(st, ss, col1, col2):
    """
    initialize session Page HTML
    params:
    param: st  session
    param: ss  session state
    param: col1  size col 1
    param: col2  size col 2
    """

    if "chat_history7" not in st.session_state:
        st.session_state["chat_history7"] = []
    if "vector_store7" not in st.session_state:
        st.session_state["vector_store7"] = None
    if "prompt_introduced7" not in st.session_state:
        st.session_state["prompt_introduced7"] = ""
    if "upload_state7" not in st.session_state:
        st.session_state["upload_state7"] = ""
    if "chat_true7" not in st.session_state:
        st.session_state["chat_true7"] = "no_chat"
    if "value7" not in st.session_state:
        st.session_state.value7 = 0
    if "vcol1doc7" not in st.session_state:
        st.session_state["vcol1doc7"] = col1
    if "vcol2doc7" not in st.session_state:
        st.session_state["vcol2doc7"] = col2
    if "expander_7" not in st.session_state:
        st.session_state["expander_7"] = True
    if "parsed_htmls" not in st.session_state:
        st.session_state["parsed_htmls"] = []
    if "documents" not in st.session_state:
        st.session_state["documents"] = []
    st.session_state["init_run_7"] = True
    if "salir_7" not in st.session_state:
        st.session_state["salir_7"] = False
    return


def reset_session_7(st, ss):
    """
    Reset session Page HTML
    param: st  session
    param: ss  session state
    """

    del st.session_state["chat_history7"]
    del st.session_state["chat7"]
    del st.session_state["vector_store7"]
    del st.session_state["embeddings7"]
    del st.session_state["db_local_folder"]
    # placeholder for multiple files
    del st.session_state["db_local_file"]

    del st.session_state["prompt_introduced7"]
    del st.session_state["upload_state7"]
    del st.session_state["chat_true7"]
    del st.session_state.value7
    del st.session_state["vcol1doc7"]
    del st.session_state["vcol2doc7"]
    del st.session_state["expander_7"]
    del st.session_state["init_run_7"]
    del st.session_state["parsed_htmls"]
    del st.session_state["documents"]
    del st.session_state["index_rebuilt"]
    del st.session_state["parse_html"]
    del st.session_state["text_splitter"]
    # objects
    del st.session_state["html_query"]
    del st.session_state["salir_7"]

    return


def init_session_8(st, ss, col8, col2):
    """
    initialize session state for multiple files option
    param: st  session
    param: ss  session state
    param: model  chat (gemini model)
    """

    if "chat_history8" not in st.session_state:
        st.session_state["chat_history8"] = []
    if "vector_store8" not in st.session_state:
        st.session_state["vector_store8"] = None
    if "retriever8" not in st.session_state:
        st.session_state["retriever8"] = None
    # placeholder for multiple files
    if "file_name8" not in st.session_state:
        st.session_state["file_name8"] = "no file"
    if "upload_state8" not in st.session_state:
        st.session_state["upload_state8"] = ""
    if "file_history8" not in st.session_state:
        st.session_state["file_history8"] = "no file"
    if "prompt_introduced8" not in st.session_state:
        st.session_state["prompt_introduced8"] = ""
    if "chat_true8" not in st.session_state:
        st.session_state["chat_true8"] = "no_chat"
    if "pymupdfllm_md" not in st.session_state:
        st.session_state["pymupdfllm_md"] = ""
    if "pymupdfllm_tables" not in st.session_state:
        st.session_state["pymupdfllm_tables"] = []
    if "pymupdfllm_text" not in st.session_state:
        st.session_state["pymupdfllm_text"] = []

    if "text_summaries" not in st.session_state:
        st.session_state["text_summaries"] = []
    if "table_summaries" not in st.session_state:
        st.session_state["table_summaries"] = []
    if "img_base64_list" not in st.session_state:
        st.session_state["img_base64_list"] = []
    if "image_summaries" not in st.session_state:
        st.session_state["image_summaries"] = []
    if "pdf_ref8" not in ss:
        ss.pdf_ref8 = None
    if "value8" not in st.session_state:
        st.session_state.value8 = 0
    # buttom send to gemini
    if "vcol1doc" not in st.session_state:
        st.session_state["vcol1doc"] = col8
    if "vcol2doc" not in st.session_state:
        st.session_state["vcol2doc"] = col2
    if "expander_8" not in st.session_state:
        st.session_state["expander_8"] = True
    if "click_button_parse8" not in st.session_state:
        st.session_state["click_button_parse8"] = False
    if "fill_retriever8" not in st.session_state:
        st.session_state["fill_retriever8"] = False
    st.session_state["init_run_8"] = True
    return


def reset_session_8(st, ss):
    """
    Delete session state for multiple files option
    param: st  session
    param: ss  session state
    param: model  chat (gemini model)
    """

    del st.session_state["chat_history8"]

    del st.session_state["chat8"]
    del st.session_state["vector_store8"]
    del st.session_state["embeddings8"]
    del st.session_state["retriever8"]
    # placeholder for multiple files
    del st.session_state["file_name8"]
    del st.session_state["file_history8"]
    del st.session_state["prompt_introduced8"]
    del st.session_state["chat_true8"]
    del st.session_state["pymupdfllm_md"]
    del st.session_state["pymupdfllm_tables"]
    del st.session_state["pymupdfllm_text"]
    del st.session_state["img_base64_list"]
    del st.session_state["image_summaries"]

    del st.session_state["text_summaries"]
    del st.session_state["table_summaries"]

    del ss.pdf_ref8
    del st.session_state.value8
    # buttom send to gemini
    del st.session_state["vcol1doc"]
    del st.session_state["vcol2doc"]
    del st.session_state["expander_8"]
    del st.session_state["init_run_8"]
    # delete objects
    del st.session_state["pdf"]
    del st.session_state["pdf_viewer"]
    del st.session_state["pdf_query"]
    del st.session_state["upload_state8"]
    del st.session_state["click_button_parse8"]
    del st.session_state["salir_8"]

    return


def save_df_many(list2: List, df: pd.DataFrame, fname: str, prompt: str, filename: str):
    """
    Save prompt to a json file
    :param name_prompt: name of the prompt
    :param prompt: prompt
    :param keywords: keywords
    :param df: dataframe with all prompts
    """
    if len(list2) > 1:
        list2.reverse()
    p_dict = {}
    p_dict["id"] = str(uuid.uuid4())
    p_dict["filename"] = filename
    p_dict["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    p_dict["prompt"] = prompt.replace(",", "")
    p_dict["respuesta_chat"] = list2[0].replace(",", "")
    row = pd.DataFrame(p_dict, index=[0])
    df = pd.concat([df, row], ignore_index=True)
    df.to_csv(fname, index=False)

    return


def save_df_pdf(df: pd.DataFrame, fname: str, filename: str):
    """
    Save prompt to a json file
    :param name_prompt: name of the prompt
    :param prompt: prompt
    :param keywords: keywords
    :param df: dataframe with all prompts
    """

    p_dict = {}
    p_dict["id"] = str(uuid.uuid4())
    p_dict["filename"] = filename
    p_dict["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = pd.DataFrame(p_dict, index=[0])
    df = pd.concat([df, row], ignore_index=True)
    df.to_csv(fname, index=False)

    return


def get_filename_multi(st):
    """
    extract filename from multi file name
    """

    text0 = ""
    for file in st.session_state["multi_file_name"]:
        text0 = text0 + file.replace(".pdf", "") + "_"
    filename = text0[:-1]
    return filename
