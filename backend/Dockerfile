FROM public.ecr.aws/lambda/python:3.14

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files and install dependencies with uv
COPY pyproject.toml ${LAMBDA_TASK_ROOT}/
RUN uv pip install --system --no-cache -r ${LAMBDA_TASK_ROOT}/pyproject.toml

# Copy all root Python modules used by the Lambda runtime.
COPY *.py ${LAMBDA_TASK_ROOT}/
COPY cameras.json ${LAMBDA_TASK_ROOT}/
COPY templates/ ${LAMBDA_TASK_ROOT}/templates/

CMD ["lambda_handler.handler"]
