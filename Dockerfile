FROM python:3.13-bookworm                               # base Debian 12
WORKDIR /biblioteka
COPY requirements.txt .                                 # biblioteka/requirements.txt
RUN pip install -r requirements.txt
COPY . .                                                # требования остаются в кэше
CMD ["gunicorn", "--bind", "0.0.0.0:12345", "app:app"]  # app.py:app
