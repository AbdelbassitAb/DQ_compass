"""
Control-function tests: the generic checks in controls.py.

    python -m pytest tests/
    python tests/test_controls.py
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controls import check_validity  # noqa: E402


def test_validity_allowed_values_flags_unknown():
    df = pd.DataFrame({"region": ["FR", "BE", "DE", "XX", "FR"]})
    out = check_validity(df, field="region", allowed_values=["FR", "BE", "DE"])
    assert out["status"] == "FAIL"
    assert out["exceptions"]["region"].tolist() == ["XX"]
    assert out["metrics"]["invalid_count"] == 1


def test_validity_regex_is_a_full_match_not_a_prefix():
    # "FR123" and "fraud" share a valid 2-letter prefix but are NOT valid codes.
    df = pd.DataFrame({"code": ["FR", "BE", "FR123", "fraud", "DE"]})
    out = check_validity(df, field="code", regex="[A-Z]{2}")
    assert out["status"] == "FAIL"
    assert sorted(out["exceptions"]["code"].tolist()) == ["FR123", "fraud"]


def test_validity_regex_pass_when_all_conform():
    df = pd.DataFrame({"code": ["FR", "BE", "DE"]})
    out = check_validity(df, field="code", regex="[A-Z]{2}")
    assert out["status"] == "PASS"
    assert out["exceptions"].empty


def test_validity_range_flags_out_of_bounds():
    df = pd.DataFrame({"qty": [1, 5, 10, 0, 42]})
    out = check_validity(df, field="qty", min_val=1, max_val=10)
    assert out["status"] == "FAIL"
    assert sorted(out["exceptions"]["qty"].tolist()) == [0, 42]


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
