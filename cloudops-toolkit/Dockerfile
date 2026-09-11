FROM python:3.12-slim

RUN useradd --create-home --uid 10001 cloudops
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
USER cloudops
ENTRYPOINT ["cloudops"]
CMD ["health"]
