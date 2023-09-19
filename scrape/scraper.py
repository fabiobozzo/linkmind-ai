import csv
import multiprocessing
import os

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from config import csv_reader
from scrape import utils
from scrape.repository import Repository

default_http_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/58.0.3029.110 Safari/537.3"
}


class Scraper:
    def __init__(self, sources_file_path, root_folder_path, http_headers=None):
        self._sources = csv_reader.read_sources_csv(sources_file_path)
        self._root_folder_path = root_folder_path
        self._http_headers = http_headers
        if self._http_headers is None:
            self._http_headers = default_http_headers

    def run(self):
        num_workers = multiprocessing.cpu_count()
        with multiprocessing.Pool(num_workers) as pool:
            pool.map(self._scrape_source, self._sources)

    def _scrape_source(self, s: dict):
        print(f"=== START SCRAPING {s['category']} ::{s['url']} ===")

        source = utils.snake(urlparse(s['url']).netloc)
        source_path = os.path.join(self._root_folder_path, s['category'], source)
        if not os.path.exists(source_path):
            os.makedirs(source_path)
        repo = Repository(source_path)

        page_links = self._find_page_links(url=s['url'], max_depth=s['maxDepth'], link_class=s['linkClass'])
        for link in page_links:
            article = self._retrieve_article(link, s['articleTag'], s['articleClass'])
            if article is not None:
                repo.store_article(article['title'], article['content'])

        repo.dump_index()
        print(f"=== END SCRAPING {s['category']} ::{s['url']} ===")

    def _find_page_links(self, url, depth=1, max_depth=1, link_class="") -> set[str]:
        links = set()

        try:
            response = requests.get(url, headers=self._http_headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # print(f"GET {url} failed with {e}")
            return links

        soup = BeautifulSoup(response.content, "html.parser")

        links_find_all_kwargs = {}
        if len(link_class) > 0:
            links_find_all_kwargs['class_'] = link_class
        article_links = soup.find_all("a", **links_find_all_kwargs)  # Find article links on the page
        for link in article_links:
            if not link.has_key("href"):
                continue
            article_url = link["href"]
            article_url = urljoin(url, article_url)
            links.add(article_url)

        if depth < max_depth:
            links.update(self._find_page_links(url, depth + 1, max_depth, link_class))

        return links

    def _retrieve_article(self, url, article_tag, article_class="") -> dict | None:
        try:
            response = requests.get(url, headers=self._http_headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # print(f"GET {url} failed with {e}")
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

            return {
                "title": soup.find('title').string,
                "content": text
            }
        else:
            return None
