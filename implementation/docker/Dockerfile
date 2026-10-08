ARG BASE_IMAGE=node:22-bookworm-slim
FROM ${BASE_IMAGE}
USER root
ARG CLAUDE_VERSION=2.1.207
ARG CODEX_VERSION=0.140.0
ARG GEMINI_VERSION=0.61.0
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 ca-certificates curl git strace python3-reportlab python3-pypdf \
    python3-docx python3-openpyxl python3-yaml poppler-utils \
    && rm -rf /var/lib/apt/lists/*
RUN if [ "$(codex --version 2>/dev/null)" = "codex-cli ${CODEX_VERSION}" ] \
    && [ "$(claude --version 2>/dev/null)" = "${CLAUDE_VERSION} (Claude Code)" ] \
    && [ "$(gemini --version 2>/dev/null)" = "${GEMINI_VERSION}" ]; then \
        echo "Reusing matching pinned CLI installations"; \
    else \
        npm install -g \
          @anthropic-ai/claude-code@${CLAUDE_VERSION} \
          @openai/codex@${CODEX_VERSION} \
          @google/gemini-cli@${GEMINI_VERSION}; \
    fi
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /workspace
USER node
