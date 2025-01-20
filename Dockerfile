FROM python:3.9-slim

WORKDIR /app

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONIOENCODING=utf8

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]