from vn_financial_engine.valuation.peers import build_peer_multiples


def test_peer_median_excludes_subject_and_other_sectors():
    peers = [
        {"symbol":"FPT","sector":"TECHNOLOGY","pe":20},
        {"symbol":"CMG","sector":"TECHNOLOGY","pe":15},
        {"symbol":"ELC","sector":"TECHNOLOGY","pe":18},
        {"symbol":"HPG","sector":"STEEL","pe":8},
    ]
    result = build_peer_multiples(
        peers, subject_symbol="FPT", sector="TECHNOLOGY", min_peers=3
    )
    assert result["multiples"]["pe"]["median"] is None
    assert result["multiples"]["pe"]["peer_count"] == 2
    assert result["excluded_companies"][0]["reason"] == "SELF_OR_MISSING_SYMBOL"


def test_peer_median_uses_same_sector_sample():
    peers = [
        {"symbol":"AAA","sector":"STEEL","pe":8},
        {"symbol":"BBB","sector":"STEEL","pe":10},
        {"symbol":"CCC","sector":"STEEL","pe":12},
        {"symbol":"DDD","sector":"STEEL","pe":100},
        {"symbol":"EEE","sector":"STEEL","pe":11},
    ]
    result = build_peer_multiples(
        peers, subject_symbol="HPG", sector="STEEL", min_peers=3
    )
    assert result["multiples"]["pe"]["status"] == "CALCULATED"
    assert result["multiples"]["pe"]["median"] == 10.5
    assert "DDD" in result["multiples"]["pe"]["outliers_excluded"]
