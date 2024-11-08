# To help construct our Chat Messages
from langchain.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.output_parsers import PydanticOutputParser
from langchain_core.messages import AIMessage

# To parse outputs and get structured data back
from langchain_core.runnables import RunnableLambda
from .data_models import EntityDataExtraction


# Instantiate the parser with the new model.
parser = PydanticOutputParser(pydantic_object=EntityDataExtraction)

# Update the prompt to match the new query and desired format.
prompt_epd = ChatPromptTemplate(
    messages=[
        HumanMessagePromptTemplate.from_template(
            "Answer the users question as best as possible about the name of the company Requested.\n{format_instructions}\n{question}"
        )
    ],
    input_variables=["question"],
    partial_variables={
        "format_instructions": parser.get_format_instructions(),
    },
)


PROMPT_TEMPLATE = """[INST]You are a friendly virtual assistant and maintain a conversational, polite, patient, friendly and gender neutral tone throughout the conversation.

Your task is to understand the QUESTION, read the Content list from the DOCUMENT delimited by ```, generate an answer based on the Content, and provide references used in answering the question in the format "[Title](URL)".
Do not depend on outside knowledge or fabricate responses.
DOCUMENT: ```{context}```

Your response should follow these steps:

1. The answer should be short and concise, clear.
    * If detailed instructions are required, present them in an ordered list or bullet points.
2. If the answer to the question is not available in the provided DOCUMENT, ONLY respond that you couldn't find any information related to the QUESTION, and do not show references and citations.
3. Citation
    * ALWAYS start the citation section with "Here are the sources to generate response." and follow with references in markdown link format [Title](URL) to support the answer.
    * Use Bullets to display the reference [Title](URL).
    * You MUST ONLY use the URL extracted from the DOCUMENT as the reference link. DO NOT fabricate or use any link outside the DOCUMENT as reference.
    * Avoid over-citation. Only include references that were directly used in generating the response.
    * If no reference URL can be provided, remove the entire citation section.
    * The Citation section can include one or more references. DO NOT include same URL as multiple references. ALWAYS append the citation section at the end of your response.
    * You MUST follow the below format as an example for this citation section:
      Here are the sources used to generate this response:
      * [Title](URL)
[/INST]
[INST]
QUESTION: {question}
FINAL ANSWER:[/INST]"""


prompt_template_html = PromptTemplate(
    template=PROMPT_TEMPLATE, input_variables=["context", "question"]
)


# Prompt
text_pdf_multi_text = """You are an assistant tasked with summarizing tables and text for retrieval. \
These summaries will be embedded and used to retrieve the raw text or table elements. \
Give a concise summary of the table or text that is well optimized for retrieval. Table or text: {element} """
prompt_text_pdf_multi_text = PromptTemplate.from_template(text_pdf_multi_text)
empty_response_pdf_multi_text = RunnableLambda(
    lambda x: AIMessage(content="Error processing document")
)


prompt_image_pdf_multi_text = """You are an assistant tasked with summarizing images for retrieval. \
    These summaries will be embedded and used to retrieve the raw image. \
    Give a concise summary of the image that is well optimized for retrieval."""


pront_multi_system = """You are financial analyst tasking with providing investment advice.\n
            You will be given a mixed of text, tables, and image(s) usually of charts or graphs.\n
            Use this information to provide investment advice related to the user question. \n"""
