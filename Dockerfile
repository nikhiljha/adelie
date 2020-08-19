FROM python:3.8.5-alpine3.12

COPY . /adelie
RUN cd /adelie && pip install -r requirements.txt

CMD python3 /adelie/src/main.py
