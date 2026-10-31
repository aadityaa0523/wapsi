import asyncio
import hashlib
import html
import os
import re
import time
from datetime import datetime, timezone

import httpx
import psycopg

SOURCES = [
    {
        "name": "RBI 2017 customer liability circular",
        "url": "https://www.rbi.org.in/scripts/FS_Notification.aspx?Id=11040",
        "clause": "within three working days of receiving the communication from the bank",
    },
    {"name": "RBI 2026 directions press release", "url": "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=63011"},
    {"name": "RBI press release feed", "url": "https://www.rbi.org.in/pressreleases_rss.xml"},
    {"name": "RBI complaint portal", "url": "https://cms.rbi.org.in/"},
    {"name": "National cybercrime portal", "url": "https://cybercrime.gov.in/"},
    {"name": "Money Restoration portal", "url": "https://mrm-ncrp.mha.gov.in/public-info"},
    {"name": "IFSC lookup", "url": "https://ifsc.razorpay.com/SBIN0005943"},
]

CACHE_SECONDS = 300
_cache = {"at": 0.0, "body": None}
_lock = asyncio.Lock()


def now():
    return datetime.now(timezone.utc).isoformat()


def page_text(body):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))


async def check_source(client, source):
    result = {"name": source["name"], "url": source["url"], "checked_at": now(), "reachable": False}
    try:
        response = await client.get(source["url"])
    except httpx.HTTPError as error:
        result["error"] = type(error).__name__
        return result
    result["status_code"] = response.status_code
    result["reachable"] = response.is_success
    result["sha256"] = hashlib.sha256(response.content).hexdigest()
    if "clause" in source and response.is_success:
        result["clause_verified"] = source["clause"] in page_text(response.text)
    return result


def check_database():
    url = os.environ.get("DATABASE_URL")
    if not url:
        return {"configured": False, "reachable": False}
    try:
        with psycopg.connect(url, connect_timeout=5) as connection:
            connection.execute("select 1")
        return {"configured": True, "reachable": True}
    except psycopg.Error as error:
        # type name only: psycopg messages can include the connection host
        return {"configured": True, "reachable": False, "error": type(error).__name__}


async def run_checks(transport=None):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Wapsi status check)"}
    async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=headers, transport=transport) as client:
        sources, database = await asyncio.gather(
            asyncio.gather(*(check_source(client, source) for source in SOURCES)),
            asyncio.to_thread(check_database),
        )
    return {"generated_at": now(), "sources": list(sources), "database": database}


async def cached_status():
    # keyless public endpoint: the cache stops it being used to hammer government sites
    async with _lock:
        if _cache["body"] is None or time.monotonic() - _cache["at"] > CACHE_SECONDS:
            _cache["body"] = await run_checks()
            _cache["at"] = time.monotonic()
        return _cache["body"]
