import argparse
import logging
import multiprocessing_logging
import uvicorn as uvicorn

import api.handler
from model.builder import ModelBuilder
from model.reader import ModelReader
from scrape.scraper import Scraper, retrieve_content


def main():
    parser = argparse.ArgumentParser(description="LinkMind CLI")
    parser.add_argument("command", choices=["scrape", "model", "classify", "api"], help="Command to execute")
    parser.add_argument("url", help="URL to scrape and classify", nargs="?")
    parser.add_argument(
        "--root-path",
        "-rp",
        help="The directory where the scraped web contents are saved",
        nargs='?',
        default='/tmp/linkmind'
    )
    parser.add_argument(
        "--sources-filepath",
        "-sp",
        help="The file path containing the list of web resources to scrape",
        nargs='?',
        default='./resources/sources.csv'
    )
    parser.add_argument(
        "--categories-filepath",
        "-cp",
        help="The file path containing the list of web categories",
        nargs='?',
        default='./resources/categories.csv'
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if args.command == "scrape":
        multiprocessing_logging.install_mp_handler()
        scraper = Scraper(args.sources_filepath, args.root_path)
        scraper.run()
    elif args.command == "model":
        model_builder = ModelBuilder(args.categories_filepath, args.root_path)
        model_builder.build()
    elif args.command == "classify":
        model_reader = ModelReader(args.categories_filepath, args.root_path)
        content = retrieve_content(args.url, "body")
        if content is None:
            print("cannot retrieve the content from url")
            return
        print(model_reader.classify(f"{content['title']}\n{content['content']}"))
    elif args.command == "api":
        uvicorn.run(api.handler.app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
