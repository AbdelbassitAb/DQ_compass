"""
Tests for the data source connectors and their validation.

    python -m pytest tests/
    python tests/test_connectors.py
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from connectors import (SourceUnavailable, get_connector,  # noqa: E402
                        load_source, normalize_entry)
from rule_authoring import source_schema  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _tmp(suffix):
    fd, name = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return Path(name)


def test_csv_default_comma():
    conn = get_connector("csv")
    df = conn.load({"path": "sample_data/orders.csv"}, ROOT)
    assert list(df.columns)[0] == "order_id"
    assert len(df) == 11


def test_csv_semicolon_delimiter():
    p = _tmp(".csv")
    p.write_text("a;b;c\n1;2;3\n4;5;6\n", encoding="utf-8")
    try:
        df = get_connector("csv").load({"path": str(p), "delimiter": ";"}, ROOT)
        assert list(df.columns) == ["a", "b", "c"]
        assert len(df) == 2
    finally:
        p.unlink()


def test_csv_header_row_offset():
    p = _tmp(".csv")
    p.write_text("junk line\ntitle,x\nid,value\n1,10\n2,20\n", encoding="utf-8")
    try:
        df = get_connector("csv").load({"path": str(p), "header_row": 3}, ROOT)
        assert list(df.columns) == ["id", "value"]
        assert len(df) == 2
    finally:
        p.unlink()


def test_csv_probe_and_validate():
    conn = get_connector("csv")
    pr = conn.probe({"path": "sample_data/orders.csv"}, ROOT)
    assert pr.ok and "amount" in pr.columns and pr.row_count == 11
    bad = conn.validate({"path": "x.csv", "delimiter": "||"})
    assert any(i.code == "bad_delimiter" for i in bad)
    missing = conn.probe({"path": "sample_data/does_not_exist.csv"}, ROOT)
    assert not missing.ok


def test_excel_roundtrip():
    p = _tmp(".xlsx")
    pd.DataFrame({"id": [1, 2], "amount": [10.0, 20.0]}).to_excel(p, index=False, sheet_name="Data")
    try:
        conn = get_connector("excel")
        df = conn.load({"path": str(p), "sheet": "Data"}, ROOT)
        assert list(df.columns) == ["id", "amount"] and len(df) == 2
        pr = conn.probe({"path": str(p), "sheet": "Data"}, ROOT)
        assert pr.ok and pr.row_count == 2
        bad = conn.probe({"path": str(p), "sheet": "Missing"}, ROOT)
        assert not bad.ok and "not found" in bad.error.lower()
    finally:
        try:
            p.unlink()
        except OSError:
            pass


def test_planned_connectors_raise_and_probe_fail():
    for t in ("json", "sql", "url"):
        conn = get_connector(t)
        assert conn.IMPLEMENTED is False
        try:
            conn.load({}, ROOT)
            assert False, "expected SourceUnavailable"
        except SourceUnavailable:
            pass
        assert conn.probe({}, ROOT).ok is False


def test_sql_shape_validation():
    issues = get_connector("sql").validate({"host": "", "database": "", "port": "abc"})
    codes = {i.code for i in issues}
    assert "required" in codes and "bad_port" in codes


def test_url_scheme_validation():
    issues = get_connector("url").validate({"url": "ftp://x/y.csv"})
    assert any(i.code == "bad_url" for i in issues)


def test_normalize_entry_flat_and_rich():
    flat = normalize_entry({"path": "a.csv", "format": "csv"})
    assert flat["type"] == "csv" and flat["config"]["path"] == "a.csv" and flat["status"] == "active"
    rich = normalize_entry({"type": "excel", "status": "retired", "config": {"path": "b.xlsx"}})
    assert rich["type"] == "excel" and rich["status"] == "retired"


def test_load_source_missing_and_retired():
    cfg = {"orders": {"type": "csv", "status": "retired", "config": {"path": "sample_data/orders.csv"}}}
    try:
        load_source("orders", cfg, ROOT)
        assert False
    except SourceUnavailable as exc:
        assert "retired" in str(exc)
    try:
        load_source("ghost", cfg, ROOT)
        assert False
    except SourceUnavailable:
        pass


def test_source_schema_validation():
    names = ["orders"]
    r = source_schema.validate_source("orders", "csv", {"path": "x.csv"}, names)
    assert any(i.code == "duplicate" for i in r.errors)
    r2 = source_schema.validate_source("new_src", "csv",
                                       {"path": "sample_data/orders.csv"}, [])
    assert r2.ok
    r3 = source_schema.validate_source("bad name!", "csv", {"path": "x"}, [])
    assert any(i.code == "format" for i in r3.errors)


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
