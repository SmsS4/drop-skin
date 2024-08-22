FROM python:3.11.7 as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=360 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.6.1

WORKDIR /app

RUN apt-get update -o Acquire::Check-Valid-Until=false -y --fix-missing && apt-get install -y cron
RUN pip install "poetry==$POETRY_VERSION"
RUN python -m venv /venv
COPY pyproject.toml poetry.lock ./
RUN . /venv/bin/activate && poetry install --only main --no-root

COPY . .

FROM base as final

COPY --from=base /venv /venv
COPY --from=base /app .

EXPOSE 5000

ENTRYPOINT /app/entrypoint.sh
