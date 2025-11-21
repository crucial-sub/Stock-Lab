#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env.local (only key=value lines)
export $(grep -v '^#' .env.local | grep '=' | xargs)

# Run migration script
python -m scripts.migrate_strategies
