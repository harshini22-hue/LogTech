#!/usr/bin/env python
"""Simple CLI to run RCA using a short description and log file.

Usage:
  python run_query.py -d "description" [-l path/to/log.txt]
"""
import argparse
from rca import run_rca


def main():
    p = argparse.ArgumentParser(description="Run RCA and show Jira-informed result")
    p.add_argument("-d", "--description", help="Issue description", required=False)
    p.add_argument("-l", "--log", help="Path to log file", required=False)
    args = p.parse_args()

    desc = args.description
    if not desc:
        desc = input("Enter issue description: ")

    log_text = ""
    if args.log:
        with open(args.log, "r", encoding="utf-8", errors="ignore") as fh:
            log_text = fh.read()
    else:
        print("No log file provided — continuing with empty log text.")

    try:
        out = run_rca(desc, log_text)
        print("\n=== RCA Output ===\n")
        print(out)
    except Exception as e:
        print("Error running RCA:", e)


if __name__ == "__main__":
    main()
