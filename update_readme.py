from scholarly import scholarly
import re

SCHOLAR_ID = "Wyw_fPIAAAAJ"
README_PATH = "README.md"
START_TAG = "<!-- START_SCHOLAR -->"
END_TAG = "<!-- END_SCHOLAR -->"


def fetch_latest_pubs(scholar_id, n=3):
    author = scholarly.search_author_id(scholar_id)
    author_filled = scholarly.fill(author, sections=["publications"])
    pubs = sorted(
        author_filled["publications"],
        key=lambda p: int(p.get("bib", {}).get("pub_year", 0)),
        reverse=True
    )
    latest = []
    for pub in pubs[:n]:
        bib = pub.get("bib", {})
        title = bib.get("title", "Untitled")
        venue = bib.get("venue", "")
        year = bib.get("pub_year", "")
        venue_year = f"{venue}, {year}"
        if not venue:
            venue_year = bib.get("citation", "")
        url = pub.get("pub_url", "")
        if url:
            latest.append(f"- 📄 [{title}]({url}) ({venue_year})")
        else:
            latest.append(f"- 📄 **{title}** ({venue_year})")
    return latest


def update_readme_section(content, new_lines):
    pattern = f"{START_TAG}.*?{END_TAG}"
    replacement = f"{START_TAG}\n" + "\n".join(new_lines) + f"\n{END_TAG}"
    return re.sub(pattern, replacement, content, flags=re.DOTALL)


if __name__ == "__main__":
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    latest_pubs = fetch_latest_pubs(SCHOLAR_ID)
    updated_readme = update_readme_section(readme, latest_pubs)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated_readme)
