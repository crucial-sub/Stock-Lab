#!/bin/sh
set -e

echo "📦 Installing dependencies..."
pnpm install

echo "🚀 Starting Next.js development server..."
exec pnpm exec next dev
