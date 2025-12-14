import time
import sys
import json
from pathlib import Path
import requests
import pandas as pd

BASE = "https://musicbrainz.org/ws/2"
UA = "mb-lab/0.1 (contact: oliviaxu0401@gmail.com)"

OUT_DIR = Path("outputs")
OUT_DIR.mkdir(exist_ok=True)

s = requests.Session()
s.headers.update({"User-Agent": UA})


# =============== 0) 通用请求（带最简单重试） ===============
def mb_get(path: str, params: dict, retries: int = 3) -> dict:
    """
    作用：向 MusicBrainz 发 GET 请求，拿 JSON（dict）

    - path: "/recording" 或 "/recording/<mbid>"
    - params: 查询参数，比如 {"query":..., "fmt":"json"}
    - retries: 失败最多重试几次
    """
    url = f"{BASE}{path}"

    for attempt in range(1, retries + 1):
        try:
            r = s.get(url, params=params, timeout=20)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            # 最后一轮还失败就抛出
            if attempt == retries:
                raise
            # 简单退避：1s,2s,4s...
            sleep_s = 2 ** (attempt - 1)
            print(f"[WARN] request failed (attempt {attempt}/{retries}): {e} -> sleep {sleep_s}s")
            time.sleep(sleep_s)


# =============== 1) Search（索引层） ===============
def search_recordings(query: str, pages: int = 4, limit: int = 25) -> pd.DataFrame:
    """
    作用：分页 search，拿一批 recording 的“骨架信息（skeleton）”
    输出：DataFrame，至少包含 mbid（后续 lookup 必须）
    """
    rows = []

    for page in range(pages):
        params = {
            "query": query,
            "fmt": "json",
            "limit": limit,
            "offset": page * limit,
        }
        data = mb_get("/recording", params)

        recs = data.get("recordings", [])
        print(f"[SEARCH] page={page+1}/{pages}  got={len(recs)}")

        for rec in recs:
            ac = rec.get("artist-credit") or []
            artist = ac[0].get("name") if ac else None

            rows.append({
                "mbid": rec.get("id"),
                "title": rec.get("title"),
                "artist": artist,
                "length_ms": rec.get("length"),
                "score": rec.get("score"),
            })

        time.sleep(1.05)  # ✅ 官方建议 1 req/s

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["mbid"]).drop_duplicates(subset=["mbid"])
    return df


# =============== 2) Lookup（详情层） ===============
def lookup_recording(mbid: str) -> dict:
    """
    作用：用 mbid 查“单条详情”，并用 inc 拉更多关联字段
    """
    inc = "artists+releases+tags+ratings+genres"
    return mb_get(f"/recording/{mbid}", {"inc": inc, "fmt": "json"})


def parse_detail_to_row(detail: dict, mbid: str) -> dict:
    """
    作用：把 lookup 返回的“复杂 JSON”压平为一行表格（适合做 DataFrame）
    """
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


# =============== 3) 断点续跑（Resume） ===============
def load_done_mbid(details_csv: Path) -> set:
    """
    作用：如果 details.csv 已存在，读取已完成的 mbid，避免重复 lookup
    """
    if not details_csv.exists():
        return set()
    try:
        df = pd.read_csv(details_csv)
        if "mbid" in df.columns:
            return set(df["mbid"].dropna().astype(str).tolist())
    except Exception:
        pass
    return set()


# =============== 4) 主流程：Search -> 保存 -> Lookup -> 保存 ===============
def main():
    # ---- 命令行参数（都给默认值，保证你直接跑也能跑）
    # 用法：
    #   python3 musicbrainz_pipeline.py 'recording:"love" AND artist:"Radiohead"' 4 25
    query = sys.argv[1] if len(sys.argv) > 1 else 'recording:"love" AND artist:"Radiohead"'
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 25

    # ---- 输出路径
    search_csv = OUT_DIR / "musicbrainz_search.csv"
    details_csv = OUT_DIR / "musicbrainz_details.csv"
    json_dir = OUT_DIR / "details_json"
    json_dir.mkdir(exist_ok=True)

    # ---- Step A: Search（索引层）
    df_search = search_recordings(query=query, pages=pages, limit=limit)
    df_search.to_csv(search_csv, index=False, encoding="utf-8")
    print(f"\n[OK] saved search -> {search_csv}  rows={len(df_search)}")

    # ---- Step B: Lookup（详情层）+ Resume
    done = load_done_mbid(details_csv)
    print(f"[RESUME] already have details for {len(done)} mbids")

    detail_rows = []
    total = len(df_search)

    for i, mbid in enumerate(df_search["mbid"].astype(str).tolist(), 1):
        if mbid in done:
            print(f"[SKIP] {i}/{total} mbid={mbid} (already done)")
            continue

        detail = lookup_recording(mbid)

        # 保存每条完整 JSON（可复现/debug）
        with open(json_dir / f"recording_{mbid}.json", "w", encoding="utf-8") as f:
            json.dump(detail, f, ensure_ascii=False, indent=2)

        row = parse_detail_to_row(detail, mbid)
        detail_rows.append(row)

        print(f"[LOOKUP] {i}/{total} mbid={mbid} ok")

        time.sleep(1.05)  # ✅ 仍然限速

    # ---- Step C: 追加写入 details.csv（增量）
    if detail_rows:
        df_new = pd.DataFrame(detail_rows)

        if details_csv.exists():
            df_old = pd.read_csv(details_csv)
            df_all = pd.concat([df_old, df_new], ignore_index=True)
            df_all = df_all.drop_duplicates(subset=["mbid"])
        else:
            df_all = df_new

        df_all.to_csv(details_csv, index=False, encoding="utf-8")
        print(f"\n[OK] saved details -> {details_csv}  rows={len(df_all)}")
    else:
        print("\n[OK] no new details to fetch (everything already done)")

    # ---- Step D: 最小分析（可选，顺手给你一个小输出）
    # Top 10 artists
    try:
        df_details = pd.read_csv(details_csv)
        top_artists = df_details["artist"].value_counts().head(10)
        print("\n=== Quick Insight: Top 10 Artists in details ===")
        print(top_artists)
    except Exception:
        pass


if __name__ == "__main__":
    main()
