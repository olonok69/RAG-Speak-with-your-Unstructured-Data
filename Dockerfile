FROM python:3.11-slim

# USER to Run this docker
ARG user_app

ENV USER_APP=$user_app
ENV FAISS_ENABLE_GPU=ON
# Install necessary packages
RUN apt-get update && apt-get -y upgrade \
    && apt-get install -y libsm6 libxext6 git net-tools  python3-magic nano iputils-ping procps \
    && pip install --upgrade pip 


# Ref:
# * https://github.com/GoogleCloudPlatform/python-runtime/blob/8cdc91a88cd67501ee5190c934c786a7e91e13f1/README.md#kubernetes-engine--other-docker-hosts
# * https://github.com/GoogleCloudPlatform/python-runtime/blob/8cdc91a88cd67501ee5190c934c786a7e91e13f1/scripts/testdata/hello_world_golden/Dockerfile

RUN groupadd ${USER_APP} && useradd --create-home -g ${USER_APP} ${USER_APP}
ENV PATH=/home/${USER_APP}/.local/bin:${PATH}

WORKDIR /home/${USER_APP}/gemini

COPY ./requirements.txt /home/${USER_APP}/gemini/requirements.txt


RUN pip install -r /home/${USER_APP}/gemini/requirements.txt

COPY . .

RUN chown -R ${USER_APP}:${USER_APP} /home/${USER_APP}/gemini 
RUN chmod -R 776 /home/${USER_APP}

EXPOSE 8501
USER ${USER_APP}

ENTRYPOINT [ "streamlit", "run", "pages.py", "--server.port", "8501" ]
