"""
rule_authoring/charts.py

Dependency-free inline-SVG / HTML chart builders for the Reporting page.
Colours use CSS custom properties so the charts follow the light/dark theme.
Each function returns a markup string to be rendered with |safe in Jinja.
"""
from __future__ import annotations


def score_bar(value: float, delta=None) -> str:
    value = max(0.0, min(100.0, float(value)))
    band = "var(--ok)" if value >= 90 else ("var(--warn)" if value >= 70 else "var(--bad)")
    d = ""
    if delta is not None and delta != 0:
        up = delta > 0
        d = (f'<span class="kpi-delta {"up" if up else "down"}">'
             f'{"&#9650;" if up else "&#9660;"} {abs(delta):g} vs previous run</span>')
    elif delta == 0:
        d = '<span class="kpi-delta flat">no change vs previous run</span>'
    return f'''<div class="score-wrap">
      <div class="score-head"><span class="score-num" style="color:{band}">{value:g}</span>
        <span class="score-cap">/ 100 &nbsp; DQ score</span>{d}</div>
      <div class="score-track">
        <div class="score-fill" style="width:{value:.1f}%;background:{band}"></div>
        <span class="score-tick" style="left:70%"></span>
        <span class="score-tick" style="left:90%"></span>
      </div>
      <div class="score-scale"><span>0</span><span style="left:70%">70</span>
        <span style="left:90%">90</span><span style="right:0">100</span></div>
    </div>'''


def trend_chart(series: list) -> str:
    """DQ-score line over runs (primary), with a thin pass/fail composition strip
    under each run. series oldest->newest: [{label, ts, pass, fail, error, score}]."""
    if not series:
        return '<div class="muted small">No run history yet &mdash; run the engine a few times.</div>'
    n = len(series)
    W, H = max(340, n * 46), 168
    pl, pr, pt, pb = 28, 8, 12, 34          # plot padding
    ph = H - pt - pb                        # plot height (score area)
    pw = W - pl - pr
    xs = [pl + (pw * i / (n - 1) if n > 1 else pw / 2) for i in range(n)]

    # y-axis auto-floored so movement is visible when scores cluster high
    lo = max(0, min(float(s["score"]) for s in series) - 8)
    lo = 0 if lo < 12 else round(lo / 5) * 5
    span = (100 - lo) or 1

    def sy(v):  # score -> y
        return pt + ph * (1 - (float(v) - lo) / span)

    gridvals = sorted({lo, (lo + 100) // 2 // 5 * 5, 100})
    grid = "".join(
        f'<line x1="{pl}" y1="{sy(v):.1f}" x2="{W - pr}" y2="{sy(v):.1f}" '
        f'stroke="var(--border)" stroke-width="0.6"/>'
        f'<text x="{pl - 5}" y="{sy(v) + 3:.1f}" text-anchor="end" class="c-axis">{v}</text>'
        for v in gridvals)

    strips = []
    for i, s in enumerate(series):
        tot = (s["pass"] + s["fail"] + s["error"]) or 1
        sw = min(26, pw / n - 6)
        strip_y = pt + ph + 6
        x = xs[i] - sw / 2
        for val, col in ((s["pass"], "var(--ok)"), (s["fail"], "var(--bad)"), (s["error"], "var(--grey)")):
            wseg = sw * val / tot
            if wseg > 0.4:
                strips.append(f'<rect x="{x:.1f}" y="{strip_y:.1f}" width="{wseg:.1f}" height="5" '
                              f'fill="{col}" rx="1"/>')
            x += wseg
        strips.append(f'<text x="{xs[i]:.1f}" y="{H - 6}" text-anchor="middle" '
                      f'class="c-axis">{s["label"]}</text>')

    pts = [(xs[i], sy(s["score"])) for i, s in enumerate(series)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = ""
    if n > 1:
        area = (f'<polygon points="{pl},{pt + ph} {poly} {W - pr},{pt + ph}" '
                f'fill="var(--accent)" opacity="0.08"/>')
    line = f'<polyline points="{poly}" fill="none" stroke="var(--accent)" stroke-width="2"/>'
    dots = "".join(
        f'<g><title>{s["ts"]}  &bull;  {s["pass"]}P / {s["fail"]}F / {s["error"]}E  '
        f'&bull;  score {s["score"]}</title>'
        f'<circle cx="{pts[i][0]:.1f}" cy="{pts[i][1]:.1f}" r="3" fill="var(--surface)" '
        f'stroke="var(--accent)" stroke-width="1.8"/></g>'
        for i, s in enumerate(series))
    return (f'<svg viewBox="0 0 {W:.0f} {H}" class="chart-svg" preserveAspectRatio="xMinYMid meet">'
            f'{grid}{area}{line}{dots}{"".join(strips)}</svg>')


def donut(p: int, f: int, e: int) -> str:
    total = (p + f + e) or 1
    gp, rp, ep = 100 * p / total, 100 * f / total, 100 * e / total
    off_r = 25 - gp
    off_e = 25 - gp - rp
    return f'''<svg viewBox="0 0 42 42" class="donut-svg">
      <circle cx="21" cy="21" r="15.9" fill="none" stroke="var(--surface-3)" stroke-width="5.5"/>
      <circle cx="21" cy="21" r="15.9" fill="none" stroke="var(--ok)" stroke-width="5.5"
              stroke-dasharray="{gp:.1f} {100 - gp:.1f}" stroke-dashoffset="25"/>
      <circle cx="21" cy="21" r="15.9" fill="none" stroke="var(--bad)" stroke-width="5.5"
              stroke-dasharray="{rp:.1f} {100 - rp:.1f}" stroke-dashoffset="{off_r:.1f}"/>
      <circle cx="21" cy="21" r="15.9" fill="none" stroke="var(--grey)" stroke-width="5.5"
              stroke-dasharray="{ep:.1f} {100 - ep:.1f}" stroke-dashoffset="{off_e:.1f}"/>
      <text x="21" y="23.5" text-anchor="middle" class="donut-num">{p + f + e}</text>
    </svg>'''


def hbars(items: list, label_key: str, val_key: str, tone: str = "bad", unit: str = "") -> str:
    items = [i for i in items if i.get(val_key)]
    if not items:
        return '<div class="muted small">Nothing to show &mdash; no exceptions in this run.</div>'
    mx = max(i[val_key] for i in items) or 1
    rows = []
    for i in items:
        w = 100 * i[val_key] / mx
        rows.append(
            f'<div class="hb-row"><div class="hb-label" title="{i[label_key]}">{i[label_key]}</div>'
            f'<div class="hb-track"><div class="hb-fill hb-{tone}" style="width:{w:.0f}%"></div></div>'
            f'<div class="hb-val">{i[val_key]}{unit}</div></div>')
    return "".join(rows)


def sparkline(vals: list) -> str:
    vals = [float(v) for v in vals]
    if len(vals) < 2:
        return ""
    mn, mx = min(vals), max(vals)
    rng = (mx - mn) or 1
    pts = " ".join(f"{i / (len(vals) - 1) * 60:.1f},{16 - (v - mn) / rng * 13:.1f}"
                   for i, v in enumerate(vals))
    return (f'<svg viewBox="0 0 60 16" class="spark"><polyline points="{pts}" fill="none" '
            f'stroke="var(--text-subtle)" stroke-width="1.6"/></svg>')


def mini_bar(hits: int, total: int, tone: str = "bad") -> str:
    total = total or 1
    w = 100 * hits / total
    return (f'<span class="mini-bar"><span class="mini-fill mini-{tone}" '
            f'style="width:{w:.0f}%"></span></span>')
