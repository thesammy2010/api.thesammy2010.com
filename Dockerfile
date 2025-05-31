# Stage 1: Build Stage - Install dependencies and build the wheel
FROM python:3.13-slim AS build-stage

# Set environment variables for Poetry
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install Poetry
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get remove --purge -y build-essential curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy pyproject.toml and poetry.lock to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry
# We use --no-root to install only the dependencies, not the current project itself yet
RUN poetry install --no-root --only main

# Stage 2: Production Stage - Create a minimal runtime image
FROM python:3.13-slim AS production-stage

# Set environment variables for Poetry (needed for virtualenv activation if using it later)
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PATH="$POETRY_HOME/bin:$PATH"

# Set the working directory
WORKDIR /app

# Copy only the necessary files from the build stage and your application code
COPY --from=build-stage /app/.venv /app/.venv
COPY . /app

# Expose the port your FastAPI app will run on (default for Uvicorn)
EXPOSE 8000

# Command to run the application
# We activate the virtual environment and then run uvicorn
# Replace `main:app` with the actual path to your FastAPI app instance
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
