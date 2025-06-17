FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    elasticsearch \
    requests \
    pyyaml

# Add the parent directory to Python path so imports work correctly
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose the port
EXPOSE 5001

# Command to run the application
CMD ["python", "app.py"] 