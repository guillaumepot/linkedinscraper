# src/job_scraping/ElasticSearchEngine.py

import elasticsearch
from src.utils.LoggerManager import LoggerManager


class ElasticSearchEngine:
    def __init__(self, config: dict):
        self.logger = LoggerManager.configure_logger(name='ElasticsearchEngine', verbose=True)
        self.config = config

        connection_params = {
            'hosts': self.config['hosts'],
            'max_retries': 3,
            'retry_on_timeout': True,
            'request_timeout': 30,
            'verify_certs': self.config.get('verify_certs', False)
        }
        
        if self.config.get('use_ssl', False):
            connection_params['use_ssl'] = True
            if self.config.get('ca_certs'):
                connection_params['ca_certs'] = self.config['ca_certs']
        
        if self.config.get('basic_auth'):
            connection_params['basic_auth'] = self.config['basic_auth']
            
        self.es = elasticsearch.Elasticsearch(**connection_params)
        
        try:
            if not self.test_connection():
                self.logger.error("Failed to connect to Elasticsearch")
                raise ConnectionError("Cannot connect to Elasticsearch")
                
            # Create indices with error handling
            self._create_indices_safely()
            
        except Exception as e:
            self.logger.error(f"Error initializing Elasticsearch connection: {e}")
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(self, 'es'):
            self.es.close()

    def test_connection(self):
        try:
            return self.es.ping()
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    def _create_indices_safely(self):
        for index_name in ["jobs"]:
            try:
                self.create_index(index=index_name)
            except Exception as e:
                self.logger.error(f"Failed to create index '{index_name}': {e}")

    def create_index(self, index: str, settings: dict = None):
        try:
            if not self.es.indices.exists(index=index):
                self.es.indices.create(index=index, body=settings)
                self.logger.info(f"Index '{index}' created successfully.")
            else:
                self.logger.debug(f"Index '{index}' already exists.")
        except Exception as e:
            self.logger.error(f"Error creating index '{index}': {e}")
            raise

    def delete_index(self, index: str):
        try:
            if self.es.indices.exists(index=index):
                self.es.indices.delete(index=index)
                self.logger.info(f"Index '{index}' deleted successfully.")
            else:
                self.logger.warning(f"Index '{index}' does not exist.")
        except Exception as e:
            self.logger.error(f"Error deleting index '{index}': {e}")

    def search(self, query: str, index: str = "jobs"):
        try:
            return self.es.search(index=index, body=query)
        except Exception as e:
            self.logger.error(f"Error searching in index {index}: {e}")
            return {"hits": {"hits": []}}
        
    def insert_jobs(self, jobs: list, index: str = "jobs"):
        try:
            self.es.bulk(index=index, body=jobs)
        except Exception as e:
            self.logger.error(f"Error inserting jobs into index {index}: {e}")
            raise