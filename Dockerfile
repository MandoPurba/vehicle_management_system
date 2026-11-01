# Butuh Python 3.12: struktur data di core/ memakai sintaks generic PEP 695.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PARKIR_STATE_PATH=/app/state/state.json

WORKDIR /app

# Dependensi disalin lebih dulu supaya layer-nya tidak dibangun ulang
# setiap kali kode berubah.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./
COPY core/ ./core/
COPY views/ ./views/
COPY .streamlit/ ./.streamlit/
COPY data/sample_data.json data/README.md ./data/

# State yang berubah tinggal di /app/state, bukan di /app/data, supaya
# volume tidak menutupi sample_data.json yang ikut di dalam image.
RUN mkdir -p /app/state \
 && adduser --disabled-password --gecos "" --uid 10001 parkir \
 && chown -R parkir:parkir /app/state
USER parkir

EXPOSE 8501

# Endpoint kesehatan bawaan Streamlit. Dicek dengan urllib supaya image
# tidak perlu tambahan curl.
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3).status == 200 else 1)"

CMD ["streamlit", "run", "app.py"]
