FROM python:3.10

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install tokenizers==0.12.1 transformers==4.18.0

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
