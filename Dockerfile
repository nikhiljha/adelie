FROM python:3.9.5-buster

RUN pip install --no-cache-dir poetry
COPY . /src
RUN cd /src && poetry config virtualenvs.create false
RUN cd /src && poetry install --no-dev

CMD python -m adelie
