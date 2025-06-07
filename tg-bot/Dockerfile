FROM ghcr.io/astral-sh/uv:0.7.12-alpine3.21

WORKDIR /app/
COPY ./ ./

RUN uv sync --frozen

CMD ["uv", "run", "src/main.py"]
