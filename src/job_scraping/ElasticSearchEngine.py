# src/job_scraping/ElasticSearchEngine.py

import elasticsearch
from src.utils.LoggerManager import LoggerManager


class ElasticSearchEngine:
    """Engine for managing Elasticsearch operations including indexing and searching job data."""
    
    def __init__(self, config: dict):
        """Initialize the Elasticsearch engine with configuration.
        
        Args:
            config (dict): Configuration dictionary containing hosts, credentials, and other settings.
        """
        self.logger = LoggerManager.configure_logger(name='ElasticsearchEngine', verbose=True)
        self.config = config
        self.es = elasticsearch.Elasticsearch(
            hosts = self.config['hosts'],
            max_retries = 3,
            retry_on_timeout = True,
            request_timeout = 30,
            verify_certs = self.config['verify_certs']
        )
        
   
    def __enter__(self):
        """Context manager entry point."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit point, closes Elasticsearch connection."""
        if hasattr(self, 'es'):
            self.es.close()

    def test_connection(self):
        """Test the connection to Elasticsearch cluster.
        
        Returns:
            bool: True if connection is successful, False otherwise.
        """
        try:
            return self.es.ping()
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    def _create_indices_safely(self):
        """Create required indices safely, handling any errors that occur."""
        for index_name in ["jobs"]:
            try:
                self.create_index(index=index_name)
            except Exception as e:
                self.logger.error(f"Failed to create index '{index_name}': {e}")

    def create_index(self, index: str, settings: dict = None):
        """Create an Elasticsearch index if it doesn't exist.
        
        Args:
            index (str): Name of the index to create.
            settings (dict, optional): Index settings. Defaults to None.
            
        Raises:
            Exception: If index creation fails.
        """
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
        """Delete an Elasticsearch index if it exists.
        
        Args:
            index (str): Name of the index to delete.
        """
        try:
            if self.es.indices.exists(index=index):
                self.es.indices.delete(index=index)
                self.logger.info(f"Index '{index}' deleted successfully.")
            else:
                self.logger.warning(f"Index '{index}' does not exist.")
        except Exception as e:
            self.logger.error(f"Error deleting index '{index}': {e}")

    def search(self, query: str, index: str = "jobs"):
        """Search for documents in an Elasticsearch index.
        
        Args:
            query (str): Elasticsearch query to execute.
            index (str, optional): Index name to search in. Defaults to "jobs".
            
        Returns:
            dict: Search results or empty results if error occurs.
        """
        try:
            return self.es.search(index=index, body=query)
        except Exception as e:
            self.logger.error(f"Error searching in index {index}: {e}")
            return {"hits": {"hits": []}}
        
    def insert_jobs(self, jobs: list, index: str = "jobs"):
        """Insert job documents into Elasticsearch using bulk operation.
        
        Args:
            jobs (list): List of job dictionaries to insert.
            index (str, optional): Index name to insert into. Defaults to "jobs".
            
        Returns:
            dict: Bulk operation response.
            
        Raises:
            Exception: If bulk insert operation fails.
        """
        try:
            self.create_index(index)
            
            bulk_data = []
            for job in jobs:
                bulk_data.append({
                    "index": {
                        "_index": index
                    }
                })
                bulk_data.append(job)
            
            response = self.es.bulk(body=bulk_data)
            
            if response.get('errors'):
                error_items = [item for item in response['items'] if 'error' in item.get('index', {})]
                if error_items:
                    self.logger.error(f"Bulk insert had errors: {error_items}")
                    raise Exception(f"Bulk insert had {len(error_items)} errors")
                    
            return response
            
        except Exception as e:
            self.logger.error(f"Error inserting jobs into index {index}: {e}")
            raise