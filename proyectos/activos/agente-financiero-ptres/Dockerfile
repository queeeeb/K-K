FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY core/ core/
COPY pipelines/ pipelines/
COPY main.py ./
COPY scripts/ scripts/

RUN uv sync --no-dev --frozen

CMD ["uv", "run", "python", "main.py"]
