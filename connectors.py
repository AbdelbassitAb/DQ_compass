"""
connectors.py

Data source connector abstraction, shared by the engine (dq_engine.py) and the
authoring web app (rule_authoring/).

A connector knows how to turn a small config dict into a pandas DataFrame. Each
one declares a typed field spec (FIELDS) that drives the "New data source" form.

Implemented in this prototype : CSV, Excel.
Preview-only (selector shown, no live connection) : JSON, SQL database,
SharePoint / Drive / URL. Their load() raises SourceUnavailable; they are saved
with status "planned" and skipped by the engine.

The registry key ("csv", "excel", ...) is stored as `type` in datasets_config.yaml.
"""
from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field as _dc_field
from pathlib import Path

import pandas as pd


def _openpyxl_available() -> bool:
    return importlib.util.find_spec("openpyxl") is not None


class SourceUnavailable(RuntimeError):
    """A data source cannot be loaded (missing, retired, or connector not implemented)."""


@dataclass
class Field:
    name: str
    label: str
    kind: str = "text"          # text | number | select | bool | secret | textarea
    required: bool = False
    default: str = ""
    options: list = _dc_field(default_factory=list)
    help: str = ""
    advanced: bool = False
    placeholder: str = ""


@dataclass
class ProbeResult:
    ok: bool
    error: str | None = None
    columns: list = _dc_field(default_factory=list)
    row_count: int | None = None
    sample: list = _dc_field(default_factory=list)   # list[dict]


@dataclass
class SourceIssue:
    level: str      # error | warning | info
    field: str
    code: str
    message: str


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _resolve(path: str, root: Path) -> Path:
    p = Path(path or "")
    return p if p.is_absolute() else (root / p)


def _unescape_delim(d: str) -> str:
    if d in ("\\t", "tab", "TAB", "\t"):
        return "\t"
    try:
        return d.encode().decode("unicode_escape")
    except Exception:
        return d


def _sample(df: pd.DataFrame, n: int = 5) -> list:
    return df.head(n).astype(str).to_dict("records")


# --------------------------------------------------------------------------
# Implemented connectors
# --------------------------------------------------------------------------
class CsvConnector:
    TYPE = "csv"
    LABEL = "CSV file"
    ICON = "CSV"
    IMPLEMENTED = True
    DESCRIPTION = "Delimited text file. You choose the delimiter, encoding and header row."
    FIELDS = [
        Field("path", "File path", "text", required=True,
              placeholder="sample_data/orders.csv",
              help="Relative to the project root, or an absolute path."),
        Field("delimiter", "Delimiter", "text", default=",",
              help="Exactly one character. Use \\t for a tab."),
        Field("header_row", "Header row", "number", default="1",
              help="1-based row number that holds the column names."),
        Field("encoding", "Encoding", "text", default="utf-8", advanced=True),
        Field("quotechar", "Quote character", "text", default='"', advanced=True),
        Field("skip_rows", "Rows to skip before the header", "number", default="0", advanced=True),
    ]

    def _read_kwargs(self, config: dict) -> dict:
        sep = _unescape_delim(str(config.get("delimiter") or ","))
        header_row = int(config.get("header_row") or 1) - 1
        skip = int(config.get("skip_rows") or 0)
        return dict(
            sep=sep,
            header=header_row if header_row >= 0 else 0,
            skiprows=range(0, skip) if skip else None,
            encoding=config.get("encoding") or "utf-8",
            quotechar=(str(config.get("quotechar") or '"')[:1] or '"'),
            engine="python",
        )

    def load(self, config: dict, root: Path) -> pd.DataFrame:
        path = _resolve(config.get("path", ""), root)
        if not path.exists():
            raise SourceUnavailable(f"CSV file not found: {path}")
        return pd.read_csv(path, **self._read_kwargs(config))

    def probe(self, config: dict, root: Path) -> ProbeResult:
        try:
            df = self.load(config, root)
        except SourceUnavailable as exc:
            return ProbeResult(False, str(exc))
        except Exception as exc:
            return ProbeResult(False, f"{type(exc).__name__}: {exc}")
        return ProbeResult(True, None, [str(c) for c in df.columns], len(df), _sample(df))

    def validate(self, config: dict) -> list:
        issues = []
        if not (config.get("path") or "").strip():
            issues.append(SourceIssue("error", "path", "required", "File path is required."))
        d = _unescape_delim(str(config.get("delimiter") or ","))
        if len(d) != 1:
            issues.append(SourceIssue("error", "delimiter", "bad_delimiter",
                                      "Delimiter must be exactly one character (use \\t for a tab)."))
        hr = config.get("header_row")
        if hr not in (None, "") and (not str(hr).isdigit() or int(hr) < 1):
            issues.append(SourceIssue("error", "header_row", "bad_row",
                                      "Header row must be an integer >= 1."))
        return issues


class ExcelConnector:
    TYPE = "excel"
    LABEL = "Excel file"
    ICON = "XLS"
    IMPLEMENTED = True
    DESCRIPTION = "Workbook (.xlsx / .xls). You choose the sheet and the header row."
    FIELDS = [
        Field("path", "File path", "text", required=True, placeholder="data/Q3_orders.xlsx",
              help="Relative to the project root, or an absolute path."),
        Field("sheet", "Sheet", "text", default="0",
              help="Sheet name, or 0 for the first sheet."),
        Field("header_row", "Header row", "number", default="1",
              help="1-based row number that holds the column names."),
        Field("skip_rows", "Extra rows to skip above the header", "number", default="0", advanced=True),
        Field("nrows", "Max rows to read", "number", default="", advanced=True),
    ]

    def _sheet(self, config: dict):
        s = str(config.get("sheet") or "0").strip()
        return int(s) if s.lstrip("-").isdigit() else s

    def load(self, config: dict, root: Path) -> pd.DataFrame:
        path = _resolve(config.get("path", ""), root)
        if not path.exists():
            raise SourceUnavailable(f"Excel file not found: {path}")
        if not _openpyxl_available():
            raise SourceUnavailable("openpyxl is not installed (pip install openpyxl).")
        header_row = int(config.get("header_row") or 1) - 1
        skip = int(config.get("skip_rows") or 0)
        nrows = str(config.get("nrows") or "").strip()
        return pd.read_excel(
            path, sheet_name=self._sheet(config),
            header=header_row if header_row >= 0 else 0,
            skiprows=range(0, skip) if skip else None,
            nrows=int(nrows) if nrows.isdigit() else None,
            engine="openpyxl",
        )

    def probe(self, config: dict, root: Path) -> ProbeResult:
        path = _resolve(config.get("path", ""), root)
        if not path.exists():
            return ProbeResult(False, f"Excel file not found: {path}")
        if not _openpyxl_available():
            return ProbeResult(False, "openpyxl is not installed (pip install openpyxl).")
        try:
            with pd.ExcelFile(path, engine="openpyxl") as xl:
                names = list(xl.sheet_names)
            s = self._sheet(config)
            if isinstance(s, str) and s not in names:
                return ProbeResult(False, f"Sheet '{s}' not found. Available: {', '.join(names)}.")
            if isinstance(s, int) and s >= len(names):
                return ProbeResult(False, f"Sheet index {s} out of range (workbook has {len(names)}).")
            df = self.load(config, root)
        except SourceUnavailable as exc:
            return ProbeResult(False, str(exc))
        except Exception as exc:
            return ProbeResult(False, f"{type(exc).__name__}: {exc}")
        return ProbeResult(True, None, [str(c) for c in df.columns], len(df), _sample(df))

    def validate(self, config: dict) -> list:
        issues = []
        if not (config.get("path") or "").strip():
            issues.append(SourceIssue("error", "path", "required", "File path is required."))
        hr = config.get("header_row")
        if hr not in (None, "") and (not str(hr).isdigit() or int(hr) < 1):
            issues.append(SourceIssue("error", "header_row", "bad_row",
                                      "Header row must be an integer >= 1."))
        return issues


# --------------------------------------------------------------------------
# Preview-only connectors (selector shown, no live connection)
# --------------------------------------------------------------------------
class _PlannedConnector:
    IMPLEMENTED = False

    def load(self, config: dict, root: Path) -> pd.DataFrame:
        raise SourceUnavailable(
            f"The {self.LABEL} connector is a preview and is not available in this prototype.")

    def probe(self, config: dict, root: Path) -> ProbeResult:
        return ProbeResult(False, f"{self.LABEL}: preview connector — no live connection in this prototype.")

    def validate(self, config: dict) -> list:
        return list(self._shape_issues(config or {}))

    def _shape_issues(self, config: dict):
        return iter(())


class JsonConnector(_PlannedConnector):
    TYPE = "json"
    LABEL = "JSON file"
    ICON = "{ }"
    DESCRIPTION = "JSON or JSON Lines file. Preview only — selector shown for the demo."
    FIELDS = [
        Field("path", "File path", "text", required=True, placeholder="data/orders.json"),
        Field("orient", "Orientation", "select", default="records",
              options=["records", "columns", "index", "table", "values"]),
        Field("lines", "JSON Lines (one object per line)", "bool", default=""),
        Field("record_path", "Record path (nested array)", "text", advanced=True,
              help="Dotted path to the array to flatten, e.g. data.orders"),
    ]

    def _shape_issues(self, config: dict):
        if not (config.get("path") or "").strip():
            yield SourceIssue("error", "path", "required", "File path is required.")


class SqlConnector(_PlannedConnector):
    TYPE = "sql"
    LABEL = "SQL database"
    ICON = "SQL"
    DESCRIPTION = "Relational database via SQLAlchemy. Preview only — selector shown for the demo."
    FIELDS = [
        Field("driver", "Driver", "select", default="postgresql",
              options=["postgresql", "mysql", "sqlite", "mssql", "oracle"]),
        Field("host", "Host", "text", required=True, placeholder="db.internal"),
        Field("port", "Port", "number", default="5432"),
        Field("database", "Database", "text", required=True),
        Field("schema", "Schema", "text", advanced=True),
        Field("username", "Username", "text"),
        Field("password", "Password", "secret"),
        Field("table", "Table", "text", help="Provide a table OR a query below."),
        Field("query", "Query", "textarea", help="SELECT ... — overrides the table when set."),
    ]

    def _shape_issues(self, config: dict):
        if not (config.get("host") or "").strip():
            yield SourceIssue("error", "host", "required", "Host is required.")
        if not (config.get("database") or "").strip():
            yield SourceIssue("error", "database", "required", "Database is required.")
        p = config.get("port")
        if p not in (None, "") and not str(p).isdigit():
            yield SourceIssue("error", "port", "bad_port", "Port must be numeric.")
        if not (config.get("table") or "").strip() and not (config.get("query") or "").strip():
            yield SourceIssue("warning", "table", "need_table_or_query",
                              "Provide a table or a query.")


class UrlConnector(_PlannedConnector):
    TYPE = "url"
    LABEL = "SharePoint / Drive / URL"
    ICON = "URL"
    DESCRIPTION = "Remote file via a share or direct-download link. Preview only — selector shown for the demo."
    FIELDS = [
        Field("url", "Link", "text", required=True, placeholder="https://.../orders.xlsx"),
        Field("auth", "Authentication", "select", default="none", options=["none", "token"]),
        Field("token", "Access token", "secret", advanced=True,
              help="Used only when authentication = token."),
        Field("format", "File format", "select", default="csv", options=["csv", "xlsx"]),
    ]

    def _shape_issues(self, config: dict):
        u = (config.get("url") or "").strip()
        if not u:
            yield SourceIssue("error", "url", "required", "Link is required.")
        elif not u.lower().startswith(("http://", "https://")):
            yield SourceIssue("error", "url", "bad_url", "Link must start with http:// or https://.")


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------
CONNECTOR_ORDER = ["csv", "excel", "json", "sql", "url"]
_REGISTRY = {c.TYPE: c() for c in (CsvConnector, ExcelConnector, JsonConnector, SqlConnector, UrlConnector)}

DEFAULT_CSV_CONFIG = {"delimiter": ",", "encoding": "utf-8", "header_row": 1}


def get_connector(type_: str):
    if not type_:
        return _REGISTRY["csv"]
    if type_ in _REGISTRY:
        return _REGISTRY[type_]
    raise SourceUnavailable(f"Unknown connector type: {type_}")


def describe_connectors() -> list:
    out = []
    for t in CONNECTOR_ORDER:
        c = _REGISTRY[t]
        out.append({
            "type": c.TYPE, "label": c.LABEL, "icon": c.ICON,
            "implemented": c.IMPLEMENTED, "description": c.DESCRIPTION,
            "fields": [vars(f) for f in c.FIELDS],
        })
    return out


def normalize_entry(entry) -> dict:
    """Accept both the legacy flat shape ({path, format}) and the rich shape."""
    if not isinstance(entry, dict):
        return {"type": "csv", "status": "active", "config": {}, "created_at": "", "updated_at": ""}
    if "config" in entry or "type" in entry:
        e = dict(entry)
        e.setdefault("type", entry.get("format", "csv"))
        e.setdefault("status", "active")
        e.setdefault("config", {})
        e.setdefault("created_at", "")
        e.setdefault("updated_at", "")
        return e
    cfg = {k: v for k, v in entry.items() if k != "format"}
    t = entry.get("format", "csv")
    if t == "csv":
        cfg = {**DEFAULT_CSV_CONFIG, **cfg}
    return {"type": t, "status": "active", "config": cfg, "created_at": "", "updated_at": ""}


def load_source(name: str, datasets_config: dict, root: Path) -> pd.DataFrame:
    if name not in (datasets_config or {}):
        raise SourceUnavailable(f"data source '{name}' is not declared in datasets_config.yaml")
    entry = normalize_entry(datasets_config[name])
    if entry.get("status") != "active":
        raise SourceUnavailable(f"data source '{name}' is {entry.get('status')}")
    return get_connector(entry["type"]).load(entry.get("config", {}), root)
