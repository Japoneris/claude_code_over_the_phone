# Web-Based Linux Terminal

A Docker container that provides a Linux terminal accessible via web browser - perfect for smartphones and devices without a built-in terminal.

## Features

- Access a full Linux terminal from any web browser
- Touch-friendly interface for smartphones
- Pre-installed tools: bash, vim, nano, git, python3, curl, etc.
- Non-root user with sudo access

## Quick Start

### Using Docker Compose (Recommended)

1. Build and start the container:
```bash
docker-compose up -d
```

2. Access the terminal:
   - Open your browser (including smartphone) and navigate to:
   - `http://localhost:7681`
   - Or from another device: `http://<your-server-ip>:7681`

3. Stop the container:
```bash
docker-compose down
```

### Using Docker directly

1. Build the image:
```bash
docker build -t web-terminal .
```

2. Run the container:
```bash
docker run -d -p 7681:7681 --name web-terminal web-terminal
```

3. Access via browser at `http://localhost:7681`

## Default Credentials

- Username: `terminal`
- Password: `terminal`

Use `sudo` for administrative tasks.

## Accessing from Smartphone

1. Make sure your smartphone is on the same network as the server
2. Find your server's IP address: `hostname -I` or `ip addr show`
3. On your smartphone browser, navigate to: `http://<server-ip>:7681`
4. You now have a full Linux terminal on your phone!

## Tips

- The terminal is fully interactive and supports all standard terminal features
- You can copy/paste using browser context menu
- Touch and hold on mobile devices for selection
- Supports multi-touch for scrolling

## Security Notes

- Default password is set to `terminal` - change it after first login:
  ```bash
  sudo passwd terminal
  ```
- For production use, consider adding authentication or running behind a reverse proxy with HTTPS
- Only expose port 7681 on trusted networks

## Customization

Edit the Dockerfile to:
- Add more packages
- Change default user
- Install additional tools
- Modify terminal settings
