import re
from collections import Counter
from typing import Dict, Any, List

TS_RE = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")


def analyze_log_text(log_text: str) -> Dict[str, Any]:
    """Return structured analysis from raw log text.

    Keys: timestamps (min,max), severity_counts, error_lines, top_errors,
    stack_traces, components
    """
    lines = [l.rstrip() for l in log_text.splitlines() if l.strip()]
    timestamps = []
    severity_counts = Counter()
    error_lines: List[str] = []
    components = Counter()

    # Collect stack traces blocks (simple heuristic: lines starting with whitespace
    # following a Traceback or 'Exception')
    stack_traces = []
    cur_trace = []
    in_trace = False

    for line in lines:
        m = TS_RE.search(line)
        if m:
            timestamps.append(m.group(1))

        upper = line.upper()
        if "ERROR" in upper:
            severity_counts["ERROR"] += 1
            error_lines.append(line)
        elif "WARN" in upper or "WARNING" in upper:
            severity_counts["WARN"] += 1
        elif "INFO" in upper:
            severity_counts["INFO"] += 1
        elif "DEBUG" in upper:
            severity_counts["DEBUG"] += 1

        # component heuristic: look for patterns like 'module.submodule' or '[module]'
        comp_m = re.search(r"\[([A-Za-z0-9_.-]+)\]", line)
        if comp_m:
            components[comp_m.group(1)] += 1
        else:
            comp2 = re.search(r"([A-Za-z0-9_]+)\.", line)
            if comp2:
                components[comp2.group(1)] += 1

        if line.startswith("Traceback") or line.startswith("Exception") or "Traceback (most recent call last)" in line:
            in_trace = True
            cur_trace = [line]
            continue

        if in_trace:
            if line.startswith(" ") or line.startswith("\t") or line.startswith("at "):
                cur_trace.append(line)
                continue
            else:
                # trace ended
                if cur_trace:
                    stack_traces.append("\n".join(cur_trace))
                cur_trace = []
                in_trace = False

    # Catch any trailing trace
    if cur_trace:
        stack_traces.append("\n".join(cur_trace))

    top_errors = [t for t, _ in Counter(error_lines).most_common(5)]

    time_range = None
    if timestamps:
        time_range = (min(timestamps), max(timestamps))

    return {
        "timestamps": time_range,
        "severity_counts": dict(severity_counts),
        "error_lines": error_lines,
        "top_errors": top_errors,
        "stack_traces": stack_traces,
        "components": components.most_common(5),
    }


def format_for_llm(analysis: Dict[str, Any]) -> str:
    """Create a concise plain-text summary suitable for LLM prompts."""
    parts: List[str] = []
    if analysis.get("timestamps"):
        parts.append(f"Time range: {analysis['timestamps'][0]} to {analysis['timestamps'][1]}")
    sc = analysis.get("severity_counts", {})
    if sc:
        parts.append("Severity counts: " + ", ".join(f"{k}={v}" for k, v in sc.items()))
    top = analysis.get("top_errors", [])
    if top:
        parts.append("Top error messages:")
        for t in top:
            parts.append(f"- {t[:200]}")
    comps = analysis.get("components", [])
    if comps:
        parts.append("Top components: " + ", ".join(f"{c[0]}({c[1]})" for c in comps))
    traces = analysis.get("stack_traces", [])
    if traces:
        parts.append("Sample stack trace: \n" + traces[0][:1000])

    return "\n".join(parts)
