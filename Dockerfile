FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY nutriken_engine.py plan_template.py drugbank_client.py ./
COPY index.html script.js style.css i18n.js ./
RUN mkdir -p local_db && chmod 777 local_db
COPY local_db/ ./local_db/
EXPOSE 7860
CMD ["uvicorn", "nutriken_engine:app", "--host", "0.0.0.0", "--port", "7860"]

