from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai  # Ensure you have `openai` installed: pip install openai
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
    ticker: str
    start_date: str
    end_date: str

# Function to generate structured JSON strategy logic using GPT
def generate_strategy_logic(description: str, ticker: str, start_date: str, end_date: str):
    prompt = f"""
    Convert the following trading strategy description into a structured JSON format.

    "{description}"

    The output MUST be valid JSON, following this format:

    {{
      "ticker": "{ticker}",
      "start_date": "{start_date}",
      "end_date": "{end_date}",
      "strategy_logic": {{
        "strategy": [
          {{
            "ticker": "{ticker}",
            "indicator": "<Technical Indicator>",
            "period": <Period>,  # Ensure this is always a valid integer (default RSI: 14)
            "type": "entry" or "exit",
            "condition": "self.data.close[0] > self.indicators['SMA'][0]"
          }},
          {{
            "ticker": "{ticker}",
            "indicator": "daysSinceEntry",
            "period": <Exit Period>,
            "type": "exit",
            "condition": "self.bar_executed + <Exit Period> <= len(self)"
          }}
        ]
      }}
    }}

    - Ensure all indicators have a valid "period" value. If missing, set RSI=14, SMA=50.
    - Use double quotes ("") for all keys and string values.
    - If the strategy includes an exit after N days, use `"daysSinceEntry"` as the indicator.
    - Ensure the response is valid JSON.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial trading assistant. You generate structured trading strategies in JSON format."},
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
            strategy_logic = json.loads(strategy_logic_raw)  # ✅ Strict JSON validation

            # ✅ FIX: Ensure all indicators have a period
            for rule in strategy_logic["strategy_logic"]["strategy"]:
                if "period" not in rule or rule["period"] is None:
                    if rule["indicator"] == "RSI":
                        rule["period"] = 14  # Set default for RSI
                    elif rule["indicator"] == "SMA":
                        rule["period"] = 50  # Set default for SMA
                    elif rule["indicator"] == "EMA":
                        rule["period"] = 20  # Set default for EMA
                    else:
                        rule["period"] = 10  # Fallback default

            logger.debug(f"Fixed Strategy Logic: {strategy_logic}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {strategy_logic_raw}")
            raise HTTPException(status_code=500, detail=f"Failed to parse OpenAI response as JSON. Error: {str(e)}")

        return strategy_logic  # Convert string to dictionary

    except Exception as e:
        logger.error(f"Error generating strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating strategy: {str(e)}")

# API Endpoint for generating trading strategies
@router.post("/generate_strategy")
def generate_strategy(request: StrategyRequest):
    """
    API endpoint to generate structured strategy logic from a natural language description.
    """
    strategy_logic = generate_strategy_logic(request.description, request.ticker, request.start_date, request.end_date)
    return strategy_logic

# Register this module in FastAPI
def register_routes(app):
    app.include_router(router)
