# Use the stable Python 3.13 image (avoids the 3.14 Pydantic/ChromaDB bug)
FROM python:3.13-slim

# Install system dependencies for PyMuPDF and SQLite
RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create the refinery directory for persistence
RUN mkdir -p .refinery/profiles .refinery/extractions .refinery/pageindex .refinery/vector_db

# Expose the Gradio port
EXPOSE 7860

# Command to run the demo app
CMD ["python", "app.py"]