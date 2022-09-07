FROM python:3.7-slim

WORKDIR /app

COPY ./concordance/ .
COPY ./.env .
COPY ./requirements.txt .

RUN pip3 install -r requirements.txt --no-cache-dir
RUN pip3 install gunicorn

CMD ["gunicorn", "concordance.wsgi:application", "--bind", "0:8000"]