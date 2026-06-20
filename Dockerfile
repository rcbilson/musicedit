FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --system --no-create-home appuser
USER appuser

ENV PORT=5000
ENV CHOIR_ROOT=/choir

VOLUME ["/choir"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/')"

EXPOSE ${PORT}

CMD gunicorn --bind "0.0.0.0:${PORT}" app:app
