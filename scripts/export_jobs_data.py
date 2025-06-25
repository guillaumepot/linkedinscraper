# scripts/export_jobs_data.py

import argparse
from datetime import datetime
import elasticsearch
import os
import pandas as pd
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def load_elasticsearch_config():
    config = {
        "hosts": os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
        "verify_certs": False,
        "use_ssl": False,
        "request_timeout": 30,
        "max_retries": 3,
        "retry_on_timeout": True
    }
    return config



def export_jobs_to_csv(output_file: str = None, index_name: str = "jobs"):

    # Generate output filename if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"jobs_export_{timestamp}.csv"
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else "."
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Starting export from Elasticsearch index '{index_name}'...")
    

    try:
        config = load_elasticsearch_config()
        es = elasticsearch.Elasticsearch(
            hosts = config['hosts'],
            verify_certs = config['verify_certs'],
            request_timeout = config['request_timeout'],
            max_retries = config['max_retries'],
            retry_on_timeout = config['retry_on_timeout']
        )
        
        # Tests
        # - connection
        if not es.ping():
            raise Exception("Could not connect to Elasticsearch")
        print(f"Connected to Elasticsearch at {config['hosts']}")
        # - index exists
        if not es.indices.exists(index=index_name):
            raise Exception(f"Index '{index_name}' does not exist")
        # - count job offers
        count_response = es.count(index=index_name)
        total_jobs = count_response['count']
        print(f"Found {total_jobs} documents in index '{index_name}'")
        if total_jobs == 0:
            print("No jobs found to export")
            return
        

        # Start export
        jobs_data = []
        batch_size = 100
        
        response = es.search(
            index=index_name,
            body={
                "query": {"match_all": {}},
                "size": batch_size,
                "_source": True
            },
            scroll='2m'
        )
        
        scroll_id = response['_scroll_id']
        hits = response['hits']['hits']
        
        print(f"Processing documents in batches of {batch_size}...")
        processed = 0
        
        while hits:
            for hit in hits:
                job_data = hit['_source']
                job_data['_id'] = hit['_id']
                jobs_data.append(job_data)
            
            processed += len(hits)
            print(f"Processed {processed}/{total_jobs} jobs ({processed/total_jobs*100:.1f}%)")
            
            # Get next batch of jobs
            response = es.scroll(scroll_id=scroll_id, scroll='2m')
            hits = response['hits']['hits']
        
        # Clear scroll
        es.clear_scroll(scroll_id=scroll_id)
        print(f"Retrieved {len(jobs_data)} jobs from Elasticsearch")
        

        # Convert to DataFrame
        df = pd.DataFrame(jobs_data)
        
        expected_columns = {
            '_id': '',
            'title': '',
            'company': '',
            'location': '',
            'description': '',
            'job_url': '',
            'date': '',
            'interest': False,
            'applied': False,
            'interview': False,
            'rejected': False,
            'not_interested': False,
            'filtered': False
        }
        
        for col, default_val in expected_columns.items():
            if col not in df.columns:
                df[col] = default_val
        
        column_order = ['_id', 'title', 'company', 'location', 'date', 'job_url', 
                       'interest', 'apply', 'interview', 'rejected', 'hide', 'description']
        
        # Reorder columns
        column_order = [col for col in column_order if col in df.columns]
        remaining_cols = [col for col in df.columns if col not in column_order]
        final_column_order = column_order + remaining_cols
        df = df[final_column_order]
        
        # Convert date columns
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Export to CSV
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        print(f"Successfully exported {len(df)} jobs to '{output_file}'")
        print(f"Columns exported: {', '.join(df.columns)}")
        
        return output_file
        
    except Exception as e:
        print(f"Error during export: {e}")
        raise
    finally:
        if 'es' in locals():
            es.close()

def main():
    parser = argparse.ArgumentParser(description='Export jobs data from Elasticsearch to CSV')
    parser.add_argument('--output', '-o', type = str, help = 'Output CSV file path')
    parser.add_argument('--index', '-i', type = str, default = 'jobs', help='Elasticsearch index name (default: jobs)')
    args = parser.parse_args()
    
    try:
        output_file = export_jobs_to_csv(args.output, args.index)
        print(f"\n Export completed successfully: {output_file}")
    except Exception as e:
        print(f"\nE xport failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()