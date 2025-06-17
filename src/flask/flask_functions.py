# src/ui/flask_functions.py

from datetime import datetime
import elasticsearch
import json
import yaml

es_config: dict = {
    "hosts": "http://localhost:9200",
    "verify_certs": False,
    "use_ssl": False,
    "indexes": ["jobs"]
}


# Functions
def load_configuration(file_path: str, type: str = 'yaml'):
    if type == 'yaml':
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    elif type == 'json':
        with open(file_path, 'r') as f:
            return json.load(f)



def get_jobs_from_es(search_query=None, filters=None, page=1, per_page=20):
    """Get jobs from Elasticsearch with optional search and filters"""
    with ElasticSearchEngine(es_config) as es_engine:
        # Build the query
        query = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            },
            "sort": [
                {"date": {"order": "desc"}},
                "_score"
            ],
            "from": (page - 1) * per_page,
            "size": per_page
        }
        
        # Add search query if provided
        if search_query and search_query.strip():
            query["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": search_query,
                    "fields": ["title^3", "company^2", "description", "location"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        
        # Add filters
        if not filters:
            filters = {}
            
        # Filter by status fields
        for field in ['interest', 'applied', 'interview', 'rejected', 'not_interested']:
            if field in filters and filters[field] is not None:
                query["query"]["bool"]["filter"].append({
                    "term": {field: filters[field]}
                })
        
        # Handle filtered field specially - exclude filtered jobs by default
        if 'filtered' in filters and filters['filtered'] is not None:
            # User explicitly wants to see filtered jobs
            query["query"]["bool"]["filter"].append({
                "term": {"filtered": filters['filtered']}
            })
        else:
            # By default, exclude filtered jobs (show only non-filtered jobs)
            query["query"]["bool"]["filter"].append({
                "term": {"filtered": False}
            })
        
        # Filter by company
        if filters.get('company'):
            query["query"]["bool"]["filter"].append({
                "term": {"company.keyword": filters['company']}
            })
            
        # Filter by date range
        if filters.get('date_from') or filters.get('date_to'):
            date_filter = {"range": {"date": {}}}
            if filters.get('date_from'):
                date_filter["range"]["date"]["gte"] = filters['date_from']
            if filters.get('date_to'):
                date_filter["range"]["date"]["lte"] = filters['date_to']
            query["query"]["bool"]["filter"].append(date_filter)
        
        # If no conditions, match all
        if not query["query"]["bool"]["must"] and not query["query"]["bool"]["filter"]:
            query["query"] = {"match_all": {}}
        
        try:
            response = es_engine.search(query, "jobs")
            
            jobs = []
            total = response.get('hits', {}).get('total', {})
            if isinstance(total, dict):
                total_count = total.get('value', 0)
            else:
                total_count = total
                
            for hit in response.get('hits', {}).get('hits', []):
                job = hit['_source']
                job['_id'] = hit['_id']
                # Format date for display
                if job.get('date'):
                    try:
                        if isinstance(job['date'], str):
                            job['date_formatted'] = datetime.fromisoformat(job['date'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
                        else:
                            job['date_formatted'] = job['date']
                    except (ValueError, TypeError):
                        job['date_formatted'] = job['date']
                else:
                    job['date_formatted'] = 'N/A'
                jobs.append(job)
            
            return {
                'jobs': jobs,
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            }
        except Exception as e:
            print(f"Error searching jobs: {e}")
            return {'jobs': [], 'total': 0, 'page': 1, 'per_page': per_page, 'total_pages': 0}

def update_job_status(job_id, field, value):
    """Update a job's status field in Elasticsearch"""
    with ElasticSearchEngine(es_config) as es_engine:
        try:
            update_body = {
                "doc": {
                    field: value
                }
            }
            response = es_engine.es.update(
                index="jobs",
                id=job_id,
                body=update_body
            )
            return response
        except Exception as e:
            print(f"Error updating job {job_id}: {e}")
            return None

def delete_job(job_id):
    """Delete a job from Elasticsearch"""
    with ElasticSearchEngine(es_config) as es_engine:
        try:
            response = es_engine.es.delete(
                index="jobs",
                id=job_id
            )
            return response
        except Exception as e:
            print(f"Error deleting job {job_id}: {e}")
            return None

def get_companies():
    """Get unique companies from the database"""
    with ElasticSearchEngine(es_config) as es_engine:
        try:
            query = {
                "size": 0,
                "aggs": {
                    "companies": {
                        "terms": {
                            "field": "company.keyword",
                            "size": 100
                        }
                    }
                }
            }
            response = es_engine.search(query, "jobs")
            companies = []
            for bucket in response.get('aggregations', {}).get('companies', {}).get('buckets', []):
                companies.append(bucket['key'])
            return sorted(companies)
        except Exception as e:
            print(f"Error getting companies: {e}")
            return []

def get_job_stats():
    """Get job statistics"""
    with ElasticSearchEngine(es_config) as es_engine:
        try:
            query = {
                "size": 0,
                "aggs": {
                    "applied": {"sum": {"field": "applied"}},
                    "rejected": {"sum": {"field": "rejected"}},
                    "interview": {"sum": {"field": "interview"}},
                    "interested": {"sum": {"field": "interest"}},
                    "not_interested": {"sum": {"field": "not_interested"}},
                    "filtered": {"sum": {"field": "filtered"}}
                }
            }
            response = es_engine.search(query, "jobs")
            aggs = response.get('aggregations', {})
            
            # Get total count from hits.total
            total = response.get('hits', {}).get('total', {})
            if isinstance(total, dict):
                total_count = total.get('value', 0)
            else:
                total_count = total
            
            return {
                'total': int(total_count),
                'applied': int(aggs.get('applied', {}).get('value', 0)),
                'rejected': int(aggs.get('rejected', {}).get('value', 0)),
                'interview': int(aggs.get('interview', {}).get('value', 0)),
                'interested': int(aggs.get('interested', {}).get('value', 0)),
                'not_interested': int(aggs.get('not_interested', {}).get('value', 0)),
                'filtered': int(aggs.get('filtered', {}).get('value', 0))
            }
        except Exception as e:
            print(f"Error getting job stats: {e}")
            return {'total': 0, 'applied': 0, 'rejected': 0, 'interview': 0, 'interested': 0, 'not_interested': 0, 'filtered': 0}
        


class ElasticSearchEngine:
    """Engine for managing Elasticsearch operations including indexing and searching job data."""
    
    def __init__(self, config: dict):
        """Initialize the Elasticsearch engine with configuration.
        
        Args:
            config (dict): Configuration dictionary containing hosts, credentials, and other settings.
        """
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
            print(f"Connection test failed: {e}")
            return False


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
            print(f"Error searching in index {index}: {e}")
            return {"hits": {"hits": []}}