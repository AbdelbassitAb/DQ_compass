"""
controls.py

Library of generic DQ controls.

Key principle of the brief (Separation of Concerns): each function knows
NOTHING about a specific dataset. It receives a DataFrame + parameters and
returns a standardised result. The same "check_completeness" serves any
field, of any dataset, indefinitely.

Each control returns a standardised dict:
{
    "status": "PASS" | "FAIL",
    "metrics": {...},          # quantifiable KPIs
    "exceptions": pd.DataFrame # failing records (empty if PASS)
}
"""
from __future__ import annotations
import re
import pandas as pd


def check_completeness(df: pd.DataFrame, field: str) -> dict:
    is_null = df[field].isna() | (df[field].astype(str).str.strip() == "")
    exceptions = df[is_null]
    total = len(df)
    completeness_rate = round(100 * (total - len(exceptions)) / total, 2) if total else 100.0
    return {
        "status": "PASS" if exceptions.empty else "FAIL",
        "metrics": {"total_records": total, "null_count": int(len(exceptions)),
                    "completeness_pct": completeness_rate},
        "exceptions": exceptions,
    }


def check_validity(df: pd.DataFrame, field: str, allowed_values: list | None = None,
                    regex: str | None = None, min_val=None, max_val=None) -> dict:
    series = df[field]
    if allowed_values is not None:
        mask_invalid = ~series.isin(allowed_values)
    elif regex is not None:
        pattern = re.compile(regex)
        # fullmatch: the WHOLE value must conform to the format, not just a prefix
        # (re.match anchors only at the start, so "FR123" would pass "[A-Z]{2}").
        mask_invalid = ~series.astype(str).apply(lambda v: pattern.fullmatch(v) is not None)
    elif min_val is not None or max_val is not None:
        lo = min_val if min_val is not None else float("-inf")
        hi = max_val if max_val is not None else float("inf")
        mask_invalid = ~series.between(lo, hi)
    else:
        raise ValueError("check_validity requires allowed_values, regex, or min/max_val")
    exceptions = df[mask_invalid]
    total = len(df)
    valid_rate = round(100 * (total - len(exceptions)) / total, 2) if total else 100.0
    return {
        "status": "PASS" if exceptions.empty else "FAIL",
        "metrics": {"total_records": total, "invalid_count": int(len(exceptions)),
                    "valid_pct": valid_rate},
        "exceptions": exceptions,
    }


def check_uniqueness(df: pd.DataFrame, keys: list) -> dict:
    dup_mask = df.duplicated(subset=keys, keep=False)
    exceptions = df[dup_mask].sort_values(by=keys)
    total = len(df)
    dup_rate = round(100 * len(exceptions) / total, 2) if total else 0.0
    return {
        "status": "PASS" if exceptions.empty else "FAIL",
        "metrics": {"total_records": total, "duplicate_count": int(len(exceptions)),
                    "duplicate_pct": dup_rate},
        "exceptions": exceptions,
    }


def check_consistency(df: pd.DataFrame, field: str, ref_df: pd.DataFrame, ref_field: str) -> dict:
    valid_values = set(ref_df[ref_field].dropna().unique())
    mask_orphan = ~df[field].isin(valid_values)
    exceptions = df[mask_orphan]
    total = len(df)
    orphan_rate = round(100 * len(exceptions) / total, 2) if total else 0.0
    return {
        "status": "PASS" if exceptions.empty else "FAIL",
        "metrics": {"total_records": total, "orphan_count": int(len(exceptions)),
                    "orphan_pct": orphan_rate},
        "exceptions": exceptions,
    }


def check_timeliness(df: pd.DataFrame, field: str, max_lag_days: int,
                      reference_date: str = "today") -> dict:
    ref = pd.Timestamp.today().normalize() if reference_date == "today" else pd.Timestamp(reference_date)
    dates = pd.to_datetime(df[field])
    lag_days = (ref - dates).dt.days
    mask_stale = lag_days > max_lag_days
    exceptions = df[mask_stale].copy()
    exceptions["lag_days"] = lag_days[mask_stale]
    total = len(df)
    within_sla = round(100 * (total - len(exceptions)) / total, 2) if total else 100.0
    return {
        "status": "PASS" if exceptions.empty else "FAIL",
        "metrics": {"total_records": total, "sla_breach_count": int(len(exceptions)),
                    "within_sla_pct": within_sla},
        "exceptions": exceptions,
    }


def check_reconciliation(df: pd.DataFrame, key: str, field: str,
                          ref_df: pd.DataFrame, ref_field: str, tolerance_pct: float) -> dict:
    left = df[[key, field]].rename(columns={field: "_source_value"})
    right = ref_df[[key, ref_field]].rename(columns={ref_field: "_target_value"})
    merged = left.merge(right, on=key, how="outer", indicator=True)
    merged["delta"] = (merged["_source_value"] - merged["_target_value"]).abs()
    merged["delta_pct"] = (merged["delta"] / merged["_target_value"].replace(0, pd.NA)) * 100
    mask_break = (merged["_merge"] != "both") | (merged["delta_pct"] > tolerance_pct)
    exceptions = merged[mask_break.fillna(True)]
    total = len(merged)
    reconciled_rate = round(100 * (total - len(exceptions)) / total, 2) if total else 100.0
    return {
        "status": "PASS" if exceptions.empty else "FAIL",
        "metrics": {"total_records": total, "break_count": int(len(exceptions)),
                    "reconciled_pct": reconciled_rate},
        "exceptions": exceptions,
    }


# Registry: control_type (catalogue) -> generic function.
# This is the ONLY place where code is added to support a new control TYPE.
# Adding a dataset or a rule never touches this file.
CONTROL_REGISTRY = {
    "Completeness": check_completeness,
    "Validity": check_validity,
    "Uniqueness": check_uniqueness,
    "Consistency": check_consistency,
    "Timeliness": check_timeliness,
    "Reconciliation": check_reconciliation,
}
