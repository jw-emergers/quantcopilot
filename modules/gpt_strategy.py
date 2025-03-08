from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai
import os
import json
import logging

# Create a router for GPT-related routes
router = APIRouter()

# OpenAI API Key (set as an environment variable for security)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key. Set it as an environment variable.")

# Initialize OpenAI Client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Request model
class StrategyRequest(BaseModel):
    description: str  # User-provided natural language description of the strategy

# Function to generate structured JSON strategy logic using GPT
def generate_strategy_logic(description: str):
    prompt = f"""
    Convert the following trading strategy description into a structured JSON format.

    Ensure:
    - The "condition" field correctly escapes double quotes inside strings.
    - The JSON is valid and contains no additional text.

    Example output:
    {{
      "strategy": [
        {{
          "indicator": "SMA",
          "period": 50,
          "type": "entry",
          "condition": "self.data.close[0] > self.indicators[\\"SMA\\"][0]"
        }},
        {{
          "indicator": "SMA",
          "period": 50,
          "type": "exit",
          "condition": "self.data.close[0] < self.indicators[\\"SMA\\"][0]"
        }}
      ]
    }}

    Now, generate a strategy for:
    "{description}"
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial trading assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )

        # Extract GPT-generated response
        strategy_logic_raw = response.choices[0].message.content.strip()

        # Log raw response
        logger.debug(f"Raw GPT Response: {strategy_logic_raw}")

        # Ensure response is valid JSON
        try:
            strategy_logic = json.loads(strategy_logic_raw)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse OpenAI response: {strategy_logic_raw}")
            raise HTTPException(status_code=500, detail="Failed to parse OpenAI response as JSON.")

        # Log parsed JSON response
        logger.debug(f"Parsed Strategy Logic: {strategy_logic}")

        return strategy_logic

    except Exception as e:
        logger.error(f"Error generating strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating strategy: {str(e)}")

# API Endpoint for generating trading strategies
@router.post("/generate_strategy")
def generate_strategy(request: StrategyRequest):
    """
    API endpoint to generate structured strategy logic from a natural language description.
    """
    strategy_logic = generate_strategy_logic(request.description)
    return {"strategy_logic": strategy_logic}

# Register this module in FastAPI
def register_routes(app):
    app.include_router(router)
