from fastapi import APIRouter
from pydantic import BaseModel
import psycopg2

router = APIRouter()

# Request model for fetching stock data
class StockQuery(BaseModel):
    ticker: str
    start_date: str
    end_date: str

@router.post("/query_stock")
def query_stock(data: StockQuery):
    """Fetch stock data from PostgreSQL based on ticker and date range."""
    try:
        conn = psycopg2.connect(
            host="34.88.110.91", database="postgres", user="QuantCopilot", password="Nov@21is"
        )
        cursor = conn.cursor()

        query = """
        SELECT date, open, high, low, close, volume, resolution
        FROM stock_data
        WHERE ticker = %s AND date BETWEEN %s AND %s
        ORDER BY date ASC;
        """
        cursor.execute(query, (data.ticker, data.start_date, data.end_date))
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return {"ticker": data.ticker, "data": rows}

    except Exception as e:
        return {"error": str(e)}

def register_routes(app):
    app.include_router(router, prefix="/api", tags=["Stock Query"])
