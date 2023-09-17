import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

default_http_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/58.0.3029.110 Safari/537.3"
}


class Scraper:
    def __init__(self, repo, sources_file_path, http_headers=None):
        self._sources_file_path = sources_file_path
        self._http_headers = http_headers
        self.repository = repo
        if self._http_headers is None:
            self._http_headers = default_http_headers

    def run(self):
        with open(self._sources_file_path) as sources_file:
            sources_csv = csv.reader(sources_file)
            next(sources_file)  # skip the csv headers
            for row in sources_csv:
                cat = row[0]
                url = row[1]
                lnk_cls = row[2]
                art_tag = row[3]
                print(f"===\ncategory:{cat} url:{url}")
                page_links = self._scrape_page_links(url=url, link_class=lnk_cls)
                for link in page_links:
                    article = self._scrape_article(link, art_tag)
                    if article is not None:
                        self.repository.store_article(cat, url, article)
                print("===")

    def _scrape_page_links(self, url, depth=1, max_depth=2, link_class=""):
        links = set()

        try:
            response = requests.get(url, headers=self._http_headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"GET {url} failed with {e}")
            return links

        soup = BeautifulSoup(response.content, "html.parser")

        links_find_all_kwargs = {}
        if len(link_class) > 0:
            links_find_all_kwargs['class_'] = link_class
        article_links = soup.find_all("a", **links_find_all_kwargs)  # Find article links on the page
        for link in article_links:
            article_url = link["href"]
            article_url = urljoin(url, article_url)
            links.add(article_url)

        if depth < max_depth:
            links.update(self._scrape_page_links(url, depth + 1, max_depth, link_class))

        return links

    def _scrape_article(self, url, article_tag, article_class=""):
        print(f"scrape_article: {url}")
        try:
            response = requests.get(url, headers=self._http_headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"GET {url} failed with {e}")
            return None

        soup = BeautifulSoup(response.content, "html.parser")

        article_find_all_kwargs = {}
        if len(article_class) > 0:
            article_find_all_kwargs['class_'] = article_class
        article = soup.find(article_tag, **article_find_all_kwargs)  # Extract article content
        if article:
            paragraphs = article.find_all("p")
            if len(paragraphs) > 0:
                text = " ".join(p.get_text() for p in paragraphs)
            else:
                text = article.get_text()

            # text preprocessing steps
            text = text.strip()

            title = soup.find('title')

            return title.string, text
        else:
            return None
