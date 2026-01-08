from jira import search_jira, build_jira_context
import logging

logging.basicConfig(level=logging.INFO)

issues = search_jira()
print("Fetched:", len(issues))

ctx = build_jira_context(issues)
for c in ctx:
    print(c["key"], "-", c["title"])
