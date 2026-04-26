FROM python:3.11-slim

# Install system dependencies required by OpenCV (used in controlnet_aux)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (HuggingFace security requirement)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /home/user/app

# Install Python dependencies FIRST (cached layer)
COPY --chown=user requirements.txt .

# Install CPU-only torch (smaller than CUDA version, saves huge amount of RAM and space)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY --chown=user . .

# Create the static models directory so it's ready and writable
RUN mkdir -p /home/user/app/static/models

# HuggingFace Spaces MUST listen on port 7860
EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
