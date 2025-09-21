import requests
from bs4 import BeautifulSoup

def fetch_title(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip() if soup.title and soup.title.string else url
        return title
    except Exception:
        return url
