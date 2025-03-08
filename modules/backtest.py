from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import psycopg2
import backtrader as bt
import logging

# Create a router for backtest-related routes
router = APIRouter()

# PostgreSQL connection settings
DB_HOST = "34.88.110.91"  # Public IP of your database
DB_NAME = "postgres"
DB_USER = "QuantCopilot"
DB_PASS = "Nov@21is"

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database connection function
def get_stock_data(ticker: str, start_date: str, end_date: str):
    """
    Fetch stock data from PostgreSQL database.
    """
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
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Backtrader Strategy Class
class DynamicStrategy(bt.Strategy):
    params = (("strategy_rules", []),)

    def __init__(self):
        self.rules = self.params.strategy_rules
        self.indicators = {}
        self.bar_executed = 0  # Tracks when a trade was entered

        for rule in self.rules:
            if rule["indicator"] == "SMA":
                self.indicators["SMA"] = bt.ind.SMA(period=rule["period"])
            elif rule["indicator"] == "EMA":
                self.indicators["EMA"] = bt.ind.EMA(period=rule["period"])
            elif rule["indicator"] == "RSI":
                self.indicators["RSI"] = bt.ind.RSI(period=rule["period"])
            elif rule["indicator"] == "MACD":
                self.indicators["MACD"] = bt.ind.MACD()
            elif rule["indicator"] == "Stochastic":
                self.indicators["Stochastic"] = bt.ind.Stochastic()
            elif rule["indicator"] == "ADX":
                self.indicators["ADX"] = bt.ind.ADX()
            elif rule["indicator"] == "BollingerBands":
                self.indicators["BollingerBands"] = bt.ind.BollingerBands()
            elif rule["indicator"] == "Momentum":
                self.indicators["Momentum"] = bt.ind.Momentum()
            elif rule["indicator"] == "CCI":
                self.indicators["CCI"] = bt.ind.CCI(period=rule["period"])
            elif rule["indicator"] == "ATR":
                self.indicators["ATR"] = bt.ind.ATR(period=rule["period"])
            elif rule["indicator"] == "OBV":
                self.indicators["OBV"] = bt.ind.OBV()
            elif rule["indicator"] == "WilliamsR":
                self.indicators["WilliamsR"] = bt.ind.WilliamsR()
            elif rule["indicator"] == "ParabolicSAR":
                self.indicators["ParabolicSAR"] = bt.ind.ParabolicSAR()
            elif rule["indicator"] == "DMI":
                self.indicators["DMI"] = bt.ind.DMI()
            elif rule["indicator"] == "TRIX":
                self.indicators["TRIX"] = bt.ind.TRIX()
            elif rule["indicator"] == "ROC":
                self.indicators["ROC"] = bt.ind.ROC(period=rule["period"])
            elif rule["indicator"] == "MFI":
                self.indicators["MFI"] = bt.ind.MFI()
            elif rule["indicator"] == "ChaikinMoneyFlow":
                self.indicators["ChaikinMoneyFlow"] = bt.ind.ChaikinMoneyFlow()
            elif rule["indicator"] == "Volatility":
                self.indicators["Volatility"] = bt.ind.StdDev(period=rule["period"])
            elif rule["indicator"] == "daysSinceEntry":
                self.bar_executed = 0  # Initialize bar execution tracker

    def next(self):
        for rule in self.rules:
            try:
                if rule["type"] == "entry" and eval(rule["condition"]):
                    self.buy()
                    self.bar_executed = len(self)  # Track entry point
                elif rule["type"] == "exit" and rule["indicator"] == "daysSinceEntry":
                    if self.bar_executed + rule["period"] <= len(self):
                        self.sell()
                elif rule["type"] == "exit" and eval(rule["condition"]):
                    self.sell()
            except Exception as e:
                logger.error(f"Error evaluating rule: {rule}. Error: {e}")


# Backtest execution
def run_backtest(stock_data: pd.DataFrame, strategy_logic: dict):
    """
    Run a backtest using Backtrader based on the given strategy logic and stock data.
    """
    cerebro = bt.Cerebro()
    data = bt.feeds.PandasData(dataname=stock_data.set_index("date"))
    cerebro.adddata(data)

    cerebro.addstrategy(DynamicStrategy, strategy_rules=strategy_logic["strategy"])
    cerebro.broker.set_cash(10000)  # Starting capital
    cerebro.run()

    return cerebro.broker.getvalue()


# Request model for backtesting
class BacktestRequest(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    strategy_logic: dict  # ✅ Now expects a dictionary


# Route to handle backtest requests
@router.post("/backtest")
def backtest(request: BacktestRequest):
    """
    API endpoint to execute a backtest.
    """
    try:
        stock_data = get_stock_data(request.ticker, request.start_date, request.end_date)
        final_value = run_backtest(stock_data, request.strategy_logic)
        return {"final_portfolio_value": final_value}
    except Exception as e:
        logger.error(f"Error in backtest execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in backtest execution: {str(e)}")


# Register routes
def register_routes(app):
    app.include_router(router)
