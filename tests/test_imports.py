def test_all_adapters_import_without_optional_runtime_services():
    from vn_financial_engine.sources.vietcap import _fetch_bctc_ssi
    from vn_financial_engine.sources.ssi import SSIPriceAdapter
    from vn_financial_engine.technical.analyzer import ProfessionalTechnicalAnalyzer
    from vn_financial_engine.ai.client import run_analysis
    from vn_financial_engine.storage.mongo import connect_database
    assert callable(_fetch_bctc_ssi)
    assert SSIPriceAdapter is not None
    assert ProfessionalTechnicalAnalyzer is not None
    assert callable(run_analysis)
    assert callable(connect_database)
