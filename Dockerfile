FROM python:3.8

WORKDIR /usr/src/heximages

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install "poetry==1.1"

COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

COPY ./heximages .

RUN chmod +x /usr/src/heximages/entrypoint.sh

ENTRYPOINT ["/usr/src/heximages/entrypoint.sh"]