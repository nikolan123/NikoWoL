# build tailwind
FROM node:lts-alpine AS node_builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
RUN npm run build:tailwind
# build python stuff
FROM python:3.10-slim-buster AS python_builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# final
FROM python:3.10-slim-buster
WORKDIR /app
COPY --from=python_builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=python_builder /usr/local/bin /usr/local/bin
COPY --from=node_builder /app/static/css/output.css ./static/css/output.css
COPY . .
COPY config/config.example.json config/config.json
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["sh", "-c", "echo \"{\\\"host\\\": \\\"$APP_HOST\\\", \\\"port\\\": $APP_PORT}\" > /app/config/config.json && exec \"$@\"", "--"]
CMD ["python", "src/app.py"]
