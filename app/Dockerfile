# For a Hugging Face Docker Space. Render does not need this file.
FROM python:3.11-slim
WORKDIR /code
COPY app/requirements-api.txt app/requirements-api.txt
RUN pip install --no-cache-dir -r app/requirements-api.txt
COPY . .
EXPOSE 7860
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "7860"]
