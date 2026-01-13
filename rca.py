import re
from typing import List

from jira import search_jira, build_jira_context
from llm import run_llm
from jira import extract_text_from_adf

# Matching utilities

STOPWORDS = {
    "the", "is", "when", "from", "on", "in", "to", "and",
    "a", "of", "for", "with", "as", "by", "an", "at"
}

def normalize(text: str) -> set:
    if not text:
        return set()
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 3}

def match_score(user_desc: str, jira_text: str) -> float:
    """
    Simple but very effective keyword overlap score.
    """
    u = normalize(user_desc)
    j = normalize(jira_text)
    if not u or not j:
        return 0.0
    return len(u & j) / len(u)
 
# Jira issue selection 

def find_matching_jira_issues(
    jira_issues: List[dict],
    user_description: str,
    threshold: float = 0.15,
    top_n: int = 100
) -> List[dict]:
    """
    Select Jira issues that actually match the user description.
    """
    scored = []

    for issue in jira_issues:
        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        description = extract_text_from_adf(fields.get("description"))

        combined_text = f"{summary} {description}"
        score = match_score(user_description, combined_text)

        if score >= threshold:
            scored.append((issue, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    # print("Top Jira match scores:")
    # for i, s in scored[:5]:
    #     print(i["key"], s, i["fields"]["summary"])

    return [i[0] for i in scored[:top_n]]

# for log analysis --> llm

def build_llm_log_context(parsed_logs: dict, max_events: int = 150):
    if not parsed_logs or not isinstance(parsed_logs, dict):
        return []

    important_levels = {"ERROR", "WARNING", "FATAL", "INFO"}
    events = []

    for e in parsed_logs.get("entries", []):
        if e.get("level") not in important_levels:
            continue

        events.append({
            "level": e.get("level", "UNKNOWN"),
            "component": e.get("component", "UNKNOWN"),
            "message": e.get("message", ""),
            "timestamp": e.get("timestamp", "")
        })

    return events[:max_events]

# RCA ENTRY POINT
def run_rca(description: str, parsed_logs: dict | None = None) -> str:
    """
    Works with:
    - description only
    - description + parsed logs
    """

    # Prepare log summary
    llm_logs = build_llm_log_context(parsed_logs)

    if llm_logs:
        log_summary = "\n".join(
            f"[{e['level']}] {e['component']}: {e['message']}"
            for e in llm_logs
            if e["message"]
        )
    else:
        log_summary = "No log file provided or no significant log events found."

    # Fetch Jira issues
    jira_issues = search_jira()

    # Match Jira issues
    matched_issues = find_matching_jira_issues(
        jira_issues,
        user_description=description
    )

    jira_context = build_jira_context(matched_issues)

    # Step 4: Build LLM prompt
    if jira_context:
        jira_links = "\n".join(
            f"- {j['key']}: {j['title']} — {j['url']}"
            for j in jira_context
        )

        prompt = f"""
You are a senior SIP/HFA Root Cause Analysis engineer with deep expertise in
telephony call flows, SIP signaling, and phone state machines.

IMPORTANT RULES:
- The Jira issues listed below were pre-matched using deterministic keyword similarity.
- Do NOT invent new Jira tickets.
- Do NOT reference any Jira ticket other than the ones explicitly listed.
- Base your analysis strictly on the provided description and log events.

ISSUE DESCRIPTION:
{description}

PARSED LOG EVENTS (chronological order):
{log_summary}

MATCHING JIRA ISSUES:
{jira_links}

TASK:
1. Determine whether any of the listed Jira issues truly match the observed problem.
2. Explicitly mention the Jira key(s) and URL(s) that match, if applicable.
3. Provide a clear and concise root cause analysis based on the logs and comments of the jira tickets if any.
4. If a fix or workaround is mentioned in the matching Jira issue(s), summarize it.
5. If no fix is documented, suggest a technically sound fix based on the root cause.
6. write the output in professional English.


OUTPUT FORMAT:
- Matched Jira Issue(s): <key(s) or "None">
- Root Cause:
- Suggested Fix:
"""
    else:
        prompt = f"""
You are a senior SIP/HFA Root Cause Analysis engineer with deep expertise in
telephony call flows, SIP signaling, and phone state machines.

IMPORTANT RULES:
- No existing Jira tickets match this issue.
- Do NOT invent or reference any Jira ticket.
- Base your analysis strictly on the provided description and log events.

ISSUE DESCRIPTION:
{description}

PARSED LOG EVENTS (chronological order):
{log_summary}

TASK:
1. State clearly that no existing Jira ticket matches this issue.
2. Analyze the log events to identify the most likely root cause.
3. Provide a clear, technically accurate explanation of the failure.
4. Suggest concrete, actionable fixes or next debugging steps.
5. write the output in professional English.

OUTPUT FORMAT:
- Jira Match Status: No existing Jira ticket matches this issue
- Root Cause:
- Suggested Fix:
"""
    return run_llm(prompt)
