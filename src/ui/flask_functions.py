# src/ui/flask_functions.py

from datetime import datetime


from src.job_scraping.ElasticSearchEngine import ElasticSearchEngine
from src.utils.common_func import load_configuration



# VARS
config = load_configuration('preferences.yaml', type='yaml')
openai_config = config['OpenAI']
config = load_configuration('src/job_scraping/config.json', type='json')
es_config = config['ElasticsearchEngine']
del config



# Functions
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