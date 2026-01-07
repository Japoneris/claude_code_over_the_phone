# Streamlit Container Manager

A web-based file manager and container information dashboard for Docker containers.

## Features

- **Container Information**: View system metrics (CPU, memory, disk usage), environment variables, and running processes
- **File Browser**: Navigate through the container filesystem
- **File Download**: Download files or entire directories as tar.gz archives

## Quick Start

### Build and Run

```bash
cd app
docker-compose up -d
```

The Streamlit app will be available at: http://localhost:8501

### Stop the Application

```bash
docker-compose down
```

## Usage

### Container Info Page
- View real-time system metrics
- Check environment variables
- Monitor running processes

### File Manager Page
1. Browse directories using the path input
2. View file listings with sizes and modification dates
3. Enter a path (file or folder) to download
4. Click "Create Archive" to generate a tar.gz file
5. Download the archive to your local machine

## Accessing Files from Another Container

If you want the Streamlit app to access files from the web-terminal container, update `docker-compose.yml`:

```yaml
version: '3.8'

services:
  streamlit-app:
    build: .
    container_name: streamlit-manager
    ports:
      - "8501:8501"
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ../terminal-data:/mnt/terminal:ro  # Mount terminal container data
```

Then run the web-terminal with a named volume:

```yaml
# In main docker-compose.yml
volumes:
  - terminal-data:/home/terminal

volumes:
  terminal-data:
```

## Architecture

- **Base Image**: python:3.12-slim
- **Framework**: Streamlit
- **Port**: 8501
- **Dependencies**: streamlit, psutil

## Security Notes

- Sensitive environment variables (containing API_KEY, PASSWORD, SECRET, TOKEN, ANTHROPIC) are automatically hidden in the UI
- The file browser respects filesystem permissions
- Consider running in read-only mode for production use
