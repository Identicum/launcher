FROM ghcr.io/identicum/alpine-python:latest

WORKDIR /app
COPY pyproject.toml README.md ./
COPY launcher ./launcher
RUN pip install --no-cache-dir . && \
    rm -rf /app/* && \
    adduser -D -H -u 1000 launcher && \
    mkdir -p /data && chown launcher /data

USER launcher
ENV DATA_DIR=/data \
    PORT=8080
EXPOSE 8080

HEALTHCHECK --timeout=5s CMD curl --fail --silent http://localhost:8080/health || exit 1

ENTRYPOINT ["launcher"]
CMD ["serve"]
