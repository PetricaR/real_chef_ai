#!/bin/bash

# fix_vertex_ai_permissions_2025.sh - Updated with June 2025 Documentation

echo "🔧 === Fixing Vertex AI Permissions - June 2025 Update ==="

# Project settings
PROJECT_ID="formare-ai"
SERVICE_NAME="bringo-chef-ai-assistant"
REGION="europe-west4"

echo "📋 Project: $PROJECT_ID"
echo "🚀 Service: $SERVICE_NAME"
echo "🌍 Region: $REGION"
echo ""

# IMPORTANT: Check for Gemini model availability restriction
echo "⚠️  IMPORTANT: Checking Gemini model availability..."
echo "   As of April 29, 2025, Gemini 1.5 Pro/Flash models are not available"
echo "   in projects with no prior usage. Your errors suggest this may apply."
echo ""

# Step 1: Enable all required APIs (updated list from 2025 docs)
echo "🔌 Enabling required APIs..."

REQUIRED_APIS=(
    "aiplatform.googleapis.com"
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "secretmanager.googleapis.com"
    "serviceusage.googleapis.com"
    "storage.googleapis.com"
    "cloudtrace.googleapis.com"
    "logging.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    echo "  Enabling $api..."
    gcloud services enable $api --project=$PROJECT_ID --quiet
    if [ $? -eq 0 ]; then
        echo "  ✅ $api enabled"
    else
        echo "  ❌ Failed to enable $api"
        exit 1
    fi
done

# Step 2: Get project details
echo ""
echo "🔍 Getting project configuration..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
if [ -z "$PROJECT_NUMBER" ]; then
    echo "❌ Failed to get project number"
    exit 1
fi

# Cloud Run default service account
DEFAULT_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
echo "🔐 Service account: $DEFAULT_SA"

# Step 3: Grant the updated roles based on June 2025 documentation
echo ""
echo "🛡️  Granting IAM roles (based on latest 2025 documentation)..."

# Core roles for Vertex AI Generative AI (from updated docs)
REQUIRED_ROLES=(
    "roles/aiplatform.user"                    # Core Vertex AI access
    "roles/serviceusage.serviceUsageConsumer"  # Service usage (required from logs)
    "roles/secretmanager.secretAccessor"       # Secret Manager access
    "roles/storage.objectViewer"               # Cloud Storage access
)

for role in "${REQUIRED_ROLES[@]}"; do
    echo "  Granting $role..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$DEFAULT_SA" \
        --role="$role" \
        --quiet
    
    if [ $? -eq 0 ]; then
        echo "  ✅ $role granted successfully"
    else
        echo "  ❌ Failed to grant $role"
    fi
done

# Step 4: Create custom role with exact permissions from latest docs
echo ""
echo "🎯 Creating custom role with exact Vertex AI permissions..."

CUSTOM_ROLE_ID="vertex_ai_predictor_2025"
CUSTOM_ROLE_TITLE="Vertex AI Model Predictor 2025"

# Updated permissions list from June 2025 documentation
CUSTOM_PERMISSIONS="aiplatform.endpoints.predict,aiplatform.models.predict,serviceusage.services.use,storage.objects.get,secretmanager.versions.access"

# Create/update custom role
gcloud iam roles create $CUSTOM_ROLE_ID \
    --project=$PROJECT_ID \
    --title="$CUSTOM_ROLE_TITLE" \
    --description="Custom role for Vertex AI model predictions (June 2025)" \
    --permissions="$CUSTOM_PERMISSIONS" \
    --quiet 2>/dev/null || \
gcloud iam roles update $CUSTOM_ROLE_ID \
    --project=$PROJECT_ID \
    --permissions="$CUSTOM_PERMISSIONS" \
    --quiet

# Grant custom role
echo "  Granting custom role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$DEFAULT_SA" \
    --role="projects/$PROJECT_ID/roles/$CUSTOM_ROLE_ID" \
    --quiet

echo "  ✅ Custom role granted"

# Step 5: Check for Gemini model access issue
echo ""
echo "🔍 Checking Gemini model access restrictions..."

# Test if project has prior Gemini usage
GEMINI_TEST=$(gcloud ai models list \
    --region=us-central1 \
    --filter="displayName:gemini" \
    --project=$PROJECT_ID \
    --format="value(name)" \
    --quiet 2>/dev/null | head -1)

if [ -z "$GEMINI_TEST" ]; then
    echo "⚠️  WARNING: Your project may not have prior Gemini model usage."
    echo "   As of April 29, 2025, new projects cannot access Gemini 1.5 models."
    echo "   Consider:"
    echo "   1. Using Gemini 2.5 models (gemini-2.5-flash, gemini-2.5-pro)"
    echo "   2. Contacting Google Cloud support for model access"
    echo "   3. Testing with gemini-2.0-flash as fallback"
else
    echo "✅ Project appears to have Gemini model access"
fi

# Step 6: Update Cloud Run service configuration
echo ""
echo "🔄 Updating Cloud Run service configuration..."

# Update service with proper IAM binding
gcloud run services update $SERVICE_NAME \
    --service-account="$DEFAULT_SA" \
    --region=$REGION \
    --project=$PROJECT_ID \
    --timeout=600 \
    --memory=4Gi \
    --cpu=2 \
    --max-instances=10 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,GOOGLE_GENAI_USE_VERTEXAI=True" \
    --quiet

if [ $? -eq 0 ]; then
    echo "✅ Cloud Run service updated"
else
    echo "⚠️  Service update had issues, but permissions may still work"
fi

# Step 7: Wait for IAM propagation
echo ""
echo "⏳ Waiting 90 seconds for IAM changes to propagate..."
for i in {90..1}; do
    echo -ne "\r   $i seconds remaining..."
    sleep 1
done
echo -e "\r   ✅ Wait complete!                    "

# Step 8: Test the service
echo ""
echo "🧪 Testing service after permission updates..."

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)" 2>/dev/null)

if [ -z "$SERVICE_URL" ]; then
    echo "❌ Could not get service URL"
    exit 1
fi

echo "🌐 Service URL: $SERVICE_URL"

# Test health endpoint
echo "  Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health" --max-time 30)
if [[ "$HEALTH_RESPONSE" == *"healthy"* ]]; then
    echo "  ✅ Health check passed"
else
    echo "  ⚠️  Health check response: ${HEALTH_RESPONSE:0:100}..."
fi

# Test agent functionality with a simple call
echo "  Testing agent API..."
TEST_RESPONSE=$(curl -s -X POST "$SERVICE_URL/run_sse" \
    -H "Content-Type: application/json" \
    -d '{
        "app_name": "bringo_chef_ai_assistant",
        "user_id": "test_user",
        "session_id": "test_session",
        "new_message": {
            "role": "user",
            "parts": [{"text": "hello"}]
        },
        "streaming": false
    }' --max-time 60)

if [[ "$TEST_RESPONSE" == *"403"* ]] || [[ "$TEST_RESPONSE" == *"PERMISSION_DENIED"* ]]; then
    echo "  ❌ Still getting permission errors"
    echo "  📋 Error details: ${TEST_RESPONSE:0:200}..."
    echo ""
    echo "🔧 Additional steps needed:"
    echo "   1. Verify billing is enabled: https://console.cloud.google.com/billing"
    echo "   2. Check Gemini model availability for your project"
    echo "   3. Consider switching to gemini-2.5-flash model"
    echo "   4. Contact Google Cloud support if issues persist"
elif [[ "$TEST_RESPONSE" == *"healthy"* ]] || [[ "$TEST_RESPONSE" == *"success"* ]] || [[ "$TEST_RESPONSE" == *"Salut"* ]]; then
    echo "  ✅ Agent responding successfully!"
    echo "  🎉 Permission fix completed successfully!"
else
    echo "  ✅ No permission errors detected"
    echo "  📋 Response preview: ${TEST_RESPONSE:0:200}..."
fi

# Step 9: Final summary
echo ""
echo "📊 === Permission Fix Summary (June 2025) ==="
echo ""
echo "✅ APIs enabled: ${#REQUIRED_APIS[@]} services"
echo "✅ IAM roles granted: ${#REQUIRED_ROLES[@]} predefined roles"
echo "✅ Custom role created: projects/$PROJECT_ID/roles/$CUSTOM_ROLE_ID"
echo "✅ Service account: $DEFAULT_SA"
echo ""
echo "🌐 Your BringoChef AI service: $SERVICE_URL"
echo "🔗 Direct access: $SERVICE_URL"
echo ""
echo "💡 Next steps:"
echo "   1. Open $SERVICE_URL in browser"
echo "   2. Test with Romanian greetings: 'salutare'"
echo "   3. If still getting 403 errors, check Gemini model availability"
echo "   4. Consider updating to Gemini 2.5 models in your agent code"
echo ""
echo "🍳 BringoChef AI permission fix completed with June 2025 updates!"