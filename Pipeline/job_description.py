from botasaurus.request import request, Request
from botasaurus.soupify import soupify

from botasaurus.browser import browser, Driver


@browser
def scrape_heading_task(driver: Driver, data):
    path = data['url']
    driver.get(path)
    # Try common containers one by one
    possible_sections = [
        "main",
        "article",
        "section",
        "[class*='job']",
        "[class*='description']",
        "[class*='desc']"
    ]
    results = {}
    for selector in possible_sections:
        try:
            results[selector] = driver.get_text(selector)
        except Exception:
            results[selector] = "not found"
    return results

class Scraper:
    def __init__(self,path):
        super().__init__()
        self.path = path

    def run(self):
        return scrape_heading_task({"url": self.path})
    

# Initiate the web scraping task
# path = "https://www.naukri.com/job-listings-walkin-drive-ai-engineer-intern-zycus-infotech-mumbai-0-to-1-years-230426029315?src=simJobDeskACP&sid=17785798263141793&xp=1&px=1"
# crawl = Scraper(path)
# crawl.run()

