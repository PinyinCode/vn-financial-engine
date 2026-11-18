"""Transparent sector-aware scorecards; missing metrics reduce coverage, not score."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ScoreResult:
    score: float
    max_score: float
    coverage: float
    components: dict[str, dict]
    status: str

def _higher(v, bands):
    if v is None: return None
    for threshold, points in bands:
        if v >= threshold: return points
    return 0.0

def _lower(v, bands):
    if v is None: return None
    for ceiling, points in bands:
        if v <= ceiling: return points
    return 0.0

def _score(items):
    components, earned, possible = {}, 0.0, 0.0
    for name, weight, value, points in items:
        if points is None:
            components[name] = {"score": None, "max": weight, "value": value, "status": "MISSING"}
        else:
            earned += points * weight
            possible += weight
            components[name] = {"score": round(points * weight, 2), "max": weight,
                                "value": value, "status": "AVAILABLE"}
    coverage = possible / 50
    score = earned / possible * 50 if possible else 0
    return ScoreResult(round(score, 2), 50, round(coverage, 3), components,
                       "COMPLETE" if coverage >= .9 else "PARTIAL")

def score_fundamentals(m, sector):
    """50-point financial score. Inputs are ratios in decimal form, not percentages."""
    sector = sector.upper()
    if sector == "BANK":
        specs = [
          ("roe",12,m.get("roe"),_higher(m.get("roe"),[(.20,1),(.15,.8),(.10,.6),(.05,.3)])),
          ("profit_growth",8,m.get("profit_growth_yoy"),_higher(m.get("profit_growth_yoy"),[(.25,1),(.15,.8),(.05,.6),(0,.3)])),
          ("npl_quality",8,m.get("npl_ratio"),_lower(m.get("npl_ratio"),[(.01,1),(.02,.8),(.03,.6),(.05,.3)])),
          ("loan_loss_coverage",6,m.get("loan_loss_coverage"),_higher(m.get("loan_loss_coverage"),[(1.5,1),(1.2,.8),(1,.6),(.7,.3)])),
          ("capital_adequacy",10,m.get("capital_adequacy"),_higher(m.get("capital_adequacy"),[(.15,1),(.12,.8),(.10,.6),(.08,.3)])),
          ("cost_to_income",6,m.get("cost_to_income"),_lower(m.get("cost_to_income"),[(.30,1),(.40,.8),(.50,.6),(.60,.3)])),
        ]
    elif sector == "SECURITIES":
        specs = [
          ("roe",10,m.get("roe"),_higher(m.get("roe"),[(.20,1),(.15,.8),(.10,.6),(.05,.3)])),
          ("profit_growth",8,m.get("profit_growth_yoy"),_higher(m.get("profit_growth_yoy"),[(.30,1),(.20,.8),(.10,.6),(0,.3)])),
          ("capital_to_assets",10,m.get("capital_to_assets"),_higher(m.get("capital_to_assets"),[(.50,1),(.35,.8),(.25,.6),(.15,.3)])),
          ("margin_lending_risk",10,m.get("margin_lending_to_equity"),_lower(m.get("margin_lending_to_equity"),[(1,1),(1.5,.8),(2,.5),(2.5,.2)])),
          ("operating_margin",12,m.get("operating_margin"),_higher(m.get("operating_margin"),[(.35,1),(.25,.8),(.15,.6),(.05,.3)])),
        ]
    else:
        specs = [
          ("roe",12,m.get("roe"),_higher(m.get("roe"),[(.20,1),(.15,.8),(.10,.6),(.05,.3)])),
          ("profit_growth",10,m.get("profit_growth_yoy"),_higher(m.get("profit_growth_yoy"),[(.25,1),(.15,.8),(.05,.6),(0,.3)])),
          ("cash_conversion",10,m.get("cfo_to_net_income"),_higher(m.get("cfo_to_net_income"),[(1,1),(.8,.8),(.5,.6),(0,.3)])),
          ("leverage",10,m.get("debt_to_equity"),_lower(m.get("debt_to_equity"),[(.5,1),(1,.8),(1.5,.6),(2.5,.3)])),
          ("operating_margin",8,m.get("operating_margin"),_higher(m.get("operating_margin"),[(.20,1),(.15,.8),(.08,.6),(.03,.3)])),
        ]
    return _score(specs)

def score_valuation(current_multiple, peer_multiple):
    if current_multiple is None or peer_multiple is None or current_multiple <= 0 or peer_multiple <= 0:
        return ScoreResult(0,30,0,{"relative_multiple":{"score":None,"max":30,"status":"MISSING"}},"INSUFFICIENT_DATA")
    relative=current_multiple/peer_multiple
    points=30 if relative<=.70 else 26 if relative<=.85 else 22 if relative<=1 else 16 if relative<=1.15 else 9 if relative<=1.35 else 3
    return ScoreResult(points,30,1,{"relative_multiple":{"score":points,"max":30,"relative":round(relative,4),"status":"AVAILABLE"}},"COMPLETE")

def combine_score(fundamental, valuation, technical_score_100):
    tech=None if technical_score_100 is None else max(0,min(100,technical_score_100))*.2
    parts={"fundamental":{"score":fundamental.score,"max":50,"coverage":fundamental.coverage},
           "valuation":{"score":valuation.score,"max":30,"coverage":valuation.coverage},
           "technical":{"score":tech,"max":20,"status":"MISSING" if tech is None else "AVAILABLE"}}
    total=fundamental.score+valuation.score+(tech or 0)
    coverage=(fundamental.coverage*50+valuation.coverage*30+(20 if tech is not None else 0))/100
    return ScoreResult(round(total,2),100,round(coverage,3),parts,"COMPLETE" if coverage>=.9 else "PARTIAL")
