FROM ghcr.io/astral-sh/uv:0.7.12-python3.13-alpine

WORKDIR /app/
COPY ./ ./

RUN uv sync --frozen

CMD ["uv", "run", "--module", "src"]
