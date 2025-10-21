#!/bin/bash
# Lint script for local development

echo "🔍 Running Ruff linter..."
ruff check . --fix

echo ""
echo "✨ Running Ruff formatter..."
ruff format .

echo ""
echo "✅ Linting complete!"
