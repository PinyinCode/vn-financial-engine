from vn_financial_engine.storage.mongo import (
    upsert_statement_records, upsert_market_bars, save_versioned_result,
    record_ingestion_run,
)


class FakeCollection:
    def __init__(self):
        self.calls = []

    def update_one(self, key, update, upsert=False):
        self.calls.append((key, update, upsert))


class FakeDB:
    def __init__(self):
        self.statements = FakeCollection()
        self.market_prices = FakeCollection()
        self.metrics = FakeCollection()
        self.scores = FakeCollection()
        self.valuations = FakeCollection()
        self.ai_analyses = FakeCollection()
        self.ingestion_runs = FakeCollection()

    def __getitem__(self, name):
        return getattr(self, name)


def test_statement_upsert_key_includes_line_id_and_source_version():
    db = FakeDB()
    records = [
        {"symbol":"FPT","statement_type":"IS","period":"2025-Q4",
         "reporting_basis":"CONSOLIDATED","id":"REVENUE","source_field":"ISA01",
         "source_hash":"abc","value":100},
        {"symbol":"FPT","statement_type":"IS","period":"2025-Q4",
         "reporting_basis":"CONSOLIDATED","id":"NET_INCOME","source_field":"ISA20",
         "source_hash":"abc","value":20},
    ]
    assert upsert_statement_records(db, records) == 2
    assert len(db.statements.calls) == 2
    assert db.statements.calls[0][0]["id"] != db.statements.calls[1][0]["id"]


def test_market_bar_and_versioned_results_upsert_by_natural_keys():
    db = FakeDB()
    assert upsert_market_bars(db, [{
        "symbol":"FPT","time":"2026-11-18T09:00:00+07:00",
        "interval":"1D","close":120,
    }]) == 1
    assert save_versioned_result(db, "scores", {
        "symbol":"FPT","as_of":"2026-11-18","formula_version":"score-v2",
        "score":80,
    }) == 1
    assert db.market_prices.calls[0][0]["interval"] == "1D"
    assert db.scores.calls[0][0]["formula_version"] == "score-v2"


def test_versioned_storage_rejects_unknown_collections_and_missing_keys():
    db = FakeDB()
    try:
        save_versioned_result(db, "statements", {})
        assert False
    except ValueError:
        pass
    try:
        upsert_market_bars(db, [{"symbol":"FPT"}])
        assert False
    except ValueError:
        pass


def test_ingestion_run_is_idempotently_keyed():
    db = FakeDB()
    assert record_ingestion_run(db, {"run_id":"run-1","status":"DONE"}) == "run-1"
    assert db.ingestion_runs.calls[0][0] == {"run_id":"run-1"}
