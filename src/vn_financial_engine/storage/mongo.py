"""MongoDB persistence isolated from the legacy quant_db application."""

from __future__ import annotations

import os


COLLECTIONS = (
    "companies", "statements", "market_prices", "metrics",
    "scores", "valuations", "ai_analyses", "ingestion_runs",
)
VERSIONED_COLLECTIONS = {"metrics", "scores", "valuations", "ai_analyses"}


def connect_database():
    uri = os.getenv("MONGO_URI", "").strip()
    if not uri:
        raise RuntimeError("Thiếu MONGO_URI")
    database_name = os.getenv("MONGO_DB_NAME", "vn_financial_engine").strip()
    try:
        from pymongo import MongoClient
    except ImportError as exc:
        raise RuntimeError("Cần cài extra storage: pip install .[storage]") from exc
    client = MongoClient(
        uri, serverSelectionTimeoutMS=15000, connectTimeoutMS=10000,
        socketTimeoutMS=30000, appname="vn_financial_engine",
    )
    client.admin.command("ping")
    return client, client[database_name]


def ensure_indexes(db):
    """Create idempotent indexes; migrate the old statement index safely."""
    db.companies.create_index([("symbol", 1)], unique=True, name="uq_company_symbol")

    statement_keys = [
        ("symbol", 1), ("statement_type", 1), ("period", 1),
        ("reporting_basis", 1), ("id", 1), ("source_field", 1),
        ("source_hash", 1),
    ]
    existing = db.statements.index_information()
    old = existing.get("uq_statement_version")
    old_keys = [tuple(item) for item in old.get("key", [])] if old else None
    if old and old_keys != statement_keys:
        # Old key omitted the financial-statement line ID and collapsed all
        # lines for a period into one unique key. Drop only that obsolete index.
        db.statements.drop_index("uq_statement_version")
    db.statements.create_index(
        statement_keys, unique=True, name="uq_statement_line_version",
    )
    db.market_prices.create_index(
        [("symbol", 1), ("time", 1), ("interval", 1)],
        unique=True, name="uq_market_bar",
    )
    for name in VERSIONED_COLLECTIONS:
        db[name].create_index(
            [("symbol", 1), ("as_of", -1), ("formula_version", 1)],
            unique=True, name=f"uq_{name}_symbol_asof_version",
        )
    db.ingestion_runs.create_index([("started_at", -1)], name="idx_ingestion_started")
    return list(COLLECTIONS)


def _upsert_records(collection, records, key_fields):
    count = 0
    for record in records:
        missing = [field for field in key_fields if record.get(field) in (None, "")]
        if missing:
            raise ValueError(f"Thiếu khóa upsert: {', '.join(missing)}")
        key = {field: record[field] for field in key_fields}
        collection.update_one(
            key,
            {"$set": record, "$setOnInsert": {"created_at": record.get("retrieved_at")}},
            upsert=True,
        )
        count += 1
    return count


def upsert_statement_records(db, records):
    """Upsert individual statement lines, preserving source and restatement versions."""
    return _upsert_records(
        db.statements, records,
        ("symbol", "statement_type", "period", "reporting_basis",
         "id", "source_field", "source_hash"),
    )


def upsert_market_bars(db, records):
    """Upsert canonical OHLCV bars by symbol/timeframe/time."""
    return _upsert_records(db.market_prices, records, ("symbol", "time", "interval"))


def save_versioned_result(db, collection_name, document):
    """Save a reproducible metrics/score/valuation/AI snapshot."""
    if collection_name not in VERSIONED_COLLECTIONS:
        raise ValueError(f"Collection không được phép: {collection_name}")
    return _upsert_records(
        db[collection_name], [document], ("symbol", "as_of", "formula_version")
    )


def record_ingestion_run(db, document):
    if not document.get("run_id"):
        raise ValueError("Thiếu run_id")
    db.ingestion_runs.update_one(
        {"run_id": document["run_id"]},
        {"$set": document},
        upsert=True,
    )
    return document["run_id"]
