"""
Tests for the meta-catalogue validation layer (rule_authoring/schema.py).

    python -m pytest tests/            # with pytest
    python tests/test_schema.py        # without pytest (minimal built-in runner)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rule_authoring import schema  # noqa: E402

DSCFG = {"orders": {}, "customers": {}, "orders_reference": {}}
DSCOLS = {
    "orders": ["order_id", "customer_id", "order_date", "amount", "status", "region"],
    "customers": ["customer_id", "name", "email", "country"],
    "orders_reference": ["order_id", "amount"],
}


def base(**kw):
    r = {
        "rule_id": "DQ99",
        "control_name": "Test rule",
        "control_type": "Completeness",
        "description": "A description long enough to pass validation.",
        "dataset_scope": "orders",
        "ref_dataset_scope": "",
        "severity": "High",
        "frequency": "Daily",
        "owner": "Data Steward",
        "output_type": "Error dataset",
        "kpi": "% completeness",
        "remediation_action": "Contact the source owner.",
        "params": {"field": "amount"},
        "threshold_pct": None,
    }
    r.update(kw)
    return r


def val(rule, existing=None):
    return schema.validate_rule(rule, existing or [], DSCFG, DSCOLS)


def test_valid_completeness():
    assert val(base()).ok


def test_missing_description():
    assert not val(base(description="court")).ok


def test_unknown_dataset():
    rep = val(base(dataset_scope="ventes"))
    assert any(i.code == "unknown_dataset" for i in rep.errors)


def test_unknown_column():
    rep = val(base(params={"field": "montant"}))
    assert any(i.code == "unknown_column" for i in rep.errors)


def test_validity_needs_a_mode():
    rep = val(base(control_type="Validity", params={"field": "status"}))
    assert any(i.code == "validity_no_mode" for i in rep.errors)


def test_validity_allowed_values_ok():
    assert val(base(control_type="Validity",
                    params={"field": "status", "allowed_values": ["PENDING", "SHIPPED"]})).ok


def test_validity_two_modes_rejected():
    rep = val(base(control_type="Validity",
                   params={"field": "status", "allowed_values": ["A"], "regex": "^A$"}))
    assert any(i.code == "validity_many_modes" for i in rep.errors)


def test_bad_regex():
    rep = val(base(control_type="Validity", params={"field": "status", "regex": "([A-Z"}))
    assert any(i.code == "bad_regex" for i in rep.errors)


def test_uniqueness_unknown_key():
    rep = val(base(control_type="Uniqueness", params={"keys": ["order_ref"]}))
    assert any(i.code == "unknown_column" for i in rep.errors)


def test_consistency_requires_ref_dataset():
    rep = val(base(control_type="Consistency",
                   params={"field": "customer_id", "ref_field": "customer_id"}))
    assert any(i.field == "ref_dataset_scope" for i in rep.errors)


def test_consistency_ok():
    assert val(base(control_type="Consistency", ref_dataset_scope="customers",
                    params={"field": "customer_id", "ref_field": "customer_id"})).ok


def test_timeliness_bad_lag():
    rep = val(base(control_type="Timeliness",
                   params={"field": "order_date", "max_lag_days": 0, "reference_date": "today"}))
    assert any(i.code == "non_positive" for i in rep.errors)


def test_reconciliation_ok():
    assert val(base(control_type="Reconciliation", ref_dataset_scope="orders_reference",
                    params={"key": "order_id", "field": "amount", "ref_field": "amount",
                            "tolerance_pct": 0.5})).ok


def test_reconciliation_tolerance_out_of_range():
    rep = val(base(control_type="Reconciliation", ref_dataset_scope="orders_reference",
                   params={"key": "order_id", "field": "amount", "ref_field": "amount",
                           "tolerance_pct": 250}))
    assert any(i.code == "out_of_range" for i in rep.errors)


def test_duplicate_rule_id():
    rep = val(base(), existing=[base(rule_id="DQ99")])
    assert any(i.code == "duplicate" for i in rep.errors)


def test_bad_rule_id_format():
    rep = val(base(rule_id="9-bad id"))
    assert any(i.code == "format" for i in rep.errors)


def test_high_severity_low_freq_is_a_warning():
    rep = val(base(frequency="Monthly"))
    assert rep.ok
    assert any(i.code == "critical_low_freq" for i in rep.warnings)


def test_loose_threshold_on_critical_warns():
    rep = val(base(threshold_pct=20))
    assert rep.ok
    assert any(i.code == "loose_critical" for i in rep.warnings)


def test_no_threshold_is_info_not_error():
    rep = val(base(threshold_pct=None))
    assert rep.ok
    assert any(i.code == "no_threshold" for i in rep.infos)


def test_duplicate_control_logic_warns():
    existing = [base(rule_id="DQ01")]
    rep = val(base(rule_id="DQ02"), existing=existing)
    assert rep.ok
    assert any(i.code == "duplicate_control" for i in rep.warnings)


def test_derivations():
    logic = schema.derive_logic_definition("Completeness", {"field": "amount"}, "orders", "")
    assert "amount IS NULL" in logic
    assert schema.derive_data_element("Uniqueness", {"keys": ["a", "b"]}) == "a, b"
    plain = schema.explain_plain_language("Consistency", {"field": "customer_id"},
                                          "orders", "customers")
    assert "orders" in plain and "customers" in plain


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {fn.__name__}: {exc}")
    print(f"\n{len(fns) - failed}/{len(fns)} tests OK")
    sys.exit(1 if failed else 0)
