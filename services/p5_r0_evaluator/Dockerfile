FROM python:3.12.8-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=0 \
    PORT=8080
WORKDIR /app
COPY services /app/services
COPY evaluation /app/evaluation
COPY schemas /app/schemas
RUN pip install --no-cache-dir -r /app/services/p5_r0_evaluator/requirements.txt
USER 65532:65532
EXPOSE 8080
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "4", "--timeout", "30", "services.p5_r0_evaluator.app:application"]
