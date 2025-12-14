#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import requests


@dataclass
class Config:
    base: str = "https://www.deezer.com"
    target_page: str = "https://www.deezer.com/en/charts/track"
    timeout: int = 25

    out_json: Path = Path(os.environ.get("OUT_JSON", "outputs/deezer_page.json"))
    debug_dir: Path = Path(os.environ.get("DEBUG_DIR", "deezer_debug"))


def build_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "user-agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            ),
            "accept": "*/*",
            "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
            "referer": "https://www.deezer.com/",
            "origin": "https://www.deezer.com",
        }
    )

    cookie_str = os.environ.get("DEEZER_COOKIE", "").strip()
    if cookie_str:
        for part in cookie_str.split(";"):
            part = part.strip()
            if not part or "=" not in part:
                continue
            k, v = part.split("=", 1)
            s.cookies.set(k.strip(), v.strip(), domain=".deezer.com")

    sid = os.environ.get("DEEZER_SID", "").strip()
    if sid and not s.cookies.get("sid"):
        s.cookies.set("sid", sid, domain=".deezer.com")

    return s



def dump_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch(session: requests.Session, url: str, timeout: int) -> str:
    r = session.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text


def parse(html: str) -> Dict[str, Any]:
    start_str = "window.__DZR_APP_STATE__ = "
    start_index = html.find(start_str)
    if start_index == -1:
        raise RuntimeError("Could not find __DZR_APP_STATE__ in the page")

    start_json = start_index + len(start_str)
    
    # Find the matching closing brace
    brace_level = 0
    end_json = -1
    # Make sure we start at the first brace
    first_brace = html.find('{', start_json)
    if first_brace == -1:
        raise RuntimeError("Could not find the start of the JSON object")

    for i in range(first_brace, len(html)):
        if html[i] == '{':
            brace_level += 1
        elif html[i] == '}':
            brace_level -= 1
            if brace_level == 0:
                end_json = i + 1
                break
    
    if end_json == -1:
        raise RuntimeError("Could not find the end of the JSON object")

    json_str = html[first_brace:end_json]
    return json.loads(json_str)


def save(path: Path, data: Dict[str, Any]) -> None:
    dump_json(path, data)


def main() -> int:
    cfg = Config()
    session = build_session()
    html = ""
    try:
        html = fetch(session, cfg.target_page, cfg.timeout)
        data = parse(html)
        save(cfg.out_json, data)
        
        print(f"[OK] successfully extracted __DZR_APP_STATE__ -> {cfg.out_json.resolve()}")
        return 0

    except requests.RequestException as e:
        print(f"[ERROR] network/http error: {e}")
        return 1
    except (RuntimeError, json.JSONDecodeError) as e:
        print(f"[ERROR] failed to extract data: {e}")
        cfg.debug_dir.mkdir(parents=True, exist_ok=True)
        (cfg.debug_dir / "error.html").write_text(html, encoding="utf-8")
        print(f"saved error page to {cfg.debug_dir.resolve() / 'error.html'}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
