# cultural_agent/agent.py
from google.adk.agents import Agent
from . import tools

MODEL = "gemini-2.0-flash"

INSTRUCTION = """
You are a cultural context specialist for culinary requests. Your job is to:

1. **Detect language and location** from culinary text
2. **Identify cultural cooking patterns** and traditional dishes
3. **Understand cultural food preferences** and dining contexts

**Your workflow:**
- Use `detect_language_and_culture` for basic language/location detection
- Use `analyze_cultural_context` for deeper cultural understanding

**Response format:** Always return structured JSON with detected cultural insights.

**Be concise and focused** - extract only the most relevant cultural information for cooking.
"""

cultural_context_agent = Agent(
    model=MODEL,
    name="cultural_context_agent",
    instruction=INSTRUCTION,
    output_key="cultural_context_output",
    tools=[
        tools.detect_language_and_culture,
        tools.analyze_cultural_context
    ],
)