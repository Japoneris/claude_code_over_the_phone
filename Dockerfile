FROM python:3.12-slim

# Install essential dependencies including Node.js for Claude Code
RUN apt-get update && apt-get install -y \
    wget \
    bash \
    curl \
    vim \
    nano \
    git \
    sudo \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install ttyd (web-based terminal)
RUN wget https://github.com/tsl0922/ttyd/releases/download/1.7.4/ttyd.x86_64 -O /usr/local/bin/ttyd \
    && chmod +x /usr/local/bin/ttyd

# Install Claude Code
RUN curl -fsSL https://claude.ai/install.sh | bash

# Add Claude to PATH
ENV PATH="/root/.local/bin:$PATH"

# Configure Claude API key helper
RUN mkdir -p /root/.claude && \
    echo '{\n  "apiKeyHelper": "~/.claude/anthropic_key.sh"\n}' > /root/.claude/settings.json && \
    echo '#!/bin/bash\necho "$ANTHROPIC_API_KEY"' > /root/.claude/anthropic_key.sh && \
    chmod +x /root/.claude/anthropic_key.sh

# Set working directory
WORKDIR /home/terminal

# Expose port 7681 (default ttyd port)
EXPOSE 7681

# Run ttyd with bash and proper options for interactive CLIs
CMD ["ttyd", "-p", "7681", "-t", "fontSize=18", "-t", "enableZmodem=true", "-t", "disableLeaveAlert=true", "-W", "bash"]
