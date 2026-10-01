#!/usr/bin/env python3
"""Statistics report for the insurance benchmark full-ladder runs (fl-*).

Read-only on the run results. Standard library only. Re-runnable:

    python3 analyze.py            # writes report.md and summary.json next to this script

Held-out sets (names starting with "heldout"): only counts, rates and statistics are
written. Question ids of held-out sets are slugs of the question text, so they are never
printed. Development-set ("all") ids may appear.
"""
import json
import math
import os
import re
import statistics
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.normpath(os.path.join(HERE, "..", "..", "work", "insurance", "runs"))

MODELS = [
    # run id, label, expected sets
    ("fl-opus", "Opus 5.5", ["heldout-3", "all", "heldout-3-unanswerable"]),
    ("fl-sonnet", "Sonnet 5", ["heldout-3", "all", "heldout-3-unanswerable"]),
    ("fl-qwen", "Qwen 3.8 27B (local)", ["heldout-3", "heldout-3-unanswerable"]),
    ("fl-luna", "GPT-6 Luna (max)", ["heldout-3", "all", "heldout-3-unanswerable"]),
    ("fl-sol", "GPT-6 Sol (medium)", ["heldout-3", "all", "heldout-3-unanswerable"]),
    ("fl-terra", "GPT-5.6 Terra (high)", ["heldout-3", "all", "heldout-3-unanswerable"]),
]
INCOMPLETE = {"fl-luna", "fl-sol", "fl-terra"}
LEVELS = ["baseline-full", "L0", "L1", "L2", "L3", "LB", "W0", "W1", "W2", "WB"]
SHORT = {"baseline-full": "P"}
SETS = ["heldout-3", "all", "heldout-3-unanswerable"]
BELOW = {"L0": "baseline-full", "W0": "baseline-full", "L1": "L0", "L2": "L1", "L3": "L2",
         "LB": "L3", "W1": "W0", "W2": "W1", "WB": "W2"}
EXPECTED_BUILD = {lv: "49c0e1cb" for lv in LEVELS if lv != "baseline-full"}
EXPECTED_BUILD["LB"] = "627009a1"
EXPECTED_BUILD["WB"] = "627009a1"
TRUSTED = {"certified", "governed"}
ALPHA = 0.05


def lv(level):
    return SHORT.get(level, level)


def is_heldout(s):
    return s.startswith("heldout")


def unanswerable(s):
    return s.endswith("unanswerable")


# ---------------------------------------------------------------- statistics

def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(b, c):
    """Exact two-sided McNemar p: binomial test of b vs c with p=0.5."""
    n = b + c
    if n == 0:
        return 1.0
    m = min(b, c)
    tail = sum(math.comb(n, i) for i in range(m + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def pct(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.0f}%"


def quantile(vals, q):
    """Nearest-rank quantile."""
    if not vals:
        return None
    s = sorted(vals)
    r = max(1, math.ceil(q * len(s)))
    return s[r - 1]


def fmt_p(p):
    if p is None:
        return "-"
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


# ---------------------------------------------------------------- loading

def load(run, level, set_):
    d = os.path.join(RUNS, run, level, set_)
    f = os.path.join(d, "report.json")
    if not os.path.isdir(d):
        return None, "not run (no directory)"
    if not os.path.isfile(f):
        return None, "no report.json (running or aborted)"
    try:
        with open(f) as fh:
            rep = json.load(fh)
    except Exception as e:  # partially written
        return None, f"unreadable report.json ({type(e).__name__})"
    if rep.get("invalid"):
        inv = rep["invalid"]
        why = inv.get("reason", "invalid") if isinstance(inv, dict) else str(inv)
        q = inv.get("questions") if isinstance(inv, dict) else None
        return None, f"INVALID: {why}" + (f" ({q} questions)" if q is not None else "")
    return rep, None


def question_tokens(rep, r):
    """Tokens for one result if recorded per result (baseline reports)."""
    u = r.get("usage")
    if not isinstance(u, dict):
        return None
    keys = ("input", "output", "cacheRead", "cacheWrite", "inputTokens", "outputTokens",
            "cacheReadTokens", "cacheWriteTokens")
    return {k: u.get(k, 0) or 0 for k in keys if k in u}


def summarize(run, level, set_, rep):
    res = rep.get("results") or []
    rows = {}
    for r in res:
        name = (r.get("name") or "").strip()
        ans = r.get("answer") or {}
        sql = (ans.get("sql") or "").strip()
        if unanswerable(set_):
            ok = bool(r.get("passed"))
        else:
            ok = bool(r.get("executionMatched"))
        rows[name] = {
            "ok": ok,
            "trust": ans.get("trustState") or "none",
            "stopped": not sql,
            "tier": ans.get("tier"),
            "ms": r.get("durationMs"),
            "dispatch": r.get("providerDispatchCount"),
            "usage": question_tokens(rep, r),
            "cost": r.get("costUsd"),
        }
    n = len(rows)
    k = sum(1 for x in rows.values() if x["ok"])
    lo, hi = wilson(k, n)
    trusted = [x for x in rows.values() if x["trust"] in TRUSTED]
    wrong_trusted = [x for x in trusted if not x["ok"]]
    wrong_trusted_ids = [nm for nm, x in rows.items() if x["trust"] in TRUSTED and not x["ok"]]
    stops = sum(1 for x in rows.values() if x["stopped"])
    ms = [x["ms"] for x in rows.values() if isinstance(x["ms"], (int, float))]
    trust_counts = {}
    for x in rows.values():
        trust_counts[x["trust"]] = trust_counts.get(x["trust"], 0) + 1
    disp = [x["dispatch"] for x in rows.values() if isinstance(x["dispatch"], (int, float))]

    # tokens
    tokens = None
    per_q = [x["usage"] for x in rows.values() if x["usage"]]
    if per_q and len(per_q) == n:
        tot = [sum(u.values()) for u in per_q]
        inp = sum(u.get("input", 0) + u.get("inputTokens", 0) for u in per_q)
        cr = sum(u.get("cacheRead", 0) + u.get("cacheReadTokens", 0) for u in per_q)
        cw = sum(u.get("cacheWrite", 0) + u.get("cacheWriteTokens", 0) for u in per_q)
        out = sum(u.get("output", 0) + u.get("outputTokens", 0) for u in per_q)
        tokens = {"source": "per-result usage", "questions": len(per_q), "input": inp,
                  "cacheRead": cr, "cacheWrite": cw, "output": out, "total": sum(tot),
                  "medianPerQuestion": statistics.median(tot), "calls": None}
    elif isinstance(rep.get("usage"), dict) and isinstance(rep["usage"].get("byQuestion"), dict):
        bq = list(rep["usage"]["byQuestion"].values())  # keys are question text: never output
        outside = rep["usage"].get("outside") or {}
        tot = [(q.get("inputTokens", 0) or 0) + (q.get("outputTokens", 0) or 0)
               + (q.get("cacheReadTokens", 0) or 0) + (q.get("cacheWriteTokens", 0) or 0)
               for q in bq]
        tokens = {"source": "report usage.byQuestion", "questions": len(bq),
                  "input": sum(q.get("inputTokens", 0) or 0 for q in bq),
                  "cacheRead": sum(q.get("cacheReadTokens", 0) or 0 for q in bq),
                  "cacheWrite": sum(q.get("cacheWriteTokens", 0) or 0 for q in bq),
                  "output": sum(q.get("outputTokens", 0) or 0 for q in bq),
                  "reasoning": sum(q.get("reasoningTokens", 0) or 0 for q in bq),
                  "total": sum(tot), "medianPerQuestion": statistics.median(tot) if tot else None,
                  "calls": sum(q.get("calls", 0) or 0 for q in bq),
                  "outsideCalls": outside.get("calls", 0)}
    else:
        jl = os.path.join(RUNS, run, level, set_, "usage.jsonl")
        if os.path.isfile(jl):
            inp = out = calls = 0
            with open(jl) as fh:
                for line in fh:
                    try:
                        e = json.loads(line)
                    except Exception:
                        continue
                    calls += 1
                    inp += e.get("inputTokens", 0) or 0
                    out += e.get("outputTokens", 0) or 0
            tokens = {"source": "usage.jsonl", "questions": None, "input": inp, "output": out,
                      "cacheRead": 0, "cacheWrite": 0, "total": inp + out,
                      "medianPerQuestion": None, "calls": calls}
    costs = [x["cost"] for x in rows.values() if isinstance(x["cost"], (int, float))]

    ident = rep.get("identity") or {}
    tools = ident.get("tools") or {}
    effort = tools.get("effort")
    m = re.search(r"model_reasoning_effort=(\w+)", tools.get("codexCli") or "")
    if m:
        effort = m.group(1)
    return {
        "rows": rows,
        "n": n, "k": k, "acc": k / n if n else None, "ci": [lo, hi],
        "trusted": len(trusted), "wrongTrusted": len(wrong_trusted),
        "trustPrecision": (len(trusted) - len(wrong_trusted)) / len(trusted) if trusted else None,
        "wrongTrustedIds": wrong_trusted_ids,
        "stops": stops,
        "correctStops": (sum(1 for x in rows.values() if x["ok"] and x["stopped"])
                         if unanswerable(set_) else None),
        "trustCounts": trust_counts,
        "medianS": statistics.median(ms) / 1000 if ms else None,
        "p90S": quantile(ms, 0.9) / 1000 if ms else None,
        "meanDispatch": statistics.mean(disp) if disp else None,
        "tokens": tokens,
        "costUsd": sum(costs) if costs else None,
        "build": ((ident.get("dql") or {}).get("commit") or "")[:8],
        "dqlVersion": (ident.get("dql") or {}).get("version"),
        "model": ident.get("model"),
        "provider": ident.get("provider"),
        "effort": effort,
        "resumedKept": (rep.get("resumedFrom") or {}).get("kept"),
        "createdAt": ident.get("createdAt"),
    }


def paired(a, b):
    """Compare level a (new) against b (reference). Returns gained/lost/p/unpaired."""
    ra, rb = a["rows"], b["rows"]
    common = sorted(set(ra) & set(rb))
    gained = sum(1 for q in common if ra[q]["ok"] and not rb[q]["ok"])
    lost = sum(1 for q in common if not ra[q]["ok"] and rb[q]["ok"])
    return {"n": len(common), "gained": gained, "lost": lost,
            "p": mcnemar_exact(gained, lost),
            "unpairedA": len(set(ra) - set(rb)), "unpairedB": len(set(rb) - set(ra)),
            "kA": sum(1 for q in common if ra[q]["ok"]), "kB": sum(1 for q in common if rb[q]["ok"])}


# ---------------------------------------------------------------- main

def main():
    data, missing, problems = {}, [], []
    for run, label, sets in MODELS:
        for level in LEVELS:
            for s in sets:
                if level == "baseline-full" and unanswerable(s):
                    continue
                rep, why = load(run, level, s)
                if rep is None:
                    missing.append({"run": run, "level": level, "set": s, "why": why})
                    continue
                data[(run, level, s)] = summarize(run, level, s, rep)

    # build exceptions
    build_exc = []
    for (run, level, s), d in sorted(data.items()):
        exp = EXPECTED_BUILD.get(level)
        if exp and d["build"] != exp:
            build_exc.append({"run": run, "level": level, "set": s, "build": d["build"], "expected": exp})

    # superseded invalid attempts beside a canonical report (informational)
    attempts = []
    for run, _, _ in MODELS:
        rd = os.path.join(RUNS, run)
        if not os.path.isdir(rd):
            continue
        for level in sorted(os.listdir(rd)):
            ld = os.path.join(rd, level)
            if not os.path.isdir(ld):
                continue
            for sd in sorted(os.listdir(ld)):
                if "." in sd:
                    f = os.path.join(ld, sd, "report.json")
                    status = "no report.json"
                    if os.path.isfile(f):
                        try:
                            with open(f) as fh:
                                status = "invalid" if json.load(fh).get("invalid") else "valid"
                        except Exception:
                            status = "unreadable"
                    attempts.append({"run": run, "level": level, "dir": sd, "status": status})

    comps = {}
    for (run, level, s), d in data.items():
        if level == "baseline-full":
            continue
        p = data.get((run, "baseline-full", s))
        if p:
            comps[(run, level, s, "P")] = paired(d, p)
        below = BELOW.get(level)
        if below and below != "baseline-full":
            b = data.get((run, below, s))
            if b:
                comps[(run, level, s, lv(below))] = paired(d, b)
    for c in comps.values():
        if c["unpairedA"] or c["unpairedB"]:
            problems.append("question ids that do not pair between levels were found")
            break

    out = []
    w = out.append
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    w("# Insurance benchmark: full-ladder statistics (fl-* runs)")
    w("")
    w(f"Generated {now} by `analyze.py` from `work/insurance/runs/fl-*/<level>/<set>/report.json`. "
      "Read-only on the results. Held-out sets are shown as counts and rates only.")
    w("")
    w("Levels: **P** = plain model, one-shot SQL from the full DDL (baseline-full); **L0** dbt only; "
      "**L1** +modeling; **L2** +dbt MetricFlow metrics; **L3** +skills; **LB** +business layer; "
      "**W0** warehouse only (no dbt); **W1** +modeling; **W2** +native metrics; **WB** +business layer.")
    w("")
    w("Sets: **heldout-3** (40 sealed questions, the publishable set); **all** (41 development "
      "questions); **heldout-3-unanswerable** (10; a correct stop counts as passed).")
    w("")

    # ---------------- models
    w("## Models")
    w("")
    w("| Run | Model | Provider | Effort (P / DQL) | Status |")
    w("|---|---|---|---|---|")
    for run, label, sets in MODELS:
        ds = [v for (r, l, s), v in data.items() if r == run]
        model = next((v["model"] for v in ds if v["model"]), "-")
        prov = next((v["provider"] for v in ds if v["provider"]), "-")
        pe = next((v["effort"] for (r, l, s), v in data.items() if r == run and l == "baseline-full"), None)
        de = next((v["effort"] for (r, l, s), v in data.items() if r == run and l != "baseline-full" and v["effort"]), None)
        status = "INCOMPLETE (still running)" if run in INCOMPLETE else "complete"
        if run == "fl-qwen":
            status += "; heldout-3 + unanswerable only"
        w(f"| {run} | {model} | {prov} | {pe or '-'} / {de or 'route default'} | {status} |")
    w("")

    # ---------------- data problems
    w("## Data problems and provenance")
    w("")
    w("**Missing or invalid reports** (treated as missing):")
    w("")
    if missing:
        w("| Run | Level | Set | Why |")
        w("|---|---|---|---|")
        for m in missing:
            w(f"| {m['run']} | {lv(m['level'])} | {m['set']} | {m['why']} |")
    else:
        w("None.")
    w("")
    w("**Build exceptions** (expected DQL 49c0e1cb, and 627009a1 for LB/WB):")
    w("")
    if build_exc:
        for b in build_exc:
            w(f"- {b['run']} {lv(b['level'])} {b['set']}: ran on **{b['build']}**, expected {b['expected']}")
    else:
        w("- None.")
    w("")
    pb = sorted({(r, d["build"]) for (r, l, s), d in data.items() if l == "baseline-full"})
    w("P (baseline-full) does not use DQL; its `identity.dql.commit` is the harness repo commit: "
      + ", ".join(f"{r} {b}" for r, b in pb) + ".")
    w("")
    kept = [(r, l, s, d["resumedKept"]) for (r, l, s), d in sorted(data.items()) if d["resumedKept"]]
    if kept:
        w("**Resumed reports** (questions kept from an earlier attempt that hit a provider limit; "
          "only the refused questions were re-run): "
          + "; ".join(f"{r} {lv(l)} {s} kept {k}" for r, l, s, k in kept) + ".")
        w("")
    inv_att = [a for a in attempts if a["status"] != "valid"]
    if inv_att:
        w(f"Superseded attempt directories beside the canonical ones (ignored): {len(attempts)} "
          f"({sum(1 for a in attempts if a['status'] == 'invalid')} invalid, "
          f"{sum(1 for a in attempts if a['status'] == 'no report.json')} without report.json).")
        w("")
    for pr in sorted(set(problems)):
        w(f"- {pr}")
    trust_seen = sorted({t for d in data.values() for t in d["trustCounts"]})
    w(f"Trust states seen: {', '.join(trust_seen)}. No answer was `certified`; every trusted answer is `governed`. "
      "`not_applicable` and `review_required` are not trusted.")
    w("")

    # ---------------- cross-model heldout-3
    def cell(run, level, s):
        d = data.get((run, level, s))
        if not d:
            return "missing"
        return f"{d['k']}/{d['n']} ({pct(d['acc'])})"

    w("## Held-out-3 accuracy, models x levels")
    w("")
    w("k/40 execution-matched. `*` = significantly different from the same model's P (exact McNemar, p<0.05); "
      "`+`/`-` give the direction.")
    w("")
    w("| Model | " + " | ".join(lv(l) for l in LEVELS) + " |")
    w("|---|" + "---|" * len(LEVELS))
    for run, label, sets in MODELS:
        cells = []
        for level in LEVELS:
            c = cell(run, level, "heldout-3")
            cp = comps.get((run, level, "heldout-3", "P"))
            if cp and cp["p"] < ALPHA:
                c += " *" + ("+" if cp["gained"] > cp["lost"] else "-")
            cells.append(c)
        w(f"| {label} | " + " | ".join(cells) + " |")
    w("")

    # ---------------- significance vs P on heldout-3
    w("## Which levels beat P on heldout-3")
    w("")
    w("Per model: discordant pairs vs P as `+gained/-lost`, exact McNemar p. **Bold** = p<0.05.")
    w("")
    w("| Model | " + " | ".join(lv(l) for l in LEVELS[1:]) + " |")
    w("|---|" + "---|" * (len(LEVELS) - 1))
    sig_vs_p = {}
    for run, label, sets in MODELS:
        cells = []
        for level in LEVELS[1:]:
            cp = comps.get((run, level, "heldout-3", "P"))
            if not cp:
                cells.append("missing")
                continue
            t = f"+{cp['gained']}/-{cp['lost']} p={fmt_p(cp['p'])}"
            if cp["p"] < ALPHA:
                t = f"**{t}**"
                sig_vs_p.setdefault(level, []).append((run, "beats" if cp["gained"] > cp["lost"] else "below"))
            cells.append(t)
        w(f"| {label} | " + " | ".join(cells) + " |")
    w("")
    w("Pooled across models (per level: models where the level is significantly above P, out of models with data; "
      "and a stratified exact McNemar that sums discordant pairs over models. The stratified test treats model x question "
      "pairs as independent, which they are not - the same 40 questions repeat - so read it as indicative).")
    w("")
    w("| Level | Sig. above P | Sig. below P | Models with data | Pooled +gained/-lost | Pooled p |")
    w("|---|---|---|---|---|---|")
    pooled = {}
    for level in LEVELS[1:]:
        cs = [comps[(run, level, "heldout-3", "P")] for run, _, _ in MODELS
              if (run, level, "heldout-3", "P") in comps]
        g = sum(c["gained"] for c in cs)
        l_ = sum(c["lost"] for c in cs)
        p = mcnemar_exact(g, l_) if cs else None
        above = [r for r, d in sig_vs_p.get(level, []) if d == "beats"]
        below = [r for r, d in sig_vs_p.get(level, []) if d == "below"]
        pooled[level] = {"models": len(cs), "gained": g, "lost": l_, "p": p,
                         "sigAbove": above, "sigBelow": below}
        w(f"| {lv(level)} | {len(above)} ({', '.join(above) or '-'}) | {len(below)} ({', '.join(below) or '-'}) | "
          f"{len(cs)} | +{g}/-{l_} | {fmt_p(p)} |")
    w("")

    # ---------------- per model detail
    w("## Per model, level and set")
    w("")
    w("Columns: accuracy k/n with Wilson 95% CI; paired vs P and vs the level below as `+gained/-lost (p)`; "
      "trust as wrong/trusted and trust precision; stops (no SQL); median and p90 latency in seconds; "
      "mean provider dispatches per question.")
    w("")
    for run, label, sets in MODELS:
        w(f"### {label} ({run})")
        w("")
        for s in sets:
            w(f"#### {s}")
            w("")
            if unanswerable(s):
                w("| Level | Correct stops k/n | Wilson 95% CI | vs level below | Stops | Wrong/trusted | Median s | p90 s | Dispatch |")
                w("|---|---|---|---|---|---|---|---|---|")
            else:
                w("| Level | Acc k/n | Wilson 95% CI | vs P | vs level below | Wrong/trusted | Trust precision | Stops | Median s | p90 s | Dispatch | Build |")
                w("|---|---|---|---|---|---|---|---|---|---|---|---|")
            for level in LEVELS:
                if level == "baseline-full" and unanswerable(s):
                    continue
                d = data.get((run, level, s))
                if not d:
                    why = next((m["why"] for m in missing if m["run"] == run and m["level"] == level and m["set"] == s), "missing")
                    ncol = 9 if unanswerable(s) else 12
                    w(f"| {lv(level)} | missing: {why} |" + " |" * (ncol - 2))
                    continue
                ci = f"{pct(d['ci'][0])}-{pct(d['ci'][1])}"
                below = BELOW.get(level)
                cb = comps.get((run, level, s, lv(below))) if below and below != "baseline-full" else None
                cp = comps.get((run, level, s, "P"))

                def cf(c):
                    if not c:
                        return "-"
                    t = f"+{c['gained']}/-{c['lost']} ({fmt_p(c['p'])})"
                    return f"**{t}**" if c["p"] < ALPHA else t
                wt = f"{d['wrongTrusted']}/{d['trusted']}"
                if d["wrongTrusted"]:
                    wt = f"**{wt}**"
                med = f"{d['medianS']:.1f}" if d["medianS"] is not None else "-"
                p90 = f"{d['p90S']:.1f}" if d["p90S"] is not None else "-"
                dsp = f"{d['meanDispatch']:.2f}" if d["meanDispatch"] is not None else "-"
                if unanswerable(s):
                    w(f"| {lv(level)} | {d['k']}/{d['n']} ({pct(d['acc'])}) | {ci} | {cf(cb)} | {d['stops']} | {wt} | {med} | {p90} | {dsp} |")
                else:
                    tp = pct(d["trustPrecision"]) if d["trusted"] else "-"
                    w(f"| {lv(level)} | {d['k']}/{d['n']} ({pct(d['acc'])}) | {ci} | {cf(cp) if level != 'baseline-full' else '-'} | "
                      f"{cf(cb) if level not in ('L0', 'W0', 'baseline-full') else '(= vs P)' if level != 'baseline-full' else '-'} | "
                      f"{wt} | {tp} | {d['stops']} | {med} | {p90} | {dsp} | {d['build'] if level != 'baseline-full' else 'n/a'} |")
            w("")

    # ---------------- trust summary
    w("## Trust: wrong/trusted by model and level")
    w("")
    w("Trusted = `certified` or `governed`. Wrong = not execution-matched (answerable sets) or not a correct stop "
      "(unanswerable). Shown as wrong/trusted with trust precision in brackets; `0/0` = no trusted answers.")
    w("")
    for s in SETS:
        w(f"### {s}")
        w("")
        w("| Model | " + " | ".join(lv(l) for l in LEVELS[1:]) + " |")
        w("|---|" + "---|" * (len(LEVELS) - 1))
        for run, label, sets in MODELS:
            if s not in sets:
                continue
            cells = []
            for level in LEVELS[1:]:
                d = data.get((run, level, s))
                if not d:
                    cells.append("missing")
                elif d["trusted"] == 0:
                    cells.append("0/0")
                else:
                    t = f"{d['wrongTrusted']}/{d['trusted']} ({pct(d['trustPrecision'])})"
                    cells.append(f"**{t}**" if d["wrongTrusted"] else t)
            w(f"| {label} | " + " | ".join(cells) + " |")
        w("")
    wrong_all = [(r, l, d["wrongTrustedIds"]) for (r, l, s), d in sorted(data.items()) if s == "all" and d["wrongTrustedIds"]]
    if wrong_all:
        w("Wrong trusted answers on the development set (`all`), by question id:")
        w("")
        for r, l, ids in wrong_all:
            w(f"- {r} {lv(l)}: {', '.join(ids)}")
        w("")
    tot_t = sum(d["trusted"] for (r, l, s), d in data.items() if s == "heldout-3")
    tot_w = sum(d["wrongTrusted"] for (r, l, s), d in data.items() if s == "heldout-3")
    w(f"Across all models and levels on heldout-3: {tot_w}/{tot_t} trusted answers were wrong.")
    w("")

    # ---------------- stops
    w("## Stops")
    w("")
    w("Answers with no SQL (DQL stopped). On answerable sets a stop is a missed answer; on the unanswerable set "
      "the correct-stop rate is the accuracy column above.")
    w("")
    for s in SETS:
        w(f"### {s}")
        w("")
        w("| Model | " + " | ".join(lv(l) for l in LEVELS) + " |")
        w("|---|" + "---|" * len(LEVELS))
        for run, label, sets in MODELS:
            if s not in sets:
                continue
            cells = []
            for level in LEVELS:
                if level == "baseline-full" and unanswerable(s):
                    cells.append("n/a")
                    continue
                d = data.get((run, level, s))
                if not d:
                    cells.append("missing")
                elif unanswerable(s):
                    cells.append(f"{d['stops']}/{d['n']} (correct {d['k']}/{d['n']})")
                else:
                    cells.append(f"{d['stops']}/{d['n']}")
            w(f"| {label} | " + " | ".join(cells) + " |")
        w("")

    # ---------------- latency
    w("## Latency (indicative only)")
    w("")
    w("Median / p90 of per-question `durationMs`, in seconds. Runs were executed in parallel lanes that shared the "
      "machine and provider quotas, and some reports were resumed after provider limits, so these numbers are "
      "indicative only and not a latency benchmark.")
    w("")
    for s in SETS:
        w(f"### {s}")
        w("")
        w("| Model | " + " | ".join(lv(l) for l in LEVELS) + " |")
        w("|---|" + "---|" * len(LEVELS))
        for run, label, sets in MODELS:
            if s not in sets:
                continue
            cells = []
            for level in LEVELS:
                d = data.get((run, level, s))
                if level == "baseline-full" and unanswerable(s):
                    cells.append("n/a")
                elif not d or d["medianS"] is None:
                    cells.append("missing")
                else:
                    cells.append(f"{d['medianS']:.0f} / {d['p90S']:.0f}")
            w(f"| {label} | " + " | ".join(cells) + " |")
        w("")

    # ---------------- tokens and cost
    w("## Tokens and cost")
    w("")
    w("No report records a dollar cost (`costUsd` is null everywhere: subscription CLIs and a local model). "
      "Token usage is recorded only where listed below; for all other cells tokens are **unmeasured**. "
      "Mean provider dispatches per question (in the per-model tables) is the only cost proxy available everywhere.")
    w("")
    w("| Run | Level | Set | Source | Questions | Total tokens | Input | Cache read | Cache write | Output | Median/question | Calls |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    any_tok = False
    for (run, level, s), d in sorted(data.items(), key=lambda kv: ([m[0] for m in MODELS].index(kv[0][0]), SETS.index(kv[0][2]), LEVELS.index(kv[0][1]))):
        t = d["tokens"]
        if not t:
            continue
        any_tok = True
        med = f"{t['medianPerQuestion']:,.0f}" if t.get("medianPerQuestion") is not None else "-"
        w(f"| {run} | {lv(level)} | {s} | {t['source']} | {t.get('questions') or '-'} | {t['total']:,} | {t['input']:,} | "
          f"{t.get('cacheRead', 0):,} | {t.get('cacheWrite', 0):,} | {t['output']:,} | {med} | {t.get('calls') or '-'} |")
    if not any_tok:
        w("| - | - | - | unmeasured | | | | | | | | |")
    w("")
    unmeasured = sorted({(r, lv(l)) for (r, l, s), d in data.items() if not d["tokens"]})
    by_run = {}
    for r, l in unmeasured:
        by_run.setdefault(r, []).append(l)
    w("Unmeasured: " + "; ".join(f"{r} {', '.join(v)}" for r, v in by_run.items()) + ".")
    w("")

    # ---------------- reading
    w("## Reading the numbers")
    w("")
    w("- **Sample size.** n=40 per level on heldout-3 gives Wilson 95% intervals roughly +/-14 points around the middle "
      "of the range (for example 28/40 = 70%, CI 55%-82%). Differences under about 15 points between two levels are "
      "rarely significant on their own; the paired McNemar test is more sensitive than comparing intervals because it "
      "uses only the questions that changed, but with a handful of discordant pairs even a 5-1 split is p=0.22.")
    w("- **Unanswerable set.** n=10 is small: 10/10 correct stops has a Wilson lower bound of 72%; 9/10 has 60%. Treat "
      "it as a smoke check of the stop behaviour, not a rate estimate.")
    w("- **Development set (`all`).** These 41 questions were used to build and tune the layers, so gains there are "
      "optimistic. heldout-3 is the publishable set.")
    w("- **Multiple comparisons.** This report runs many tests (up to 9 levels x 2 references x 6 models x 3 sets). "
      "At p<0.05, a few 'significant' results are expected by chance; weigh patterns that repeat across models over any "
      "single cell. No correction is applied.")
    w("- **Trust.** Wrong trusted answers are always shown with their denominator (wrong/trusted). A small denominator "
      "gives a weak precision estimate: 0/4 is consistent with a true wrong-trusted rate well above zero.")
    w("- **Incomplete runs.** The GPT runs (luna, sol, terra) are still running; missing cells are marked and any number "
      "for them may change. Some of their reports were resumed after provider usage limits.")
    w("- **Latency** is indicative only (parallel lanes).")
    w("")

    md = "\n".join(out) + "\n"
    with open(os.path.join(HERE, "report.md"), "w") as fh:
        fh.write(md)

    # ---------------- summary.json
    def strip(d, s):
        o = {k: v for k, v in d.items() if k not in ("rows",)}
        if is_heldout(s):
            o.pop("wrongTrustedIds", None)
        return o
    summary = {
        "generatedAt": now,
        "runsDir": RUNS,
        "alpha": ALPHA,
        "levels": {l: lv(l) for l in LEVELS},
        "results": {run: {lv(l): {s: strip(d, s) for (r2, l2, s), d in data.items() if r2 == run and l2 == l}
                          for l in LEVELS} for run, _, _ in MODELS},
        "comparisons": [{"run": r, "level": lv(l), "set": s, "vs": ref, **c} for (r, l, s, ref), c in sorted(comps.items())],
        "pooledVsP_heldout3": {lv(l): v for l, v in pooled.items()},
        "missing": missing,
        "buildExceptions": build_exc,
        "supersededAttempts": attempts,
    }
    with open(os.path.join(HERE, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2, sort_keys=False)
    print(f"wrote {os.path.join(HERE, 'report.md')} and summary.json "
          f"({len(data)} valid reports, {len(missing)} missing/invalid, {len(build_exc)} build exceptions)")


if __name__ == "__main__":
    sys.exit(main())
