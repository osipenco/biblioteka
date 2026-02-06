FROM python:3.13-bookworm
WORKDIR /biblioteka
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:12345", "app:app"]
