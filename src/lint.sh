#!/bin/bash

# Default: Don't run TypeScript-related commands
RUN_TS=false

# Parse arguments
for arg in "$@"; do
  if [ "$arg" == "--ts" ]; then
    RUN_TS=true
  fi
done

# Always run Python linting and formatting
uv run isort .
uv run ruff check .
uv run ruff format .

# Always run HTML formatting
git ls-files -z -- '*.html' | xargs -0r djade --target-version 5.1

# Run TypeScript/JavaScript related commands only if --ts flag is provided
if [ "$RUN_TS" = true ]; then
  npm run lint
  npm run format
  npm run typecheck
  echo "TypeScript checks completed."
else
  echo "Skipping TypeScript checks. Use --ts to run them."
fi