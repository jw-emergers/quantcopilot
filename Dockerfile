# Use official Python image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy files
COPY . /app

# Create a virtual environment and activate it
RUN python -m venv /env
ENV PATH="/env/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Run FastAPI with Uvicorn
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
