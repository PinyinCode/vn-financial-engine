"""MongoDB persistence isolated from the legacy quant_db application."""

from __future__ import annotations

import os
from pymongo import MongoClient


COLLECTIONS = (
    "companies", "statements", "market_prices", "metrics",
    "scores", "valuations", "ai_analyses", "ingestion_runs",
)


def connect_database():
    uri = os.getenv("MONGO_URI", "").strip()
    if not uri:
        raise RuntimeError("Thiếu MONGO_URI")
    database_name = os.getenv("MONGO_DB_NAME", "vn_financial_engine").strip()
    client = MongoClient(
        uri, serverSelectionTimeoutMS=15000, connectTimeoutMS=10000,
        socketTimeoutMS=30000, appname="vn_financial_engine",
    )
    client.admin.command("ping")
    return client, client[database_name]


def ensure_indexes(db):
    """Create idempotent indexes for point-in-time and versioned records."""
    db.companies.create_index([("symbol", 1)], unique=True, name="uq_company_symbol")
    db.statements.create_index(
        [("symbol", 1), ("statement_type", 1), ("period", 1),
         ("reporting_basis", 1), ("source_hash", 1)],
        unique=True, name="uq_statement_version",
    )
    db.market_prices.create_index(
        [("symbol", 1), ("time", 1), ("interval", 1)],
        unique=True, name="uq_market_bar",
    )
    for name in ("metrics", "scores", "valuations", "ai_analyses"):
        db[name].create_index(
            [("symbol", 1), ("as_of", -1), ("formula_version", 1)],
            name=f"idx_{name}_symbol_asof",
        )
    db.ingestion_runs.create_index([("started_at", -1)], name="idx_ingestion_started")
    return list(COLLECTIONS)
