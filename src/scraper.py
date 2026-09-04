import requests
from bs4 import BeautifulSoup

url = "https://iost.tu.edu.np/notices"

# get url fetched
response = requests.get(url, verify=False)

# print(response.status_code)
# print(response)

soup = BeautifulSoup(response.text, 'html.parser')

# print(soup.prettify())

# extract details
notices =  soup.select("div.recent-post-wrapper a")
dates =  soup.select("div.recent-post-wrapper div.date")

COURSE_KEYWORDS = {
    "CSIT": ["B.sc.CSIT", "CSIT", "सीएसआईटी"],
    "BIT": ["BIT", "बिआईटी"],
    "BTECH": ["B.Tech", "Food Technology"],
    "MSC": ["M.Sc"],
    "BSC": ["B.Sc."],
}

def detect_course(title):
    matched = [course for course, keywords in COURSE_KEYWORDS.items() 
               if any(kw in title for kw in keywords)]
    return matched if matched else ["ALL"]


for notice, date in zip(notices, dates):
    courses = detect_course(notice.find("h5").text.strip())
    # print(notice["href"])
    # print(notice["href"].split("/")[-1])
    # print(notice.find("h5").text.strip())
    # print(date.text.strip())
    print(courses)



