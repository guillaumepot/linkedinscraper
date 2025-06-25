# main.py

import argparse

from src.BeautifulSoupEngine import BeautifulSoupEngine
from src.ElasticSearchEngine import ElasticSearchEngine
from src.JobScraper import JobScraper
from src.utils.tools import load_configuration
from src.utils.LoggerManager import LoggerManager
from scripts.proxy_connection_tester import test_proxy_connection



class ArgumentParser:
    @staticmethod
    def parse_args(prog:str=None, description: str=None, epilog:str=None):
        """
        Define Arg parser

        Args:
        - prog: Program Name
        - description: What it does
        - epilog:  Text art the bottom of the help
        """

        parser = argparse.ArgumentParser(prog = prog,
                                         description = description,
                                         epilog = epilog)


        parser.add_argument(
            "-p", "--use-proxy",
            action = "store_true",
            help="Use the proxy connection test.",
        )


        parser.add_argument(
            "-d", "--dev",
            action = "store_true",
            help="Use the development logger (console only).",
        )

        args = parser.parse_args()
        return args


def get_config(config: dict) -> tuple[dict, dict, dict]:
    """
    Get the configuration from the config file.
    """
    es_config = config['ElasticsearchEngine']
    bs_config = config['BeautifulSoupEngine']
    logger_config = config['Logger']
    return es_config, bs_config, logger_config


def main(args, config: dict) -> None:
    # Get config dicts
    es_config, bs_config, logger_config = get_config(config)
    # Main Logger
    if args.dev:
        logger = LoggerManager.configure_logger(name = 'dev', logger_config = logger_config)
        logger.debug("initializing main script with development logs (console only)")
    else:
        logger = LoggerManager.configure_logger(name = 'default', logger_config = logger_config)


    # Test proxy connection 
    if args.use_proxy:
        bs_config = config['BeautifulSoupEngine']
        proxies = bs_config['proxies']
        headers = bs_config['headers']
        test_proxy_connection(proxies, headers)
        del proxies, headers, config


    # Test Elasticsearch connection and execute scraper
    try:
        with ElasticSearchEngine(es_config, logger) as elastic_engine:
            print(f"Elasticsearch connection successful: {elastic_engine.test_connection()['cluster_name']}")
            
            # Create index if it doesn't exist
            index_settings = {
                "mappings": {
                    "properties": {
                        "job_url": {"type": "keyword"},
                        "title": {"type": "text"},
                        "company": {"type": "text"},
                        "location": {"type": "text"},
                        "date": {"type": "date"},
                        "description": {"type": "text"},
                        "interest": {"type": "integer"},
                        "applied": {"type": "integer"},
                        "interview": {"type": "integer"},
                        "rejected": {"type": "integer"},
                        "hidden": {"type": "integer"},
                        "filtered": {"type": "integer"}
                    }
                }
            }
            elastic_engine.create_index(index = "jobs", settings = index_settings)

            # Execute scraper
            scraper = JobScraper(backend = elastic_engine,
                                 scrap_engine = BeautifulSoupEngine(bs_config, logger),
                                 logger = logger)
            
            scraper.execute_scraper(load_configuration('config/preferences.yaml', type='yaml'))

    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")
        raise e



if __name__ == "__main__":
    config = load_configuration('config/config.json', type = 'json')
    args = ArgumentParser.parse_args()
    main(args, config)