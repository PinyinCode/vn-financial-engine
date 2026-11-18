# VN Financial Engine

Independent financial-data and screening engine for Vietnamese listed companies.

## Scope
- Collect quarterly and annual financial statements with source provenance.
- Normalize balance sheet, income statement, and cash-flow concepts.
- Calculate auditable cross-sector and sector-specific metrics.
- Produce transparent Screener scores and evidence-grounded AI analysis.

## Initial sector priorities
Banks, securities, steel, technology, oil & gas, fertilizer, manufacturing, and real estate.
Agriculture and aquaculture are excluded from the initial scope.

## Data integrity
- Preserve source URL, retrieval timestamp, source hash, reporting period, consolidation basis, and restatement history.
- Never mix parent-only and consolidated statements.
- Distinguish quarterly, year-to-date, and annual values.
- Every metric and score must retain formula version and input provenance.
- Do not invent missing data. AI output must separate facts, calculations, interpretation, risks, and missing information.

## Architecture
```text
src/vn_financial_engine/
  domain/
  ingestion/
  normalization/
  metrics/
  scoring/
  ai/
  storage/
config/
tests/
```

Production formulas and source adapters require validation against actual Vietnamese issuer filings before release.
