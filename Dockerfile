# Use a Node.js base image that includes Debian for package management
FROM node:20-slim

# Set working directory
WORKDIR /app

# Install Python, pip, git, and libmagic for python-magic
RUN apt-get update && \
    apt-get install -y python3 python3-pip git libmagic1 libmagic-dev --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy backend dependency file and install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip3 install --no-cache-dir -r /app/backend/requirements.txt

# Copy frontend dependency files and install Node.js dependencies
COPY frontend/package.json frontend/package-lock.json /app/frontend/
RUN cd /app/frontend && npm ci

# Copy the rest of the application code
# This will be overwritten by the volume mount in development,
# but it's good practice to have the code in the image.
COPY . .

# Copy the startup script and make it executable
COPY start-dev.sh .
RUN chmod +x ./start-dev.sh

# Expose ports for frontend (Vite) and backend (Uvicorn)
EXPOSE 5173 8000

# Run the startup script
CMD ["./start-dev.sh"] 