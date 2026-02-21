import argparse
import time
import re
import requests
from bs4 import BeautifulSoup


SCHOLAR_ID = "Wyw_fPIAAAAJ"
README_PATH = "README.md"
START_TAG = "<!-- START_SCHOLAR -->"
END_TAG = "<!-- END_SCHOLAR -->"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

BASE_URL = "https://scholar.google.com"


def get_publications(user_id: str, limit: int = 10) -> list[dict]:
    """
    Fetch the `limit` most recent publications from a Google Scholar profile.

    Args:
        user_id: The Google Scholar user ID (the `user` query param in the profile URL).
        limit:   Maximum number of publications to return.

    Returns:
        A list of dicts with keys: title, authors, venue, year, citations, url
    """
    publications = []
    start = 0
    page_size = min(limit, 100)  # Scholar supports up to 100 per page

    session = requests.Session()
    session.headers.update(HEADERS)

    while len(publications) < limit:
        params = {
            "user": user_id,
            "sortby": "pubdate",   # sort by publication date (newest first)
            "cstart": start,
            "pagesize": page_size,
        }

        url = f"{BASE_URL}/citations"
        resp = session.get(url, params=params, timeout=15)

        if resp.status_code == 429:
            raise RuntimeError("Rate-limited by Google Scholar. Wait a while before retrying.")
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        rows = soup.select("tr.gsc_a_tr")
        if not rows:
            break  # No more results

        for row in rows:
            if len(publications) >= limit:
                break

            # Title & link
            title_el = row.select_one("a.gsc_a_at")
            title = title_el.get_text(strip=True) if title_el else "N/A"
            pub_path = title_el["href"] if title_el and title_el.has_attr("href") else ""
            pub_url = BASE_URL + pub_path if pub_path else "N/A"

            # Authors & venue (stored in .gs_gray spans)
            gray = row.select("div.gs_gray")
            authors = gray[0].get_text(strip=True) if len(gray) > 0 else "N/A"
            venue = gray[1].get_text(strip=True) if len(gray) > 1 else "N/A"

            # Year
            year_el = row.select_one("span.gsc_a_h")
            year = year_el.get_text(strip=True) if year_el else "N/A"

            # Citation count
            cite_el = row.select_one("a.gsc_a_ac")
            citations = cite_el.get_text(strip=True) if cite_el else "0"
            citations = citations if citations else "0"

            publications.append({
                "title":     title,
                "authors":   authors,
                "venue":     venue,
                "year":      year,
                "citations": citations,
                "url":       pub_url,
            })

        # If we got fewer rows than requested, we've reached the end
        if len(rows) < page_size:
            break

        start += page_size
        time.sleep(1)  # Be polite — avoid hammering Scholar

    return publications[:limit]


def print_publications(pubs: list[dict]) -> None:
    for i, p in enumerate(pubs, 1):
        print(f"\n[{i}] {p['title']}")
        print(f"    Authors  : {p['authors']}")
        print(f"    Venue    : {p['venue']}")
        print(f"    Year     : {p['year']}")
        print(f"    Citations: {p['citations']}")
        print(f"    URL      : {p['url']}")


def extract_user_id(user_or_url: str) -> str:
    """Accept either a raw user ID or a full Scholar profile URL."""
    if user_or_url.startswith("http"):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(user_or_url).query)
        ids = qs.get("user", [])
        if not ids:
            raise ValueError("Could not extract user ID from URL.")
        return ids[0]
    return user_or_url


# ── CLI ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch latest Google Scholar publications.")
    parser.add_argument("--limit", type=int, default=4, help="Number of publications to fetch (default: 10)")
    args = parser.parse_args()

    uid = SCHOLAR_ID

    print(f"Fetching {args.limit} latest publication(s) for user: {uid}\n")
    pubs = get_publications(uid, limit=args.limit * 2)

    latest = []
    for pub in pubs:
        try:
            title = pub["title"]
            venue = pub["venue"]
            year = pub["year"]
            venue_year = f"{venue}, {year}"
            url = pub["url"]
            if url:
                latest.append(f"- 📄 [{title}]({url}) ({venue_year})")
            else:
                latest.append(f"- 📄 **{title}** ({venue_year})")
        except Exception as e:
            print(f"Error processing publication: {e}")
            continue
    latest = latest[:args.limit]

    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()
    # put in readme
    pattern = f"{START_TAG}.*?{END_TAG}"
    replacement = f"{START_TAG}\n" + "\n".join(latest) + f"\n{END_TAG}"
    updated_readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated_readme)
