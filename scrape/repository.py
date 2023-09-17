import os
import re
from urllib.parse import urlparse


def _snake(s):
    return re.sub(r'[\W_]+', '_', s)


class Repository:
    def __init__(self, root_folder):
        self._root_folder = root_folder
        if not os.path.exists(self._root_folder):
            os.mkdir(self._root_folder)

    def store_article(self, category, source, article):
        source_domain = urlparse(source).netloc
        category_path = os.path.join(self._root_folder, category, _snake(source_domain))
        if not os.path.exists(category_path):
            os.makedirs(category_path)

        title = article[0]
        content = article[1]
        content_preview = content[:20] if len(content) > 20 else content

        if len(title.strip()) == 0:
            title = f"NA_{source}_{content_preview}"

        if len(content.strip()) > 0:
            file_path = os.path.join(category_path, _snake(title))
            with open(file_path, "w") as article_file:
                print(f"writing {file_path}")
                article_file.write(content)
