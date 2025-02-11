FROM ubuntu:jammy
WORKDIR /rtci
COPY pipeline/requirements.txt pipeline/requirements.txt

RUN : \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install  \
       -y --no-install-recommends \
       git \
       python3-pip \
    && pip3 install -r pipeline/requirements.txt \
    && :

## install google chrome
#RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
#RUN apt-get install -y ./google-chrome-stable_current_amd64.deb
#RUN apt-get install -y google-chrome-stable
#
## install chromedriver
#RUN apt-get install -yqq unzip
#RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
#RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

COPY . /rtci
CMD tail -F anything


## install python, git, etc., all requirements.txt and selenium
#RUN : \
#    && apt update \
#    && DEBIAN_FRONTEND=noninteractive apt install \
#        -y \
#        --no-install-recommends \
#        python3-pip \
#	    git \
#        ssh \
#        wget \
#        gnupg \
#        curl \
#        firefox \
#    && pip3 install -r pipeline/requirements.txt \
#    && pip3 install selenium \
#    && :
#
### install google chrome
##RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
##RUN apt-get install -y ./google-chrome-stable_current_amd64.deb
##RUN apt -y update
##RUN apt-get install -y google-chrome-stable
##
### install chromedriver
##RUN apt-get install -yqq unzip
##RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
##RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
#
## install geckodriver and firefox
#
##RUN : \
##    && GECKODRIVER_VERSION=`curl -sL -I "https://github.com/mozilla/geckodriver/releases/latest" | grep -i "location:" | awk '{print $2}' | grep -o "v[0-9]\+.[0-9]\+.[0-9]\+"` \
##    && wget https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz \
##    && tar -zxf geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz -C /usr/local/bin \
##    && chmod +x /usr/local/bin/geckodriver \
##    && rm geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz \
###    && :
##
###RUN : \
###    && FIREFOX_DOWNLOAD_URL="https://download.mozilla.org/?product=firefox-latest&os=linux64" \
###    && wget --no-verbose -O /tmp/firefox.tar.bz2 $FIREFOX_DOWNLOAD_URL \
###    && apt-get -qqy --no-install-recommends install firefox \
###    && apt-get -y purge firefox \
##
##    && FIREFOX_SETUP=firefox-setup.tar.bz2 \
##    && apt-get purge firefox \
##    && wget -O $FIREFOX_SETUP "https://download.mozilla.org/?product=firefox-latest&os=linux64" \
##    && tar xjf $FIREFOX_SETUP -C /opt/ \
##    && ln -s /opt/firefox/firefox /usr/bin/firefox \
##    && rm $FIREFOX_SETUP \
##    && :
#
## install chromedriver and google-chrome
#
##RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
##    wget https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
##    unzip chromedriver_linux64.zip -d /usr/bin && \
##    chmod +x /usr/bin/chromedriver && \
##    rm chromedriver_linux64.zip
##
##RUN CHROME_SETUP=google-chrome.deb && \
##    wget -O $CHROME_SETUP "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" && \
##    dpkg -i $CHROME_SETUP && \
##    apt-get install -y -f && \
##    rm $CHROME_SETUP
#
#ENV PYTHONPATH "${PYTHONPATH}:/rtci"
