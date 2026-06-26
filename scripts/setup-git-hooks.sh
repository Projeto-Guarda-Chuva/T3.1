#!/bin/sh

git config core.hooksPath .githooks

find .githooks -type f -exec chmod +x {} \; 2>/dev/null || true

echo "Git hooks configurados."
