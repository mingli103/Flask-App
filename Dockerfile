FROM python:3.12.8-alpine3.20 as builder


ARG BUILD_DATE
ARG VCS_REF
ARG VERSION


LABEL maintainer="your-email@example.com" \
    org.label-schema.build-date=$BUILD_DATE \
    org.label-schema.name="flask-app" \
    org.label-schema.description="Flask simple app" \
    org.label-schema.url="https://github.com/mingli103/flask-app" \
    org.label-schema.vcs-ref=$VCS_REF \
    org.label-schema.vcs-url="https://github.com/mingli103/flask-app" \
    org.label-schema.version=$VERSION \
    org.label-schema.schema-version="1.0"

RUN addgroup -S flask && adduser -S flask -G flask --disabled-password

RUN apk update && apk upgrade && apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

FROM python:3.12.8-alpine3.20 as production

RUN apk update && apk upgrade && apk add --no-cache curl redis

RUN addgroup -S flask && adduser -S flask -G flask --disabled-password

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

COPY --chown=flask:flask . .

RUN mkdir -p /app/logs && chown -R flask:flask /app

USER flask

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

CMD ["sh", "/app/start.sh"] 
