import argparse
import logging

from ml.model import ModelBuilder
from scrape.scraper import Scraper


def main():
    parser = argparse.ArgumentParser(description="LinkMind CLI")
    parser.add_argument("command", choices=["scrape", "model"], help="Command to execute")
    parser.add_argument(
        "--root-path",
        "-r",
        help="The directory where the scraped web contents are saved",
        nargs='?',
        default='/tmp/linkmind'
    )
    parser.add_argument(
        "--sources-filepath",
        "-s",
        help="The file path containing the list of web resources to scrape",
        nargs='?',
        default='./resources/sources.csv'
    )
    parser.add_argument(
        "--categories-filepath",
        "-c",
        help="The file path containing the list of web categories",
        nargs='?',
        default='./resources/categories.csv'
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if args.command == "scrape":
        scraper = Scraper(args.sources_path, args.root_path)
        scraper.run()
    elif args.command == "model":
        model_builder = ModelBuilder(args.categories_path, args.root_path, "classifier.pkl")
        model_builder.build()


if __name__ == "__main__":
    main()
