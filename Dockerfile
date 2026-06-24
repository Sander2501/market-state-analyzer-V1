FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

RUN useradd -U -u 1000 appuser && chown -R 1000:1000 /app
USER 1000

CMD ["python", "-m", "streamlit", "run", "ui/streamlit_app.py", "--server.address=0.0.0.0"]
