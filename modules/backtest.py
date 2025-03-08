from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError
import pandas as pd
import psycopg2
import backtrader as bt
import json
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a router for backtest-related routes
router = APIRouter()

# PostgreSQL connection settings
DB_HOST = "34.88.110.91"  # Public IP of your database
DB_NAME = "postgres"
DB_USER = "QuantCopilot"
DB_PASS = "Nov@21is"

# Database connection function
def get_stock_data(ticker: str, start_date: str, end_date: str):
    try:
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
        )
        query = """
        SELECT date, open, high, low, close, volume
        FROM stock_data
        WHERE ticker = %s AND date BETWEEN %s AND %s
        ORDER BY date ASC;
        """
        df = pd.read_sql(query, conn, params=(ticker, start_date, end_date), parse_dates=['date'])
        conn.close()

        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for given parameters")
        return df

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Backtrader Strategy Class
class DynamicStrategy(bt.Strategy):
    params = (
        ('strategy_rules', []),
    )

    def __init__(self):
        self.rules = self.params.strategy_rules
        self.indicators = {}

        # Complete support for 20+ most used technical indicators
        for rule in self.rules:
            indicator = rule["indicator"]
            period = rule.get("period", 14)

            if indicator == "SMA":
                self.indicators["SMA"] = bt.ind.SMA(period=period)
            elif indicator == "EMA":
                self.indicators["EMA"] = bt.ind.EMA(period=period)
            elif indicator == "RSI":
                self.indicators["RSI"] = bt.ind.RSI(period=period)
            elif indicator == "MACD":
                self.indicators["MACD"] = bt.ind.MACD()
            elif indicator == "Stochastic":
                self.indicators["Stochastic"] = bt.ind.Stochastic()
            elif indicator == "ADX":
                self.indicators["ADX"] = bt.ind.ADX()
            elif indicator == "BollingerBands":
                self.indicators["BollingerBands"] = bt.ind.BollingerBands()
            elif indicator == "Momentum":
                self.indicators["Momentum"] = bt.ind.Momentum()
            elif indicator == "CCI":
                self.indicators["CCI"] = bt.ind.CCI(period=period)
            elif indicator == "ATR":
                self.indicators["ATR"] = bt.ind.ATR(period=period)
            elif indicator == "OBV":
                self.indicators["OBV"] = bt.ind.OBV()
            elif indicator == "WilliamsR":
                self.indicators["WilliamsR"] = bt.ind.WilliamsR()
            elif indicator == "ParabolicSAR":
                self.indicators["ParabolicSAR"] = bt.ind.ParabolicSAR()
            elif indicator == "DMI":
                self.indicators["DMI"] = bt.ind.DMI()
            elif indicator == "TRIX":
                self.indicators["TRIX"] = bt.ind.TRIX()
            elif indicator == "ROC":
                self.indicators["ROC"] = bt.ind.ROC(period=period)
            elif indicator == "MFI":
                self.indicators["MFI"] = bt.ind.MFI()
            elif indicator == "ChaikinMoneyFlow":
                self.indicators["ChaikinMoneyFlow"] = bt.ind.ChaikinMoneyFlow()
            elif indicator == "Volatility":
                self.indicators["Volatility"] = bt.ind.StdDev(period=period)

    def next(self):
        for rule in self.rules:
            condition = rule["condition"]
            try:
                if rule["type"] == "entry" and eval(condition):
                    self.buy()
                elif rule["type"] == "exit" and eval(condition):
                    self.sell()
            except Exception as e:
                logger.error(f"Error evaluating condition '{condition}': {str(e)}")

# Backtest execution
def run_backtest(stock_data: pd.DataFrame, strategy_logic: dict):
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=stock_data.set_index("date"))
    cerebro.adddata(data)

    cerebro.addstrategy(DynamicStrategy, strategy_rules=strategy_logic["strategy"])
    cerebro.broker.set_cash(10000)
    cerebro.run()

    return cerebro.broker.getvalue()

# Request model for backtesting
class BacktestRequest(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    strategy_logic: dict

# Route to handle backtest requests with robust JSON handling
@router.post("/backtest")
def backtest(request: BacktestRequest):
    try:
        stock_data = get_stock_data(request.ticker, request.start_date, request.end_date)
        final_value = run_backtest(stock_data, request.strategy_logic)
        return {"final_portfolio_value": final_value}
    except ValidationError as ve:
        logger.error(f"Validation error: {ve}")
        raise HTTPException(status_code=422, detail=f"Validation error: {ve}")
    except json.JSONDecodeError as je:
        logger.error(f"JSON decode error: {je}")
        raise HTTPException(status_code=400, detail=f"JSON decode error: {je}")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unhandled exception: {str(e)}")

# Register routes function
def register_routes(app):
    app.include_router(router)
