import re
from typing import List

from jira import search_jira, build_jira_context
from llm import run_llm
from log_analyzer import analyze_log_text, format_for_llm
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
    top_n: int = 3
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

    # DEBUG (uncomment if needed)
    # print("Top Jira match scores:")
    # for i, s in scored[:5]:
    #     print(i["key"], s, i["fields"]["summary"])

    return [i[0] for i in scored[:top_n]]

# RCA ENTRY POINT 
def run_rca(description: str, log_text: str = "") -> str:
    """
    Main RCA pipeline:
    1. Analyze logs
    2. Fetch Jira issues
    3. Deterministically match Jira issues
    4. Ask LLM to explain + RCA
    """
    # Step 1: Analyze logs
   
    log_analysis = analyze_log_text(log_text or "")
    log_summary = format_for_llm(log_analysis)

   
    # Step 2: Fetch Jira issues

    jira_issues = search_jira()

    # Step 3: Match Jira issues
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
You are a senior SIP/HFA Root Cause Analysis engineer.

IMPORTANT RULES:
- The Jira issues below were pre-matched by keyword similarity.
- Do NOT invent Jira tickets.
- ONLY reference the Jira issues listed below.

ISSUE DESCRIPTION:
{description}

LOG ANALYSIS SUMMARY:
{log_summary}

MATCHING JIRA ISSUES:
{jira_links}

TASK:
1. Confirm which Jira issue(s) match this problem.
2. Clearly mention the Jira key and URL.
3. Provide a concise root cause analysis.
4. Suggest clear, actionable fixes.
"""
    else:
        prompt = f"""
You are a senior SIP/HFA Root Cause Analysis engineer.

ISSUE DESCRIPTION:
{description}

LOG ANALYSIS SUMMARY:
{log_summary}

TASK:
1. State exactly: "No existing Jira ticket matches this issue."
2. Provide the most likely root cause.
3. Suggest clear, actionable fixes.
"""
  
    llm_output = run_llm(prompt)
    output_lines = []

    if jira_context:
        output_lines.append("**Matching Jira Tickets Found:**")
        for j in jira_context:
            output_lines.append(f"- {j['key']}: {j['url']}")
    else:
        output_lines.append("**No existing Jira ticket matches this issue.**")

    output_lines.append("\n---\n")
    output_lines.append("**Root Cause Analysis:**\n")
    output_lines.append(llm_output)

    return "\n".join(output_lines)
