#!/usr/bin/env bash

echo "🚀 Building Django project for Render..."


pip install -r requirements.txt


mkdir -p staticfiles


python manage.py collectstatic --noinput --clear


python manage.py migrate --noinput

echo "✅ Build completed successfully!"