import json
import os
import time

from scrape import utils


class Repository:
    def __init__(self, root_folder):
        self._root_folder = root_folder
        self._index_path = os.path.join(self._root_folder, "index.json")
        self._index = {}
        if not os.path.exists(self._root_folder):
            os.mkdir(self._root_folder)
        if os.path.exists(self._index_path):
            with open(self._index_path) as index_file:
                self._index = json.load(index_file)

    def dump_index(self):
        with open(self._index_path, "w") as index_file:
            json.dump(self._index, index_file)

    def store_article(self, title, content):
        if len(title.strip()) == 0:
            return

        title = utils.snake(title.lower())

        if len(content.strip()) > 0:
            file_path = os.path.join(self._root_folder, title)
            if utils.short_hash(title) in self._index:
                return
            with open(file_path, "w") as article_file:
                # print("store_article: " + file_path)
                article_file.write(content)
                self._index[utils.short_hash(title)] = time.time()
