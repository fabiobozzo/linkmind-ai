import argparse

from scrape.repository import Repository
from scrape.scraper import Scraper


def main():
    parser = argparse.ArgumentParser(description="LinkMind CLI")
    parser.add_argument("command", choices=["scrape", "model"], help="Command to execute")
    parser.add_argument(
        "--root",
        "-r",
        help="The directory where the scraped web contents are saved",
        nargs='?',
        default='/tmp/linkmind'
    )
    parser.add_argument(
        "--sources",
        "-s",
        help="The file path containing the list of web resources to scrape",
        nargs='?',
        default='./sources.csv'
    )
    parser.add_argument(
        "--categories",
        "-c",
        help="The file path containing the list of web categories",
        nargs='?',
        default='./categories.csv'
    )

    args = parser.parse_args()

    if args.command == "scrape":
        repo = Repository(args.root)
        scraper = Scraper(repo, args.sources)
        scraper.run()
    elif args.command == "model":
        print("TODO")


if __name__ == "__main__":
    main()
