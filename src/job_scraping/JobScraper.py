# src/job_scraping/JobScraper.py

from datetime import datetime, timedelta
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
import pandas as pd


from src.job_scraping.ElasticSearchEngine import ElasticSearchEngine
from src.job_scraping.BeautifulSoupEngine import BeautifulSoupEngine
from src.utils.common_func import load_configuration, ExecutionTime
from src.utils.LoggerManager import LoggerManager

class JobScraper:
    def __init__(self):
        self.config = load_configuration('src/job_scraping/config.json', type = 'json')
        self.bs_config = self.config['BeautifulSoupEngine']
        self.es_config = self.config['ElasticsearchEngine']
        self.logger = LoggerManager.configure_logger(name='JobScraper', verbose=True)
    
    def apply_filters(self, df, preferences, filters:list) -> pd.DataFrame:
        def safe_detect(text):
            try:
                return detect(text)
            except LangDetectException:
                return 'en'
        
        # Initialize filtered column to False
        if 'filtered' not in df.columns:
            df['filtered'] = False
      
        # Title filter (filter if the title is not in the title_include corresponding to the preferences, also, exclude the words in the title_exclude corresponding to the preferences)
        if "title" in filters:
            title_include = preferences.get('title_include', [])
            title_exclude = preferences.get('title_exclude', [])
            
            for idx, row in df.iterrows():
                title = str(row['title']).lower()
                
                title_has_include = any(word.lower() in title for word in title_include)
                title_has_exclude = any(word.lower() in title for word in title_exclude)
                
                if not title_has_include or title_has_exclude:
                    df.at[idx, 'filtered'] = True

        # Company filter (filter if the company is in the company_exclude corresponding to the preferences)
        if "company" in filters:
            company_exclude = preferences.get('company_exclude', [])
            for idx, row in df.iterrows():
                company = str(row['company'])
                if company in company_exclude:
                    df.at[idx, 'filtered'] = True
        
        # Max age filter (filter if the job is older than the max age corresponding to the preferences)
        if "max_age" in filters:
            max_age_days = preferences.get('max_age', 7)
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            for idx, row in df.iterrows():
                if pd.notna(row['date']) and row['date'] < cutoff_date:
                    df.at[idx, 'filtered'] = True

        # Language filter (filter if the description is not in the languages, use safe_detect)
        if "languages" in filters:
            allowed_languages = preferences.get('languages', ['en'])
            for idx, row in df.iterrows():
                if 'description' in row and pd.notna(row['description']):
                    description = str(row['description'])
                    if description.strip():  # Only check if description is not empty
                        detected_lang = safe_detect(description)
                        if detected_lang not in allowed_languages:
                            df.at[idx, 'filtered'] = True

        # Description filter (do not filter if these words are in the description)
        if "description" in filters:
            desc_words = preferences.get('desc_words', [])
            for idx, row in df.iterrows():
                if 'description' in row and pd.notna(row['description']):
                    description = str(row['description']).lower()
                    has_required_word = any(word.lower() in description for word in desc_words)
                    if not has_required_word:
                        df.at[idx, 'filtered'] = True

        return df

    def remove_existing_jobs_in_database(self, df: pd.DataFrame, engine: ElasticSearchEngine, es_index: str):
        try:
            search_result = engine.search(query = {"query": {"match_all": {}}}, index = es_index)
            
            existing_jobs = []
            if 'hits' in search_result and 'hits' in search_result['hits']:
                for hit in search_result['hits']['hits']:
                    if '_source' in hit:
                        existing_jobs.append(hit['_source'])
            
            if not existing_jobs:
                self.logger.info("No existing jobs found in database")
                return df
                
            existing_jobs_df = pd.DataFrame(existing_jobs)
            self.logger.info(f"Found {len(existing_jobs_df)} existing jobs in database")
            
            if 'job_url' in existing_jobs_df.columns and 'job_url' in df.columns:
                existing_urls = set(existing_jobs_df['job_url'].tolist())
                df_filtered = df[~df['job_url'].isin(existing_urls)]
                removed_count = len(df) - len(df_filtered)
                if removed_count > 0:
                    self.logger.info(f"Removed {removed_count} jobs that already exist in database")
                return df_filtered
            else:
                existing_jobs_df['title_company'] = existing_jobs_df['title'].astype(str) + "_" + existing_jobs_df['company'].astype(str)
                df['title_company'] = df['title'].astype(str) + "_" + df['company'].astype(str)
                
                existing_combinations = set(existing_jobs_df['title_company'].tolist())
                df_filtered = df[~df['title_company'].isin(existing_combinations)]
                
                df_filtered = df_filtered.drop(columns=['title_company'])
                
                removed_count = len(df) - len(df_filtered)
                if removed_count > 0:
                    self.logger.info(f"Removed {removed_count} jobs that already exist in database (based on title+company)")
                return df_filtered
                
        except Exception as e:
            self.logger.warning(f"Error checking existing jobs in database: {e}. Proceeding with all jobs.")
            return df

    @ExecutionTime
    def execute_scraper(self, preferences: dict):
        # Get job cards (one shot research)
        with BeautifulSoupEngine(self.bs_config, preferences) as bs_engine:
            job_cards = bs_engine.get_jobcards(preferences)

        # Insert jobs in a DataFrame
        jobs_df = pd.DataFrame(job_cards)
        
        # Check if any jobs were found initially
        if len(jobs_df) == 0 or jobs_df.empty:
            self.logger.warning("No jobs found from scraping")
            return
            
        self.logger.info(f"Found {len(jobs_df)} job cards from scraping")
        
        # Convert date to datetime
        jobs_df['date'] = pd.to_datetime(jobs_df['date'], format = '%Y-%m-%d', errors = 'coerce')

        # Apply filters: Remove duplicates, user preferences, jobs already in the database
        filters = ["title", "company", "max_age"]
        jobs_df = jobs_df.drop_duplicates(subset = ['title', 'company'], keep = 'first')
        jobs_df = self.apply_filters(jobs_df,
                                     preferences,
                                     filters)

        # Check if the job is already in the database
        if len(jobs_df) > 0:
            with ElasticSearchEngine(config = self.es_config) as es_engine:
                jobs_df = self.remove_existing_jobs_in_database(jobs_df,
                                                                engine = es_engine,
                                                                es_index = "jobs")

        # Request job descriptions
        if len(jobs_df) > 0:
            with BeautifulSoupEngine(self.bs_config, preferences) as bs_engine:
                job_descriptions = bs_engine.get_job_descriptions([url for url in jobs_df['job_url']])


            jobs_df['description'] = job_descriptions

            # Apply filters: language, description
            filters = ["language", "description"]
            jobs_df = self.apply_filters(jobs_df,
                                        preferences,
                                        filters)
            
            # Add columns: interest, applied, interview, rejected
            jobs_df['interest'] = False
            jobs_df['applied'] = False
            jobs_df['interview'] = False
            jobs_df['rejected'] = False

            # convert df to dict
            new_jobs = jobs_df.to_dict(orient = 'records')
            del jobs_df

            # Insert new jobs into the database
            with ElasticSearchEngine(config = self.es_config) as es_engine:
                try:
                    es_engine.insert_jobs(new_jobs, index = "jobs")
                    self.logger.info(f"Successfully inserted {len(new_jobs)} new jobs into database")

                except Exception as e:
                    self.logger.error(f"Failed to insert new jobs into database: {e}")