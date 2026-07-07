def safe_float(val, default=0.0) -> float:
    """
    Safely converts a value to float. Returns default if conversion fails or val is None.
    """
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def evaluate_split_model_candidate(baseline: dict, candidate: dict) -> dict[str, object]:
    """
    Compares baseline and candidate split model metrics to determine if the candidate is eligible for promotion.
    
    Metrics evaluated:
    - excess_return_net (must improve, i.e., candidate > baseline)
    - max_drawdown_net (must not worsen, i.e., candidate >= baseline)
    - roc_auc (must not worsen, i.e., candidate >= baseline)
    - precision_at_top_10pct (must not worsen, i.e., candidate >= baseline)
    """
    if baseline is None:
        baseline = {}
    if candidate is None:
        candidate = {}

    # Define metrics and their check rules
    # Tuple format: (metric_name, comparator, is_strict_improvement, default_val_if_missing)
    metric_rules = [
        ("excess_return_net", ">", True, 0.0),
        ("max_drawdown_net", ">=", False, -1.0),
        ("roc_auc", ">=", False, 0.0),
        ("precision_at_top_10pct", ">=", False, 0.0),
    ]

    checks = []
    all_passed = True

    for metric, comparator, strict_improvement, default_val in metric_rules:
        baseline_val = safe_float(baseline.get(metric), default_val)
        candidate_val = safe_float(candidate.get(metric), default_val)

        if strict_improvement:
            passed = candidate_val > baseline_val
        else:
            passed = candidate_val >= baseline_val

        if not passed:
            all_passed = False

        checks.append({
            "metric": metric,
            "passed": passed,
            "baseline": baseline_val,
            "candidate": candidate_val,
            "comparator": comparator
        })

    return {
        "passed": all_passed,
        "checks": checks
    }
