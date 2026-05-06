#!/bin/bash
# HOS ERP — Start Script
# Run this to start the Django dev server

set -e

# Load environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
  export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# Activate virtualenv
if [ -d "$HOME/.venv/hos-erp" ]; then
  source "$HOME/.venv/hos-erp/bin/activate"
fi

cd "$SCRIPT_DIR"

echo "Starting HOS ERP..."
echo "  Django:  http://localhost:8000"
echo "  Admin:   http://localhost:8000/admin"
echo ""

# Ensure migrations are up to date
python manage.py migrate --run-syncdb 2>/dev/null || true

# Start server
python manage.py runserver 0.0.0.0:8000