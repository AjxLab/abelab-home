FROM python:3.7
USER root

COPY ./requirements.txt /requirements.txt

RUN apt-get update
RUN apt-get install -y libasound-dev portaudio19-dev libportaudio2

RUN pip install --upgrade pip
RUN pip install -r /requirements.txt