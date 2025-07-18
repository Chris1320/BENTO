FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv@sha256:6c1e19020ec221986a210027040044a5df8de762eb36d5240e382bc41d7a9043 /uv /uvx /bin/

WORKDIR /app

COPY ./centralserver ./centralserver
COPY ./templates ./templates
COPY ./pyproject.toml ./pyproject.toml
COPY ./uv.lock ./uv.lock

RUN mkdir -p ./db ./logs
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

EXPOSE 8081

# Start the server
CMD ["uv", "run", "uvicorn", "centralserver:app", "--host", "0.0.0.0", "--port", "8081"]
