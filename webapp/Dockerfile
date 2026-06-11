FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install flask gunicorn google-cloud-bigquery google-cloud-aiplatform
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "120", "main:app"]