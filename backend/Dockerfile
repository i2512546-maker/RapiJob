# Build the React + TypeScript client
FROM node:22-alpine AS web-build
WORKDIR /web
COPY web/package.json ./
RUN npm install
COPY web/ ./
RUN npm run build

# Serve the compiled web app with FastAPI
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r /app/requirements.txt
COPY backend/ /app/backend/
COPY --from=web-build /web/dist /app/web/dist
WORKDIR /app/backend
ENV PYTHONUNBUFFERED=1 PORT=10000
EXPOSE 10000
CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:${PORT:-10000} --workers 1"]
