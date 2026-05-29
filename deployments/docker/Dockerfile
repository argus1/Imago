FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md license.txt /app/
COPY src /app/src
RUN pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["imago-api"]
