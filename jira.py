import os
import logging
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException
from dotenv import load_dotenv
from urllib.parse import quote
load_dotenv(".env")

logger = logging.getLogger(__name__)

JIRA_BASE_URL = "https://mitel.atlassian.net"
JIRA_USER = "harshini.juluri@mitel.com"
JIRA_TOKEN = "ATATT3xFfGF0idNQ3Ok5iXx18vEzP4Os2eS5bW7w5eZACGbmyQn9cSSa7-RhvoFm_qM6WYCmbIA2Kf0gCh9YlO_C5lKdVy2iKj1-x872wNP7vQSVLWiNuB_Q4K1XiuklbGIA2hwEoCmI2xrlgUtMM7167Npo1EsJkZC2ObGGEKdPdO-MvhPUQh0=4FE3119F"

if not JIRA_USER or not JIRA_TOKEN:
    raise RuntimeError("JIRA_USER / JIRA_TOKEN not set")

HEADERS = {
    "Accept": "application/json",
}

#def search_jira():
#    url = f"https://mitel.atlassian.net/rest/api/3/search/jql?fields=summary,comment,assignee,status,resolution&jql=project=DCOA"

#    params = {
#        "jql": jql,
#        "maxResults": limit,
#        "fields": "summary,description,comment,assignee,status,resolution",
#    }
#def search_jira():
#    url = f"{JIRA_BASE_URL}/rest/api/3/search"

#    params = {
#        "jql": "project=DCOA",
#        "fields": "summary,description,assignee,status,resolution",
#        "expand": "renderedFields",
#        "maxResults": 50
#    }

def search_jira():
    jql= "project=DCOA"


    url = (
        f"{JIRA_BASE_URL}/rest/api/3/search/jql"
        f"?fields=summary,comment,assignee,status,resolution"
        f"&jql={jql}"
    )

    response = requests.get(url)
    auth = HTTPBasicAuth(JIRA_USER, JIRA_TOKEN)

    logger.info("Jira GET %s", url)
    logger.info("JQL: %s")

    try:
        r = requests.get(
            url,
            headers=HEADERS,
#            params=params,
            auth=auth,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()

    except RequestException as exc:
        logger.exception("Jira API request failed")
        raise RuntimeError(f"Jira API request failed: {exc}") from exc

    issues = data.get("issues", [])
    logger.info("Jira returned %d issues", len(issues))
    return issues
def extract_text_from_adf(adf):
    texts = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                texts.append(node.get("text", ""))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for i in node:
                walk(i)

    if adf:
        walk(adf)
    return " ".join(texts)
def build_jira_context(issues):
    context = []

    for issue in issues:
        fields = issue.get("fields", {})

        summary = fields.get("summary")
        description = extract_text_from_adf(fields.get("description"))

        comments = []
        for c in fields.get("comment", {}).get("comments", []):
            body = c.get("body")
            text = extract_text_from_adf(body) if isinstance(body, dict) else body
            comments.append({
                "author": c.get("author", {}).get("displayName"),
                "created": c.get("created"),
                "text": text,
            })

        assignee = fields.get("assignee", {})
        status = fields.get("status", {}).get("name")
        resolution = fields.get("resolution", {})
        resolution_name = resolution.get("name") if isinstance(resolution, dict) else None

        context.append({
            "key": issue.get("key"),
            "url": f"{JIRA_BASE_URL}/browse/{issue.get('key')}",
            "title": summary,
            "description": description,
            "comments": comments[:10],
            "assignee": assignee.get("displayName") if assignee else None,
            "status": status,
            "resolution": resolution_name,
        })

    return context
