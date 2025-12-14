import time
import sys
import json
from pathlib import Path
import requests
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, Any, List, Set


@dataclass
class Config:
    base_url: str = "https://musicbrainz.org/ws/2"
    user_agent: str = "mb-lab/0.1 (contact: oliviaxu0401@gmail.com)"
    
    # Command-line arguments
    query: str = 'recording:"love" AND artist:"Radiohead"'
    pages: int = 4
    limit: int = 25
    
    # Output paths
    out_dir: Path = Path("outputs")
    search_csv: Path = field(init=False)
    details_csv: Path = field(init=False)
    json_dir: Path = field(init=False)

    def __post_init__(self):
        self.out_dir.mkdir(exist_ok=True)
        self.search_csv = self.out_dir / "musicbrainz_search.csv"
        self.details_csv = self.out_dir / "musicbrainz_details.csv"
        self.json_dir = self.out_dir / "details_json"
        self.json_dir.mkdir(exist_ok=True)


def build_session(user_agent: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": user_agent})
    return s


# =============== Fetch ===============
def fetch_api(session: requests.Session, url: str, params: dict, retries: int = 3) -> dict:
    for attempt in range(1, retries + 1):
        try:
            r = session.get(url, params=params, timeout=20)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt == retries:
                raise
            sleep_s = 2 ** (attempt - 1)
            print(f"[WARN] request failed (attempt {attempt}/{retries}): {e} -> sleep {sleep_s}s")
            time.sleep(sleep_s)
    return {} # Should not be reached


def search_all_recordings(session: requests.Session, cfg: Config) -> List[Dict[str, Any]]:
    results = []
    for page in range(cfg.pages):
        params = {
            "query": cfg.query,
            "fmt": "json",
            "limit": cfg.limit,
            "offset": page * cfg.limit,
        }
        data = fetch_api(session, f"{cfg.base_url}/recording", params)
        recs = data.get("recordings", [])
        print(f"[SEARCH] page={page+1}/{cfg.pages}  got={len(recs)}")
        results.extend(recs)
        time.sleep(1.05)
    return results


def lookup_recording_details(session: requests.Session, cfg: Config, mbid: str) -> dict:
    inc = "artists+releases+tags+ratings+genres"
    params = {"inc": inc, "fmt": "json"}
    return fetch_api(session, f"{cfg.base_url}/recording/{mbid}", params)


# =============== Parse ===============
def parse_search_results(records: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for rec in records:
        ac = rec.get("artist-credit") or []
        artist = ac[0].get("name") if ac else None
        rows.append({
            "mbid": rec.get("id"),
            "title": rec.get("title"),
            "artist": artist,
            "length_ms": rec.get("length"),
            "score": rec.get("score"),
        })
    df = pd.DataFrame(rows)
    df = df.dropna(subset=["mbid"]).drop_duplicates(subset=["mbid"])
    return df


def parse_detail_to_row(detail: dict, mbid: str) -> dict:
    title = detail.get("title")
    ac = detail.get("artist-credit") or []
    artist = ac[0].get("name") if ac else None
    releases = detail.get("releases") or []
    tags = detail.get("tags") or []
    genres = detail.get("genres") or []
    rating = detail.get("rating") or {}
    return {
        "mbid": mbid,
        "title": title,
        "artist": artist,
        "releases_count": len(releases),
        "top_tags": "|".join([t.get("name", "") for t in tags[:5] if t.get("name")]),
        "top_genres": "|".join([g.get("name", "") for g in genres[:5] if g.get("name")]),
        "rating_value": rating.get("value") if isinstance(rating, dict) else None,
        "rating_votes": rating.get("votes-count") if isinstance(rating, dict) else None,
    }

# =============== Save ===============
def save_search_results(df: pd.DataFrame, path: Path):
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"\n[OK] saved search -> {path}  rows={len(df)}")


def save_raw_detail(data: dict, mbid: str, path: Path):
    with open(path / f"recording_{mbid}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def append_details(new_rows: List[Dict[str, Any]], path: Path):
    if not new_rows:
        return
        
    df_new = pd.DataFrame(new_rows)
    if path.exists():
        df_old = pd.read_csv(path)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
        df_all = df_all.drop_duplicates(subset=["mbid"])
    else:
        df_all = df_new
    df_all.to_csv(path, index=False, encoding="utf-8")
    print(f"\n[OK] saved details -> {path}  rows={len(df_all)}")


# =============== Resume ===============
def load_done_mbids(details_csv: Path) -> Set[str]:
    if not details_csv.exists():
        return set()
    try:
        df = pd.read_csv(details_csv)
        if "mbid" in df.columns:
            return set(df["mbid"].dropna().astype(str).tolist())
    except Exception:
        pass
    return set()


# =============== Main ===============
def main() -> None:
    # ---- Config
    query = sys.argv[1] if len(sys.argv) > 1 else 'recording:"love" AND artist:"Radiohead"'
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 25
    cfg = Config(query=query, pages=pages, limit=limit)
    
    session = build_session(cfg.user_agent)

    # ---- Step A: Search
    search_results_raw = search_all_recordings(session, cfg)
    df_search = parse_search_results(search_results_raw)
    save_search_results(df_search, cfg.search_csv)

    # ---- Step B: Lookup (with Resume)
    done_mbids = load_done_mbids(cfg.details_csv)
    print(f"[RESUME] already have details for {len(done_mbids)} mbids")

    detail_rows = []
    mbids_to_fetch = df_search["mbid"].astype(str).tolist()
    total = len(mbids_to_fetch)

    for i, mbid in enumerate(mbids_to_fetch, 1):
        if mbid in done_mbids:
            print(f"[SKIP] {i}/{total} mbid={mbid} (already done)")
            continue

        detail_data = lookup_recording_details(session, cfg, mbid)
        save_raw_detail(detail_data, mbid, cfg.json_dir)
        
        row = parse_detail_to_row(detail_data, mbid)
        detail_rows.append(row)
        
        print(f"[LOOKUP] {i}/{total} mbid={mbid} ok")
        time.sleep(1.05)

    # ---- Step C: Append new details
    if detail_rows:
        append_details(detail_rows, cfg.details_csv)
    else:
        print("\n[OK] no new details to fetch (everything already done)")

    # ---- Step D: Quick Analysis
    try:
        df_details = pd.read_csv(cfg.details_csv)
        top_artists = df_details["artist"].value_counts().head(10)
        print("\n=== Quick Insight: Top 10 Artists in details ===")
        print(top_artists)
    except Exception:
        pass


if __name__ == "__main__":
    main()
