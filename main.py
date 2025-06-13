# main.py

import elasticsearch
import os

from src.job_scraping.JobScraper import JobScraper
from src.utils.ArgParser import ArgumentParser
from src.utils.common_func import load_configuration
from scripts.proxy_connection_tester import test_proxy_connection



def main(args):
    # Generate Data storage folders
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists('data/elasticsearch'):
        os.makedirs('data/elasticsearch')
    if not os.path.exists('data/kibana'):
        os.makedirs('data/kibana')

    # Test proxy connection 
    if not args.skip_proxy:
        scraper_config = load_configuration('src/job_scraping/config.json', type = 'json')['BeautifulSoupEngine']
        proxies = scraper_config['proxies']
        headers = scraper_config['headers']
        test_proxy_connection(proxies, headers)
        del proxies, headers, scraper_config

    # Test Elasticsearch connection
    try:
        _es = elasticsearch.Elasticsearch(
            hosts=["http://localhost:9200"],
            verify_certs=False
        )
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")

    # Execute scraper

    scraper = JobScraper()
    scraper.execute_scraper(load_configuration('preferences.yaml', type='yaml'))


if __name__ == "__main__":
    args = ArgumentParser.parse_args()
    main(args)