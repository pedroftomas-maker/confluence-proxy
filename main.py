import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
CONFLUENCE_BASE = "https://secil-pt.atlassian.net/wiki"
TOKEN = os.environ.get("CONFLUENCE_TOKEN")

class QueryIn(BaseModel):
    query: str

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/search-confluence")
async def search_confluence(payload: QueryIn):
    if not TOKEN:
        raise HTTPException(status_code=500, detail="CONFLUENCE_TOKEN not set")
    query = (payload.query or "").strip()
    if len(query) < 3:
        raise HTTPException(status_code=400, detail="Query too short")

    url = f"{CONFLUENCE_BASE}/rest/api/search"
    cql = f'text ~ "{query}" AND type = "page"'
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            url,
            params={"cql": cql, "limit": 5},
            headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"},
        )
    if resp.status_code >= 400:
        # temporarily surface Confluence response to debug
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    results = [
        {
            "title": r["title"],
            "url": f'{r["_links"]["base"]}{r["_links"]["webui"]}',
            "snippet": r.get("excerpt", ""),
        }
        for r in data.get("results", [])
    ]
    return {"results": results}

