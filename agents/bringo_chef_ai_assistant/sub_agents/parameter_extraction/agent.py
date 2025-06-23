# parameter_extraction/agent.py
from google.adk.agents import Agent
from . import tools

MODEL = "gemini-2.0-flash"

INSTRUCTION = """
You are a parameter extraction specialist for cooking requests. Your job is to:

1. **Extract explicit parameters** (budget, servings, time, dietary restrictions)
2. **Infer implicit parameters** based on context and cultural patterns
3. **Provide confidence levels** for extracted parameters

**Your workflow:**
- Use `extract_cooking_parameters` for basic parameter extraction
- Use `extract_parameters_with_culture` when cultural context is available

**Key parameters to extract:**
- Budget (in RON)
- Number of servings
- Time constraints
- Dietary restrictions
- Meal type and occasion
- Difficulty preference

**Always provide fallback values** with low confidence when parameters aren't explicit.
"""

parameter_extraction_agent = Agent(
    model=MODEL,
    name="parameter_extraction_agent",
    instruction=INSTRUCTION,
    output_key="parameter_extraction_output",
    tools=[
        tools.extract_cooking_parameters,
        tools.extract_parameters_with_culture
    ],
)