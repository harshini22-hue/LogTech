import json
import re
from datetime import datetime
from pathlib import Path


HEADER_PATTERN = re.compile(
    r"""
    (?P<level>INFO|LOG|WARNING|ERROR|FATAL|TRACE|DEBUG)
    .*?
    (?P<timestamp>(Sun|Mon|Tue|Wed|Thu|Fri|Sat)\s+.*?\d{4}\.\d+)
    """,
    re.VERBOSE
)

DETAIL_PATTERN = re.compile(
    r"""
    (?P<component>[A-Za-z0-9_]+)
    \((?P<pid>\d+)\):
    \s+(?P<file>\S+):(?P<line>\d+)
    \s+(?P<message>.*)
    """,
    re.VERBOSE
)


def parse_log_file(log_path, output_json=None, return_json=False):
    entries = []
    pending_header = None

    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()

            header_match = HEADER_PATTERN.search(line)
            if header_match:
                pending_header = header_match.groupdict()
                continue

            if pending_header:
                detail_match = DETAIL_PATTERN.match(line)
                if detail_match:
                    d = detail_match.groupdict()
                    entries.append({
                        "level": pending_header["level"],
                        "timestamp": pending_header["timestamp"],
                        "component": d["component"],
                        "pid": int(d["pid"]), # id ex - (889)
                        "source_file": d["file"],
                        "line": int(d["line"]),
                        "message": d["message"].strip()
                    })
                pending_header = None
def parse_multiple_logs(uploaded_files):
    combined_entries = []

    for uploaded_file in uploaded_files:
        temp_path = f"temp_{uploaded_file.name}"

        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        parsed = parse_log_file(temp_path)

        if parsed and "entries" in parsed:
            combined_entries.extend(parsed["entries"])

    return {
        "metadata": {
            "source_files": [f.name for f in uploaded_files],
            "total_entries": len(combined_entries)
        },
        "entries": combined_entries
    }
    output = {
        "metadata": {
            "source_file": Path(log_path).name,
            "parsed_at": datetime.utcnow().isoformat(),
            "total_entries": len(entries)
        },
        "entries": entries
    }

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

    return output
