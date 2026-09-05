import requests, re
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://iost.tu.edu.np/notices"
response = requests.get(url, verify=False)
soup = BeautifulSoup(response.text, 'html.parser')

notices = soup.select("div.recent-post-wrapper a")
dates = soup.select("div.recent-post-wrapper div.date")

# Expanded regex patterns for all M.Sc branches
# Expanded dictionary with strict M.Sc. bounding and new Bachelor programs
COURSE_PATTERNS = {
    # Bachelor Subjects
    "CSIT": r"CSIT|सीएसआईटी", 
    "BIT": r"\bBIT\b|बिआईटी|Information Technology",
    "BTECH Food": r"(?:B\.?\s*Tech).*(?:Food)|(?:Food).*(?:B\.?\s*Tech)|B\.?\s*Tech|Food Technology",
    "B MATH": r"Bachelor in Mathematical Science|B\.?\s*Math",
    "BDS (Data Science)": r"Bachelor in Data Science|BDS",
    
    # STRICT M.Sc Subjects
    "MSC Physics": r"(?:M\.?\s*Sc|स्नातकोत्तर).*(?:Physics|भौतिक)|(?:Physics|भौतिक).*(?:M\.?\s*Sc|स्नातकोत्तर)",
    "MSC Biotechnology": r"(?:M\.?\s*Sc|स्नातकोत्तर).*(?:Biotechnology)|(?:Biotechnology).*(?:M\.?\s*Sc|स्नातकोत्तर)",
    "MSC Mathematics": r"(?:M\.?\s*Sc|स्नातकोत्तर).*(?:Math(?:ematics)?|गणित)|(?:Math(?:ematics)?|गणित).*(?:M\.?\s*Sc|स्नातकोत्तर)",
    "MSC Statistics": r"(?:M\.?\s*Sc|स्नातकोत्तर).*(?:Stat(?:istics)?|तथ्याङ्क)|(?:Stat(?:istics)?|तथ्याङ्क).*(?:M\.?\s*Sc|स्नातकोत्तर)",
    "MSC Chemistry": r"(?:M\.?\s*Sc|स्नातकोत्तर).*(?:Chemistry|रसायन)|(?:Chemistry|रसायन).*(?:M\.?\s*Sc|स्नातकोत्तर)",
    "MSC Food": r"(?:M\.?\s*Sc|स्नातकोत्तर).*(?:Food)|(?:Food).*(?:M\.?\s*Sc|स्नातकोत्तर)",
    
    # General Degree Catch-alls
    "MSC Generic": r"M\.?\s*Sc|स्नातकोत्तर", 
    "BSC Generic": r"B\.?\s*Sc\.?(?![\.\s]*CSIT)" 
}

def detect_course(title):
    matched = []
    
    for course, pattern in COURSE_PATTERNS.items():
        if re.search(pattern, title, re.IGNORECASE):
            matched.append(course)
            
    # Cleanup logic: If a specific MSC (like MSC Physics) is found, remove "MSC Generic"
    msc_specifics = [c for c in matched if c.startswith("MSC ") and c != "MSC Generic"]
    if msc_specifics and "MSC Generic" in matched:
        matched.remove("MSC Generic")
        
    return matched if matched else ["ALL"]

for notice, date in zip(notices, dates):
    h5_tag = notice.find("h5")
    if not h5_tag:
        continue
        
    title = h5_tag.get_text(strip=True)
    published_date = date.get_text(strip=True)
    link = notice.get("href", "")
    
    courses = detect_course(title)
    
    print(f"Date: {published_date}")
    print(f"Title: {title}")
    print(f"Courses: {courses}")
    print(f"Link: {link}")
    print("-" * 60)