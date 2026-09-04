import re

from bs4 import BeautifulSoup
import requests


# header
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    """Returns the title and contents of the website at the given URL"""

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.title.string if soup.title else 'No title found'

    if soup.body is None:
        return f"{title}\n\nNo page body found."

    for irrelevant in soup.body(["script", "style", "img", "input"]):
        irrelevant.decompose()

    text = soup.body.get_text(separator="\n", strip=True)

    return title + "\n\n" + text



def fetch_website_links(url):
    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get('href') for link in soup.find_all("a")]

    return [link for link in links if link]

