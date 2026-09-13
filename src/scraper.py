import re
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://iost.tu.edu.np/notices"

# Courses with their keyword variants (English + Nepali)
# BSC is handled separately via regex — do not add here
COURSE_KEYWORDS = {
    "CSIT":  ["B.Sc.CSIT", "CSIT", "सीएसआईटी"],
    "BIT":   ["BIT", "बिट"],
    "BTECH": ["B.Tech", "Food Technology"],
    "MSC":   ["M.Sc"],
}

# Roman numerals in order — longer ones must come first
ROMAN = {"VIII": 8, "VII": 7, "VI": 6, "IV": 4, "V": 5, "III": 3, "II": 2, "I": 1}


def detect_course(title):
    matched = [
        course for course, keywords in COURSE_KEYWORDS.items()
        if any(kw in title for kw in keywords)
    ]

    # BSC: match "B.Sc" only when NOT followed by optional dots/spaces then "CSIT"
    if re.search(r"B\.?Sc\.?(?![\.\s]*CSIT)", title):
        matched.append("BSC")

    return matched if matched else ["ALL"]


def detect_target_batch(title):
    """
    Try to extract which batch year this notice targets.
    Looks for patterns like 'IV Semester-2081' or 'III Semester - 2080'.
    Returns a batch year int, or None if not found.
    """
    roman_pattern = "|".join(ROMAN.keys())  # VIII|VII|VI|...
    match = re.search(
        rf"({roman_pattern})\s*Semester[\s\-]+(\d{{4}})",
        title,
        re.IGNORECASE
    )
    if match:
        sem_num = ROMAN.get(match.group(1).upper())
        year = int(match.group(2))
        if sem_num:
            # Semester 1-2 → batch year, 3-4 → year-1, etc.
            batch_year = year - ((sem_num - 1) // 2)
            return batch_year
    return None


def scrape_notices():
    """
    Fetch and parse the notices page.
    Returns a list of dicts with keys: id, title, url, date, courses, target_batch
    """
    try:
        response = requests.get(URL, verify=False, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[Scraper] Error fetching page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    notice_tags = soup.select("div.recent-post-wrapper a")
    date_tags   = soup.select("div.recent-post-wrapper div.date")

    results = []
    for notice, date in zip(notice_tags, date_tags):
        href = notice.get("href", "")
        notice_id = href.split("/")[-1]

        if not notice_id.isdigit():
            continue

        h5 = notice.find("h5")
        title = h5.text.strip() if h5 else ""

        results.append({
            "id":           int(notice_id),
            "title":        title,
            "url":          href,
            "date":         date.text.strip(),
            "courses":      detect_course(title),
            "target_batch": detect_target_batch(title),
        })

    return results