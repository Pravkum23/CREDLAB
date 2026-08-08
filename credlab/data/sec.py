"""Small, cached SEC Company Facts client using only the standard library."""
from __future__ import annotations

import json
import logging
import time
import gzip
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LOG = logging.getLogger(__name__)
BASE_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


class SecClient:
    """Fetch SEC JSON while respecting identity, caching, and request pacing."""

    def __init__(self, user_agent: str, cache_dir: Path, min_interval: float = 0.12) -> None:
        if "@" not in user_agent:
            raise ValueError("SEC_USER_AGENT must identify an organization and email address")
        self.user_agent = user_agent
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.min_interval = min_interval
        self._last_request = 0.0

    def company_facts(self, cik: str, refresh: bool = False) -> dict:
        cik = str(cik).zfill(10)
        target = self.cache_dir / f"CIK{cik}.json"
        if target.exists() and not refresh:
            return json.loads(target.read_text(encoding="utf-8"))
        delay = self.min_interval - (time.monotonic() - self._last_request)
        if delay > 0:
            time.sleep(delay)
        req = Request(BASE_URL.format(cik=cik), headers={"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate"})
        try:
            with urlopen(req, timeout=30) as response:  # noqa: S310 - fixed SEC URL
                raw = response.read()
                if response.headers.get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                payload = json.loads(raw.decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"SEC Company Facts request failed for CIK {cik}: {exc}") from exc
        finally:
            self._last_request = time.monotonic()
        target.write_text(json.dumps(payload), encoding="utf-8")
        LOG.info("Cached SEC Company Facts for CIK %s", cik)
        return payload
