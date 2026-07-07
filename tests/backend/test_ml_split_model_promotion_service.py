from backend.services.ml_split_model_promotion_service import evaluate_split_model_candidate

def test_promotion_passed_when_better_or_equal():
    # Scenario 1: Candidate shows better returns, improved MDD, improved AUC, and better precision
    baseline = {
        "excess_return_net": 0.05,
        "max_drawdown_net": -0.15,
        "roc_auc": 0.60,
        "precision_at_top_10pct": 0.12
    }
    candidate = {
        "excess_return_net": 0.08,
        "max_drawdown_net": -0.12,
        "roc_auc": 0.62,
        "precision_at_top_10pct": 0.15
    }
    
    result = evaluate_split_model_candidate(baseline, candidate)
    
    assert result["passed"] is True
    assert len(result["checks"]) == 4
    for check in result["checks"]:
        assert check["passed"] is True

    # Scenario 2: Candidate has equal risk and metrics, but improved return (which is the only > requirement)
    candidate_equal_risk = {
        "excess_return_net": 0.06,  # improved
        "max_drawdown_net": -0.15,   # equal
        "roc_auc": 0.60,             # equal
        "precision_at_top_10pct": 0.12  # equal
    }
    result_equal = evaluate_split_model_candidate(baseline, candidate_equal_risk)
    assert result_equal["passed"] is True
    for check in result_equal["checks"]:
        assert check["passed"] is True


def test_promotion_failed_when_metrics_worsened():
    baseline = {
        "excess_return_net": 0.05,
        "max_drawdown_net": -0.15,
        "roc_auc": 0.60,
        "precision_at_top_10pct": 0.12
    }

    # Scenario 1: Max drawdown worsened (more negative)
    candidate_bad_mdd = {
        "excess_return_net": 0.08,
        "max_drawdown_net": -0.18,  # worsened
        "roc_auc": 0.62,
        "precision_at_top_10pct": 0.15
    }
    result = evaluate_split_model_candidate(baseline, candidate_bad_mdd)
    assert result["passed"] is False
    mdd_check = next(c for c in result["checks"] if c["metric"] == "max_drawdown_net")
    assert mdd_check["passed"] is False

    # Scenario 2: Excess return did not improve (equal to baseline)
    candidate_equal_return = {
        "excess_return_net": 0.05,  # must be strictly improved (> baseline)
        "max_drawdown_net": -0.12,
        "roc_auc": 0.62,
        "precision_at_top_10pct": 0.15
    }
    result = evaluate_split_model_candidate(baseline, candidate_equal_return)
    assert result["passed"] is False
    return_check = next(c for c in result["checks"] if c["metric"] == "excess_return_net")
    assert return_check["passed"] is False

    # Scenario 3: ROC AUC worsened
    candidate_bad_auc = {
        "excess_return_net": 0.08,
        "max_drawdown_net": -0.12,
        "roc_auc": 0.58,  # worsened
        "precision_at_top_10pct": 0.15
    }
    result = evaluate_split_model_candidate(baseline, candidate_bad_auc)
    assert result["passed"] is False
    auc_check = next(c for c in result["checks"] if c["metric"] == "roc_auc")
    assert auc_check["passed"] is False

    # Scenario 4: Precision worsened
    candidate_bad_precision = {
        "excess_return_net": 0.08,
        "max_drawdown_net": -0.12,
        "roc_auc": 0.62,
        "precision_at_top_10pct": 0.10  # worsened
    }
    result = evaluate_split_model_candidate(baseline, candidate_bad_precision)
    assert result["passed"] is False
    precision_check = next(c for c in result["checks"] if c["metric"] == "precision_at_top_10pct")
    assert precision_check["passed"] is False
