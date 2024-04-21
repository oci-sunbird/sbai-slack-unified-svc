FROM python:3.8.10
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip
RUN pip3 install --no-cache-dir --upgrade -r /app/requirements.txt
COPY . /app

CMD ["uvicorn", "main:api", "--host", "0.0.0.0", "--port", "8080"]

