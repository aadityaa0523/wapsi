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
    {
        "name": "RBI 2017: burden of proof on the bank",
        "url": "https://www.rbi.org.in/scripts/FS_Notification.aspx?Id=11040",
        "clause": "The burden of proving customer liability in case of unauthorised electronic banking transactions shall lie on the bank",
    },
    {
        "name": "RBI 2017: shadow reversal in 10 working days",
        "url": "https://www.rbi.org.in/scripts/FS_Notification.aspx?Id=11040",
        "clause": "within 10 working days from the date of such notification by the customer",
    },
    {
        "name": "RBI 2017: complaint resolved in 90 days",
        "url": "https://www.rbi.org.in/scripts/FS_Notification.aspx?Id=11040",
        "clause": "not exceeding 90 days from the date of receipt of the complaint",
    },
    {
        "name": "RBI 2027: compensation needs bank and police reports",
        "url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=13543&Mode=0",
        "clause": "on the National Cyber Crime Reporting Portal or National Cyber Crime Helpline (1930) and to the bank within five calendar days from its occurrence",
    },
    {
        "name": "RBI 2027: third-party breach, zero liability",
        "url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=13543&Mode=0",
        "clause": "reports the unauthorised fraudulent EBT to the bank within five calendar days from the date of its occurrence",
    },
    {
        "name": "RBI 2027: coerced approval counts as fraud",
        "url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=13543&Mode=0",
        "clause": "executed by the customer by granting approval under coercion or duress",
    },
    {
        "name": "RBI 2027: burden of proof on the bank",
        "url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=13543&Mode=0",
        "clause": "The burden of proving customer liability in complaints involving fraudulent EBTs shall lie on the bank",
    },
    {"name": "RBI 2026 directions press release", "url": "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=63011"},
    {"name": "RBI press release feed", "url": "https://www.rbi.org.in/pressreleases_rss.xml"},
    {"name": "RBI complaint portal", "url": "https://cms.rbi.org.in/"},
    {"name": "National cybercrime portal", "url": "https://cybercrime.gov.in/"},
    {"name": "Money Restoration portal", "url": "https://mrm-ncrp.mha.gov.in/public-info"},
    {"name": "IFSC lookup", "url": "https://ifsc.razorpay.com/SBIN0005943"},
]

CACHE_SECONDS = 300
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Wapsi status check)"}
RSS_URL = "https://www.rbi.org.in/pressreleases_rss.xml"
WATCH_WORDS = re.compile(r"liabilit|unauthori[sz]ed|fraud|customer protection|ombudsman|digital payment", re.I)
IFSC = re.compile(r"[A-Z]{4}0[A-Z0-9]{6}")
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
    async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=HEADERS, transport=transport) as client:
        sources, database = await asyncio.gather(
            asyncio.gather(*(check_source(client, source) for source in SOURCES)),
            asyncio.to_thread(check_database),
        )
    return {"generated_at": now(), "sources": list(sources), "database": database}


def rule_updates(transport=None):
    """RBI press releases that may change these rules. Flags them for a human; never changes a rule."""
    with httpx.Client(timeout=20, follow_redirects=True, headers=HEADERS, transport=transport) as client:
        response = client.get(RSS_URL)
        response.raise_for_status()
    titles = re.findall(r"<item>\s*<title><!\[CDATA\[(.*?)\]\]></title>", response.text, re.S)
    return [html.unescape(title).strip() for title in titles if WATCH_WORDS.search(title)]


def lookup_ifsc(code, transport=None):
    code = code.strip().upper()
    if not IFSC.fullmatch(code):
        raise ValueError("That is not a valid IFSC format.")
    with httpx.Client(timeout=20, transport=transport) as client:
        response = client.get(f"https://ifsc.razorpay.com/{code}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    data = response.json()
    return {"bank": data["BANK"], "branch": data["BRANCH"], "city": data["CITY"], "ifsc": code}


async def cached_status():
    # keyless public endpoint: the cache stops it being used to hammer government sites
    async with _lock:
        if _cache["body"] is None or time.monotonic() - _cache["at"] > CACHE_SECONDS:
            _cache["body"] = await run_checks()
            _cache["at"] = time.monotonic()
        return _cache["body"]
