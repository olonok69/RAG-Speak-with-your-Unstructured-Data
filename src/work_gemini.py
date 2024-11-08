from vertexai.generative_models import GenerativeModel, Part, ChatSession
import vertexai.generative_models as generative_models
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
import base64
import logging
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
import os
from langchain_google_vertexai import VertexAI, ChatVertexAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.messages import HumanMessage
from src.prompts import (
    prompt_text_pdf_multi_text,
    empty_response_pdf_multi_text,
    prompt_image_pdf_multi_text,
)
from src.files import img_prompt_func, split_image_text_types


def create_pandas_agent(llm, df):
    """
    open LLM and  create_pandas_dataframe_agent
    Args:
        llm : Model
        df : Dataframe
    return

    """
    return create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        verbose=True,
        agent_type="zero-shot-react-description",
        return_intermediate_steps=True,
        handle_parsing_errors=True,
        allow_dangerous_code=True,
    )


def get_chat_response(chat: ChatSession, prompt: str) -> str:
    text_response = []
    responses = chat.send_message(prompt, stream=True)

    try:
        for chunk in responses:

            if chunk.text:
                text_response.append(chunk.text)
        return "".join(text_response)
    except:

        return "error"


def start_chat(model):
    chat = model.start_chat(response_validation=False)
    return chat


def prepare_prompt(list_images, question, page_select, st):
    """
    Prepare the prompt for the chat session
    :param list_images: list of images
    :param question: question
    :param page_select: page selected
    :param st: st state
    :return: prompt
    """
    content = []
    if page_select == "all":
        mime_type = "application/pdf"
    else:
        mime_type = "image/jpeg"
    content = []
    for image in list_images:
        im_b64 = base64.b64encode(image).decode("utf8")
        image = Part.from_data(data=im_b64, mime_type=mime_type)
        content.append(image)
    prompt = [f"""{question} """] + content
    if len(content) > 0 and len(question) > 0:
        logging.info("Gemini app: prompt ready")
        st.session_state["prompt"] = prompt
        st.session_state.value = 5
        st.session_state["chat_true"] = "chat activo"
        st.session_state["buttom_send_not_clicked"] = True

    return


def init_model(config):
    return GenerativeModel(
        config["MODEL"],
        system_instruction=[
            """You a helpful agent who helps to extract relevant information from documents"""
        ],
        safety_settings={
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        },
        generation_config={
            "max_output_tokens": 8192,
            "temperature": 1,
            "top_p": 0.95,
        },
    )


def init_llm(model, credentials):
    """Create ChatGoogleGenerativeAI Instance

    Args:
        model (string): Model
        credentials (vertex credential service account ): Google credentials

    Returns:
        _type_: _description_
    """
    return ChatGoogleGenerativeAI(model=model, credentials=credentials)


def init_embeddings(credentials, google_api_key, model: str = "models/embedding-001"):
    """
    Init EMbeddings Generative Model
    """
    return GoogleGenerativeAIEmbeddings(
        model=model,
        credentials=credentials,
        google_api_key=google_api_key,
    )


def generate_text_summaries(
    model: str, credentials, texts, tables, summarize_texts=False
):
    """
    Summarize text elements
    texts: List of str
    tables: List of str
    summarize_texts: Bool to summarize texts
    """

    model = VertexAI(
        temperature=0,
        model_name=model,
        max_tokens=1024,
        credentials=credentials,
    ).with_fallbacks([empty_response_pdf_multi_text])

    summarize_chain = (
        {"element": lambda x: x}
        | prompt_text_pdf_multi_text
        | model
        | StrOutputParser()
    )

    # Initialize empty summaries
    text_summaries = []
    table_summaries = []

    # Apply to text if texts are provided and summarization is requested
    if texts and summarize_texts:
        text_summaries = summarize_chain.batch(texts, {"max_concurrency": 1})
    elif texts:
        text_summaries = texts

    # Apply to tables if tables are provided
    if tables:
        table_summaries = summarize_chain.batch(tables, {"max_concurrency": 1})

    return text_summaries, table_summaries


def encode_image(image_path):
    """
    Getting the base64 string
    Args:
        image_path: path to image
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def image_summarize(img_base64, model: str, credentials, prompt, type_image="jpeg"):
    """
    Make image summary
    Args:
        img_base64: base64 image
        model: model name
        credentials: credentials
        prompt: prompt
        type_image: type of image
    """
    model = ChatVertexAI(model=model, max_tokens=1024, credentials=credentials)

    msg = model.invoke(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{type_image};base64,{img_base64}"
                        },
                    },
                ]
            )
        ]
    )
    return msg.content


def generate_img_summaries(model: str, credentials, path, type_image="jpeg"):
    """
    Generate summaries and base64 encoded strings for images
    path: Path to list of .jpg files extracted by Unstructured
    Args:
        model: model name
        credentials: credentials
        path: path to images
        type_image: type of image
    """

    # Store base64 encoded images
    img_base64_list = []

    # Store image summaries
    image_summaries = []

    # Apply to images
    for img_file in sorted(os.listdir(path)):
        if img_file.endswith(f".{type_image}"):
            img_path = os.path.join(path, img_file)
            base64_image = encode_image(img_path)
            img_base64_list.append(base64_image)
            image_summaries.append(
                image_summarize(
                    base64_image,
                    model,
                    credentials,
                    prompt_image_pdf_multi_text,
                    type_image,
                )
            )

    return img_base64_list, image_summaries


def multi_modal_rag_chain(retriever, model_name, credentials):
    """
    Multi-modal RAG chain
    """

    # Multi-modal LLM
    model = ChatVertexAI(
        temperature=0, model_name=model_name, max_tokens=1024, credentials=credentials
    )

    # RAG pipeline
    chain = (
        {
            "context": retriever | RunnableLambda(split_image_text_types),
            "question": RunnablePassthrough(),
        }
        | RunnableLambda(img_prompt_func)
        | model
        | StrOutputParser()
    )

    return chain
