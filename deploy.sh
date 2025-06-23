#!/bin/bash

set -e  # Exit on any error
set -o pipefail

echo "=== BringoChef AI Deployment Script ==="

# Check if we're in the right directory
if [ ! -d "agents" ]; then
    echo "❌ Error: 'agents' directory not found."
    echo "➡️  Make sure you're running this from the 'real_chef_ai' root directory."
    exit 1
fi

echo "✅ Found 'agents' directory"

# Check for requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: 'requirements.txt' not found in root directory."
    exit 1
fi

# Optional Dockerfile check
DOCKERFILE_PRESENT=false
if [ -f "Dockerfile" ]; then
    DOCKERFILE_PRESENT=true
fi

echo "📦 Preparing deployment files..."
cp requirements.txt agents/
$DOCKERFILE_PRESENT && cp Dockerfile agents/

cd agents
echo "📁 Changed to directory: $(pwd)"

# Validate required files in agents/
echo "📋 Checking required files..."
missing=false

if [ ! -d "bringo_chef_ai_assistant" ]; then
    echo "❌ Missing: bringo_chef_ai_assistant directory"
    missing=true
fi

if [ ! -f "main.py" ]; then
    echo "❌ Missing: main.py"
    missing=true
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ Missing: requirements.txt (copy may have failed)"
    missing=true
fi

if $missing; then
    echo "❌ One or more required files are missing. Exiting."
    exit 1
fi

echo "✅ All required files found"

# Set environment variables
export GOOGLE_CLOUD_PROJECT="formare-ai"
export GOOGLE_CLOUD_LOCATION="europe-west4"

echo "🚀 Deploying to Google Cloud Run..."

gcloud run deploy bringo-chef-ai-assistant \
  --source . \
  --region "$GOOGLE_CLOUD_LOCATION" \
  --project "$GOOGLE_CLOUD_PROJECT" \
  --allow-unauthenticated \
  --port 8080 \
  --timeout 600 \
  --memory 4Gi \
  --cpu 2 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION,GOOGLE_GENAI_USE_VERTEXAI=True,PYTHONPATH=/app"

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"

    SERVICE_URL=$(gcloud run services describe bringo-chef-ai-assistant \
      --region="$GOOGLE_CLOUD_LOCATION" \
      --format="value(status.url)")

    echo "🌐 Service URL: $SERVICE_URL"
    echo "📱 Web UI: $SERVICE_URL"
else
    echo "❌ Deployment failed"
    exit 1
fi

# Cleanup
echo "🧹 Cleaning up temporary deployment files..."
rm -f requirements.txt
$DOCKERFILE_PRESENT && rm -f Dockerfile

echo "✅ Done"
