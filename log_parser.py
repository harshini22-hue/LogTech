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


def parse_log_file(log_path, output_json):
    entries = []
    pending_header = None

    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()

            # match header line
            header_match = HEADER_PATTERN.search(line)
            if header_match:
                pending_header = header_match.groupdict()
                continue

            # match detail line
            if pending_header:
                detail_match = DETAIL_PATTERN.match(line)
                if detail_match:
                    d = detail_match.groupdict()

                    entries.append({
                        "level": pending_header["level"],
                        "timestamp": pending_header["timestamp"],
                        "component": d["component"],
                        "pid": int(d["pid"]),
                        "source_file": d["file"],
                        "line": int(d["line"]),
                        "message": d["message"].strip()
                    })

                pending_header = None

    output = {
        "metadata": {
            "source_file": Path(log_path).name,
            "parsed_at": datetime.utcnow().isoformat(),
            "total_entries": len(entries)
        },
        "entries": entries
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Parsed {len(entries)} log entries → {output_json}")


if __name__ == "__main__":
    parse_log_file("sip_call.txt", "parsed.json")
