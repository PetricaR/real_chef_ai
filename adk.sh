# Set your Google Cloud Project ID
export GOOGLE_CLOUD_PROJECT="formare-ai"

# Set your desired Google Cloud Location
export GOOGLE_CLOUD_LOCATION="europe-west4" # Example location

# Set the path to your agent code directory
export AGENT_PATH="./agent" # Assuming capital_agent is in the current directory

# Set a name for your Cloud Run service (optional)
export SERVICE_NAME="real-chef-ai-assistant"

# Set an application name (optional)
export APP_NAME="real-chef-ai-assistant"


adk deploy cloud_run \
--project=$GOOGLE_CLOUD_PROJECT \
--region=$GOOGLE_CLOUD_LOCATION \
--service_name=$SERVICE_NAME \
--app_name=$APP_NAME \
--with_ui \
$AGENT_PATH