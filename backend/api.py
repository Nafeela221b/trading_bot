# backend/api.py
import os
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, select, MetaData, Table
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env
load_dotenv()

# Connect to PostgreSQL
DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL, future=True)
meta = MetaData()
meta.reflect(bind=engine)

# Reflect tables
backtests = meta.tables.get('backtests')
trades = meta.tables.get('trades')
ohlc = meta.tables.get('ohlc')

# Set up FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

@app.get("/backtests")
def list_backtests():
    with engine.connect() as conn:
        rows = conn.execute(
            select(
                backtests.c.id,
                backtests.c.name,
                backtests.c.symbol,
                backtests.c.total_return_pct
            )
        ).mappings().all()
    return rows


@app.get("/backtests/{bt_id}/ohlc")
def get_ohlc(bt_id: int, symbol: str = None):
    with engine.connect() as conn:
        if symbol:
            stmt = select(
                ohlc.c.timestamp,
                ohlc.c.open,
                ohlc.c.high,
                ohlc.c.low,
                ohlc.c.close
            ).where(ohlc.c.symbol == symbol)
        else:
            stmt = select(
                ohlc.c.timestamp,
                ohlc.c.open,
                ohlc.c.high,
                ohlc.c.low,
                ohlc.c.close
            )
        rows = conn.execute(stmt).mappings().all()
    return rows


@app.get("/backtests/{bt_id}/trades")
def get_trades(bt_id: int):
    with engine.connect() as conn:
        stmt = select(trades).where(trades.c.backtest_id == bt_id)
        rows = conn.execute(stmt).mappings().all()
    return rows
