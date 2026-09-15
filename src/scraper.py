import re, os, json, requests, urllib3
from bs4 import BeautifulSoup
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

URL = "https://iost.tu.edu.np/notices"

COURSE_KEYWORDS = {
    "CSIT":  ["B.Sc.CSIT", "CSIT", "सीएसआईटी"],
    "BIT":   ["BIT", "बिआईटी"],
    "BTECH": ["B.Tech", "Food Technology"],
    "MSC":   ["M.Sc"],
}

ROMAN = {"VIII": 8, "VII": 7, "VI": 6, "IV": 4, "V": 5, "III": 3, "II": 2, "I": 1}


# ── Fallback functions (used if Groq fails) ────────────────────────────────────

def detect_course(title):
    matched = [
        course for course, keywords in COURSE_KEYWORDS.items()
        if any(kw in title for kw in keywords)
    ]
    if re.search(r"B\.?Sc\.?(?![\.\s]*CSIT)", title):
        matched.append("BSC")
    return matched if matched else ["ALL"]


def detect_target_batch(title):
    roman_pattern = "|".join(ROMAN.keys())
    match = re.search(
        rf"({roman_pattern})\s*Semester[\s\-]+(\d{{4}})",
        title,
        re.IGNORECASE
    )
    if match:
        sem_num = ROMAN.get(match.group(1).upper())
        year = int(match.group(2))
        if sem_num:
            return year - ((sem_num - 1) // 2)
    return None


# ── AI detection ───────────────────────────────────────────────────────────────

def ai_detect(title):
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": "You extract structured info from university notice titles. Reply ONLY with valid JSON, no explanation, no markdown."
            },
            {
                "role": "user",
                "content": f"""
Extract info from this notice title and return JSON with exactly these keys:
{{
  "courses": [],
  "semester": null,
  "target_batch": null
}}

Rules:
- courses: list from CSIT, BIT, BTECH, MSC, BSC. Use ["ALL"] if for everyone.
- CSIT means B.Sc.CSIT or सीएसआईटी. BSC is general B.Sc only, NOT B.Sc.CSIT.
- semester: integer 1-8 or null
- target_batch: nepali year integer (e.g. 2080) or null

Title: "{title}"
"""
            }
        ]
    )
    result = json.loads(response.choices[0].message.content)
    return result["courses"], result["target_batch"]


def detect_with_fallback(title):
    try:
        return ai_detect(title)
    except Exception as e:
        print(f"[Groq] Failed, using fallback: {e}")
        return detect_course(title), detect_target_batch(title)


# ── Scrapers ───────────────────────────────────────────────────────────────────

def scrape_notices():
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
        courses, target_batch = detect_with_fallback(title)

        results.append({
            "id":           int(notice_id),
            "title":        title,
            "url":          href,
            "date":         date.text.strip(),
            "courses":      courses,
            "target_batch": target_batch,
        })

    return results


def scrape_until(cutoff_date):
    results = []
    url = URL

    while url:
        try:
            response = requests.get(url, verify=False, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[Scraper] Pagination error: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        notice_tags = soup.select("div.recent-post-wrapper a")
        date_tags   = soup.select("div.recent-post-wrapper div.date")

        page_done = False
        for notice, date in zip(notice_tags, date_tags):
            href = notice.get("href", "")
            notice_id = href.split("/")[-1]
            if not notice_id.isdigit():
                continue

            notice_date = date.text.strip()
            if notice_date < cutoff_date:
                page_done = True
                break

            h5 = notice.find("h5")
            title = h5.text.strip() if h5 else ""
            courses, target_batch = detect_with_fallback(title)

            results.append({
                "id":           int(notice_id),
                "title":        title,
                "url":          href,
                "date":         notice_date,
                "courses":      courses,
                "target_batch": target_batch,
            })

        if page_done:
            break

        next_link = soup.select_one("a.next, a[rel='next'], li.next a")
        url = next_link["href"] if next_link else None

    return results