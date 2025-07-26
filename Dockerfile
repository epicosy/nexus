FROM docker:dind
MAINTAINER Eduard Pinconschi <eduard.pinconschi@tecnico.ulisboa.pt>
ENV PS1="\[\e[0;33m\]|> nexus <| \[\e[1;35m\]\W\[\e[0m\] \[\e[0m\]# "

RUN apk update && apk add git python3 python3-dev py3-pip py3-psutil nano libpq-dev build-base git

WORKDIR /src
COPY . /src
RUN pip3 install --no-cache-dir -r requirements.txt \
    && python3 setup.py install
WORKDIR /

#ENTRYPOINT ["nexus"]
