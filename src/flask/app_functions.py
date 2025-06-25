# src/flask/app_functions.py

from datetime import datetime
import os
import PyPDF2
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils'))

from ElasticSearchEngine import ElasticSearchEngine


es_host = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
es_verify_certs = os.getenv('ELASTICSEARCH_VERIFY_CERTS', False)
es_use_ssl = os.getenv('ELASTICSEARCH_USE_SSL', False)
es_ca_certs = os.getenv('ELASTICSEARCH_CA_CERTS', None)
es_basic_auth = os.getenv('ELASTICSEARCH_BASIC_AUTH', None)
es_indexes = os.getenv('ELASTICSEARCH_INDEXES', ['jobs'])

es_config: dict = {
    "hosts": es_host,
    "verify_certs": es_verify_certs,
    "use_ssl": es_use_ssl,
    "ca_certs": es_ca_certs,
    "basic_auth": es_basic_auth,
    "indexes": es_indexes
  }

es_engine = ElasticSearchEngine(es_config)

# Func
def load_pdf_file(file_path: str):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text


def load_cv_text():
    """Load CV text from /app/cv.pdf if it exists"""
    cv_path = "/app/cv.pdf"
    if os.path.exists(cv_path):
        try:
            return load_pdf_file(cv_path)
        except Exception as e:
            print(f"Error loading CV: {e}")
            return None
    return None


def preprocess_text(text):
    """Preprocess text for similarity calculation"""
    if not text:
        return ""
    # Convert to lowercase, remove special characters, keep only alphanumeric and spaces
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_stopwords():
    """Get combined English and French stopwords"""
    # English stopwords
    english_stopwords = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'been', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'would', 'you', 'your', 'yours', 'yourself',
        'yourselves', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
        'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who',
        'whom', 'this', 'these', 'those', 'am', 'is', 'are', 'was', 'were',
        'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
        'can', 'could', 'should', 'ought', 'now', 'about', 'above', 'after',
        'again', 'against', 'all', 'any', 'both', 'each', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 's', 't', 'just', 'don', 'now'
    }
    
    # French stopwords
    french_stopwords = {
        'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'à', 'ce',
        'il', 'elle', 'on', 'ils', 'elles', 'je', 'tu', 'nous', 'vous',
        'me', 'te', 'se', 'lui', 'leur', 'mon', 'ma', 'mes', 'ton', 'ta',
        'tes', 'son', 'sa', 'ses', 'notre', 'nos', 'votre', 'vos', 'leur',
        'leurs', 'qui', 'que', 'quoi', 'dont', 'où', 'comment', 'quand',
        'pourquoi', 'est', 'sont', 'être', 'avoir', 'ai', 'as', 'a', 'avons',
        'avez', 'ont', 'été', 'étant', 'ayant', 'eu', 'eue', 'eues', 'eus',
        'eut', 'eûmes', 'eûtes', 'eurent', 'suis', 'es', 'sommes', 'êtes',
        'était', 'étais', 'étions', 'étiez', 'étaient', 'fus', 'fut', 'fûmes',
        'fûtes', 'furent', 'serai', 'seras', 'sera', 'serons', 'serez', 'seront',
        'serais', 'serait', 'serions', 'seriez', 'seraient', 'aurai', 'auras',
        'aura', 'aurons', 'aurez', 'auront', 'aurais', 'aurait', 'aurions',
        'auriez', 'auraient', 'dans', 'sur', 'avec', 'par', 'pour', 'sans',
        'sous', 'vers', 'chez', 'contre', 'entre', 'parmi', 'pendant', 'selon',
        'malgré', 'grâce', 'si', 'comme', 'quand', 'lorsque', 'puisque', 'car',
        'mais', 'ou', 'donc', 'or', 'ni', 'soit', 'très', 'plus', 'moins',
        'aussi', 'encore', 'déjà', 'toujours', 'jamais', 'souvent', 'parfois',
        'quelquefois', 'bien', 'mal', 'mieux', 'pire', 'peut', 'peuvent',
        'pouvez', 'pouvons', 'puis', 'pourrai', 'pourras', 'pourra', 'pourrons',
        'pourrez', 'pourront', 'pourrais', 'pourrait', 'pourrions', 'pourriez',
        'pourraient', 'veux', 'veut', 'voulons', 'voulez', 'veulent', 'voudrai',
        'voudras', 'voudra', 'voudrons', 'voudrez', 'voudront', 'voudrais',
        'voudrait', 'voudrions', 'voudriez', 'voudraient'
    }
    
    # Combine sets
    return english_stopwords.union(french_stopwords)


def calculate_cv_match_percentage(job_description, cv_text):
    """Calculate similarity percentage between job description and CV"""
    if not cv_text or not job_description:
        return 0.0
    
    try:
        # Preprocess texts
        job_desc_clean = preprocess_text(job_description)
        cv_clean = preprocess_text(cv_text)
        
        if not job_desc_clean or not cv_clean:
            return 0.0
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            stop_words=list(get_stopwords()),
            max_features=1000,
            ngram_range=(1, 2)
        )
        
        # Fit and transform
        tfidf_matrix = vectorizer.fit_transform([job_desc_clean, cv_clean])
        
        # cosine similarity
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        percentage = round(similarity * 100, 1)
        
        return max(0.0, min(100.0, percentage))
    
    except Exception as e:
        print(f"Error calculating CV match: {e}")
        return 0.0


def get_job_stats():
    """Get job statistics"""
    with es_engine:
        try:
            query = {
                "size": 0,
                "aggs": {
                    "interested": {
                        "filter": {
                            "bool": {
                                "should": [
                                    {"term": {"interest": 1}},
                                ]
                            }
                        }
                    },
                    "applied": {
                        "filter": {
                            "bool": {
                                "should": [
                                    {"term": {"applied": 1}},
                                ]
                            }
                        }
                    },
                    "interview": {
                        "filter": {
                            "bool": {
                                "should": [
                                    {"term": {"interview": 1}},
                                ]
                            }
                        }
                    },
                    "rejected": {
                        "filter": {
                            "bool": {
                                "should": [
                                    {"term": {"rejected": 1}},
                                ]
                            }
                        }
                    },
                    "hidden": {
                        "filter": {
                            "bool": {
                                "should": [
                                    {"term": {"hidden": 1}},
                                ]
                            }
                        }
                    },
                    "filtered": {
                        "filter": {
                            "bool": {
                                "should": [
                                    {"term": {"filtered": 1}},
                                ]
                            }
                        }
                    }
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
                'applied': int(aggs.get('applied', {}).get('doc_count', 0)),
                'rejected': int(aggs.get('rejected', {}).get('doc_count', 0)),
                'interview': int(aggs.get('interview', {}).get('doc_count', 0)),
                'interested': int(aggs.get('interested', {}).get('doc_count', 0)),
                'hidden': int(aggs.get('hidden', {}).get('doc_count', 0)),
                'filtered': int(aggs.get('filtered', {}).get('doc_count', 0))
            }
        except Exception as e:
            print(f"Error getting job stats: {e}")
            return {'total': 0, 'applied': 0, 'rejected': 0, 'interview': 0, 'interested': 0, 'hidden': 0, 'filtered': 0}
        

def get_jobs_from_es(search_query=None, filters=None, page=1, per_page=20, sort_by_cv_match=False):
    """Get jobs from Elasticsearch with optional search and filters"""
    with es_engine:
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
        
        if search_query and search_query.strip():
            query["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": search_query,
                    "fields": ["title^3", "company^2", "description", "location"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        
        # Filters
        if not filters:
            filters = {}
            
        for field in ['interest', 'applied', 'interview', 'rejected', 'hidden', 'filtered']:
            if field in filters and filters[field] == 'true':
                query["query"]["bool"]["filter"].append({
                    "bool": {
                        "should": [
                            {"term": {field: 1}},
                        ]
                    }
                })
        
        # Special handling for excluding filtered jobs by default
        if filters.get('exclude_filtered') == 'true':
            query["query"]["bool"]["filter"].append({
                "bool": {
                    "must_not": [
                        {"term": {"filtered": 1}}
                    ]
                }
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
        
        if sort_by_cv_match:
            query["size"] = 1000
            query["from"] = 0
        
        if (not query["query"]["bool"]["must"] and 
            not query["query"]["bool"]["filter"] and 
            (not search_query or not search_query.strip())):
            query["query"] = {"match_all": {}}
        elif not query["query"]["bool"]["must"] and not query["query"]["bool"]["filter"]:

            if search_query and search_query.strip():
                pass
            else:
                query["query"] = {"match_all": {}}
        
        try:
            response = es_engine.search(query, "jobs")
            
            jobs = []
            total = response.get('hits', {}).get('total', {})
            if isinstance(total, dict):
                total_count = total.get('value', 0)
            else:
                total_count = total
                
            # Load CV for all jobs
            cv_text = load_cv_text()
                
            for hit in response.get('hits', {}).get('hits', []):
                job = hit['_source']
                job['_id'] = hit['_id']
                
                # Calculate CV match percentage
                job_description = job.get('description', '')
                job['cv_match_percentage'] = calculate_cv_match_percentage(job_description, cv_text)
                
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
            
            # Sort by CV match
            if sort_by_cv_match:
                jobs.sort(key=lambda x: x['cv_match_percentage'], reverse=True)
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                jobs = jobs[start_idx:end_idx]
            
            return {
                'jobs': jobs,
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page,
                'cv_available': cv_text is not None
            }
        except Exception as e:
            print(f"Error searching jobs: {e}")
            return {'jobs': [], 'total': 0, 'page': 1, 'per_page': per_page, 'total_pages': 0, 'cv_available': False}
        

def update_job_status(job_id, field, value):
    """Update a job's status field in Elasticsearch"""
    with es_engine:
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
    with es_engine:
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
    with es_engine:
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
