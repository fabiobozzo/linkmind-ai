import json
import logging
import multiprocessing
import os

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from scrape import utils, config
from scrape.repository import Repository

default_http_headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/109.0",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    "Referer": "http://www.google.com/",
    "Cache-Control": "max-age=0"
}


class Scraper:
    def __init__(self, sources_file_path, root_folder_path):
        self._sources = config.read_sources_csv(sources_file_path)
        self._root_folder_path = root_folder_path

    def run(self):
        logging.info(f"scraping of {len(self._sources)} sources has started")
        num_workers = multiprocessing.cpu_count()
        with multiprocessing.Pool(num_workers) as pool:
            pool.map(self._scrape_source, self._sources)

    def _scrape_source(self, s: dict):
        source = utils.snake(urlparse(s['url']).netloc)
        source_path = os.path.join(self._root_folder_path, s['category'], source)
        if not os.path.exists(source_path):
            os.makedirs(source_path)
        repo = Repository(source_path)

        headers = default_http_headers
        if not s['headers'] == "":
            headers = json.loads(s['headers'])

        page_links = self._find_page_links(
            url=s['url'],
            max_depth=s['maxDepth'],
            link_class=s['linkClass'],
            headers=headers
        )
        logging.debug(f"found {len(page_links)} links for source {s['url']} ({s['category']})")

        count = 0
        for link in page_links:
            article = retrieve_content(link, s['articleTag'], s['articleClass'], headers=headers)
            if article is not None:
                if repo.store_article(article['title'], article['content']):
                    count += 1

        repo.dump_index()

        logging.debug(f"scraped {count} articles for source {s['url']} ({s['category']}) ✓")

    def _find_page_links(self, url, depth=1, max_depth=1, link_class="", headers=None) -> set[str]:
        links = set()

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # logging.error(f"http error:{response.status_code} GET {url}")
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


def retrieve_content(url, element_tag, element_class="", headers=None):
    if not headers:
        headers = default_http_headers

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # logging.error(f"http error: GET {url}", e, exc_info=True)
        return None

    soup = BeautifulSoup(response.content, "html.parser")

    article_find_all_kwargs = {}
    if len(element_class) > 0:
        article_find_all_kwargs['class_'] = element_class
    article = soup.find(element_tag, **article_find_all_kwargs)  # Extract article content
    if article:
        text = ''
        paragraphs = article.find_all("p")
        if len(paragraphs) > 0:
            text = " ".join(p.get_text() for p in paragraphs)

        if text.strip() == '':
            text = article.get_text()

        # text preprocessing steps
        text = text.strip()
        title = soup.find('title').string

        if text and title:
            return {"title": title, "content": text}

    return None
