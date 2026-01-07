# Docker Container Manager - Streamlit App

A powerful web-based container management interface that allows you to monitor, browse, and download files from any Docker container on your system.

## Features

### Container Selection
- **List all containers**: View all Docker containers (running and stopped)
- **Real-time status**: See container status with color indicators
- **Multi-container support**: Switch between containers easily

### Container Information Dashboard
- **Basic Info**: Container name, ID, image, status, creation date
- **Resource Metrics**: Real-time CPU, memory, and network usage
- **Port Mappings**: View all exposed ports and their bindings
- **Environment Variables**: Inspect environment variables (sensitive ones are hidden)
- **Volumes & Mounts**: See all mounted volumes and bind mounts
- **Container Logs**: View recent logs (last 100 lines)

### File Manager
- **Browse filesystem**: Navigate through any container's filesystem
- **Download files**: Download any file or directory as a TAR archive
- **Quick navigation**: One-click access to common directories (/home, /tmp, /var/log, /etc)
- **Execute commands**: Run shell commands directly in containers

### Container Control
- **Start/Stop/Restart**: Control container state from the UI
- **Real-time updates**: Refresh data on demand

## Quick Start

### Option 1: Run with main docker-compose (Recommended)

From the project root:

```bash
docker-compose build
docker-compose up -d
```

This will start both:
- Web Terminal at http://localhost:7681
- Container Manager at http://localhost:8501

### Option 2: Run standalone

From the app directory:

```bash
cd app
docker-compose up -d
```

Access at: http://localhost:8501

## How It Works

The Streamlit app connects to Docker by mounting the Docker socket:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

This allows the app to:
- List all containers on the host
- Query container stats and information
- Execute commands inside containers
- Download files from containers using Docker's native API

## Usage Examples

### Monitor the Web Terminal Container

1. Open http://localhost:8501
2. Select "web-terminal" from the container dropdown
3. View real-time CPU and memory usage
4. Check environment variables and mounted volumes

### Download Files from a Container

1. Navigate to "File Manager" page
2. Select the target container
3. Browse to the desired directory
4. Enter the path (file or folder) to download
5. Click "Download as TAR"
6. Extract the TAR archive on your local machine

### Execute Commands

1. Go to "File Manager" page
2. Scroll to "Execute Command" section
3. Enter your command (e.g., `cat /etc/hosts`)
4. Click "Execute" to see the output

### Control Container State

From the sidebar:
- **Stop**: Gracefully stop a running container
- **Start**: Start a stopped container
- **Restart**: Restart a container

## Architecture

- **Base Image**: python:3.12-slim
- **Framework**: Streamlit 1.31.0
- **Docker SDK**: docker-py 7.0.0
- **System Monitoring**: psutil 5.9.8
- **Port**: 8501
- **Docker Socket**: Mounted read-only for security

## Security Considerations

### What's Protected:
- Docker socket is mounted **read-only** (`:ro`)
- Sensitive environment variables are automatically hidden
- File operations respect container permissions

### Important Notes:
- The app can **see and interact with ALL containers** on the host
- The app can execute commands in containers (use with caution)
- Consider network isolation in production environments
- Review container logs and actions regularly

### Production Recommendations:
1. Use network policies to restrict access
2. Run behind authentication proxy (e.g., Nginx with basic auth)
3. Limit Docker socket permissions using Docker contexts
4. Monitor app usage through Docker logs

## Troubleshooting

### Cannot connect to Docker

**Error**: `Cannot connect to Docker: ...`

**Solution**: Ensure Docker socket is mounted correctly:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

### Permission denied accessing files

The app respects container filesystem permissions. If you get permission errors:
- Use the "Execute Command" feature to run commands as the container's user
- Check container user permissions with `ls -la`

### Container stats not showing

Stats are only available for **running** containers. Start the container first.

## Dependencies

```
streamlit==1.31.0    # Web framework
psutil==5.9.8        # System metrics
docker==7.0.0        # Docker Python SDK
```

## API Reference

The app uses Docker SDK for Python:
- `docker.from_env()`: Connect to Docker daemon
- `client.containers.list()`: List containers
- `container.stats()`: Get resource usage
- `container.get_archive()`: Download files
- `container.exec_run()`: Execute commands

## Contributing

Feel free to extend the app with additional features:
- Image management
- Network inspection
- Volume management
- Container creation/deletion
- Multi-container operations

## Version

**v2.0** - Docker-aware container manager with multi-container support
