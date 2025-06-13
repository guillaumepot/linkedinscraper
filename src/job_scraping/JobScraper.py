# src/job_scraping/JobScraper.py

from datetime import datetime, timedelta
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
import pandas as pd


from src.job_scraping.ElasticSearchEngine import ElasticSearchEngine
from src.job_scraping.BeaufitulSoupEngine import BeautifulSoupEngine
from src.utils.common_func import load_configuration, ExecutionTime


class JobScraper:
    def __init__(self):
        self.config = load_configuration('src/job_scraping/config.json', type = 'json')
        self.bs_config = self.config['BeautifulSoupEngine']
        self.es_config = self.config['ElasticsearchEngine']
    
    def apply_filters(self, df, preferences, filters:list) -> pd.DataFrame:
        def safe_detect(text):
            try:
                return detect(text)
            except LangDetectException:
                return 'en'
        
        # Initialize filtered column to False
        if 'filtered' not in df.columns:
            df['filtered'] = False
      
        # Title filter
        if "title" in filters:
            pattern_include = '|'.join(preferences['title_include'])
            pattern_exclude = '|'.join(preferences['title_exclude'])
            title_filtered = (~df['title'].str.contains(pattern_include, case=False, na=False)) | \
                           (df['title'].str.contains(pattern_exclude, case=False, na=False))
            df.loc[title_filtered, 'filtered'] = True

        # Company filter
        if "company" in filters:
            pattern_company_exclude = '|'.join(preferences['company_exclude'])
            company_filtered = df['company'].str.contains(pattern_company_exclude, case=False, na=False)
            df.loc[company_filtered, 'filtered'] = True
        
        # Max age filter
        if "max_age" in filters:
            age_filtered = df['date'] < datetime.now() - timedelta(days=preferences['max_age'])
            df.loc[age_filtered, 'filtered'] = True

        # Language filter
        if "languages" in filters:
            df['language'] = df['description'].apply(safe_detect)
            language_filtered = ~df['language'].isin(preferences['languages'])
            df.loc[language_filtered, 'filtered'] = True
        
        # Description filter
        if "description" in filters:
            pattern_desc_words = '|'.join(preferences['desc_words'])
            desc_filtered = ~df['description'].str.contains(pattern_desc_words, case=False, na=False)
            df.loc[desc_filtered, 'filtered'] = True

        return df

    def remove_existing_jobs_in_database(self, df: pd.DataFrame, engine: ElasticSearchEngine, es_index: str):
        # Get jobs from database
        jobs_from_database = engine.search(query = {"query": {"match_all": {}}}, index = es_index)
        jobs_from_database_DataFrame = pd.DataFrame(jobs_from_database)
        # Filter jobs from database with the jobs in the DataFrame
        jobs_from_database_DataFrame = jobs_from_database_DataFrame[jobs_from_database_DataFrame.index.isin(df.index)]
        # Remove jobs from database from the DataFrame
        df = df[~df.index.isin(jobs_from_database_DataFrame.index)]
        return df

    @ExecutionTime
    def execute_scraper(self, preferences: dict):
        # Get job cards (one shot research)
        with BeautifulSoupEngine(self.bs_config, preferences) as bs_engine:
            job_cards = bs_engine.get_jobcards(preferences)

        # Insert jobs in a DataFrame
        jobs_df = pd.DataFrame(job_cards)
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

        self.logger.warning("No new jobs found")