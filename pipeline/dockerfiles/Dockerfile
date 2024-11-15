FROM ubuntu:jammy

WORKDIR /rtci

COPY pipeline/requirements.txt pipeline/requirements.txt

# install python, git, etc., all requirements.txt and selenium
RUN : \
    && apt update \
    && DEBIAN_FRONTEND=noninteractive apt install \
        -y \
        --no-install-recommends \
        python3-pip \
	    git \
        ssh \
        wget \
        gnupg \
        curl \
    && pip install -r pipeline/requirements.txt \
    && pip install selenium \
    && :

# install google chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb
RUN apt -y update
RUN apt-get install -y google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

COPY . /rtci

ENV PYTHONPATH "${PYTHONPATH}:/rtci"

CMD tail -F anything
