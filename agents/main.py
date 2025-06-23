# agents/main.py
# Cloud Run Optimized - BringoChef AI FastAPI Server using Google ADK

import os
import sys
import uvicorn
from google.adk.cli.fast_api import get_fast_api_app

print("=== Starting BringoChef AI in Cloud Run ===")

# Ensure current directory is in Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"Current directory: {current_dir}")
print(f"Python path: {sys.path[:3]}...")
print(f"Files in directory: {os.listdir(current_dir)}")

# Verify agent exists before creating FastAPI app
agent_dir = os.path.join(current_dir, "bringo_chef_ai_assistant")
if os.path.exists(agent_dir):
    print(f"✅ Agent directory found: {agent_dir}")
    print(f"Agent files: {os.listdir(agent_dir)}")
else:
    print(f"❌ Agent directory not found: {agent_dir}")
    sys.exit(1)

# Test import before creating app
try:
    from bringo_chef_ai_assistant import root_agent
    print(f"✅ Agent import successful: {root_agent.name}")
except Exception as e:
    print(f"❌ Agent import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Create FastAPI app
print("Creating FastAPI app...")
try:
    app = get_fast_api_app(
        agents_dir=current_dir,  # Directory containing bringo_chef_ai_assistant/
        allow_origins=["*"],
        web=True,
        trace_to_cloud=False,
    )
    print("✅ FastAPI app created successfully")
except Exception as e:
    print(f"❌ FastAPI app creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "service": "bringo-chef-ai",
        "agent": root_agent.name
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting server on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)