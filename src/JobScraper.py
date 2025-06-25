# src/job_scraping/JobScraper.py

from datetime import datetime, timedelta
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
import pandas as pd

from src.utils.tools import ExecutionTime

class JobScraper:
    def __init__(self, backend, scrap_engine, logger):
        self.logger = logger
        self.backend = backend
        self.scrap_engine = scrap_engine
    

    @staticmethod
    def safe_detect(text: str) -> str:
        """
        Safe detect the language of a text.
        If the language is not detected, return 'en'.
        Args:
            text (str): The text to detect the language of.
        Returns:
            str: The detected language.
        """
        try:
            return detect(text)
        except LangDetectException:
            return 'en'


    def check_len_df(self, df: pd.DataFrame) -> bool:
        """
        Check if the DataFrame is empty.
        Args:
            df (pd.DataFrame): The DataFrame to check.
        Returns:
            bool: True if the DataFrame is not empty, False otherwise.
        """
        if len(df) == 0 or df.empty:
            self.logger.warning("No jobs found from scraping or all jobs were filtered out")
            return False
        return True


    def apply_filters(self, df: pd.DataFrame, preferences: dict, filters:list, remove_filtered: bool = False) -> pd.DataFrame:
        """
        Apply filters to the DataFrame.
        Args:
            df (pd.DataFrame): The DataFrame to apply filters to.
            preferences (dict): The preferences to apply filters to.
            filters (list): The filters to apply.
            remove_filtered (bool): Whether to remove filtered jobs from the DataFrame.
        Returns:
            pd.DataFrame: The DataFrame with filters applied.
        """
        # Title filter
          # Job titles must contain at least one of the words in the title_include corresponding to the preferences to avoid filtering
          # Job titles must not contain any of the words in the title_exclude corresponding to the preferences to avoid filtering
          # Excluded words are more important than included words
        if "title" in filters:
            title_include = preferences.get('title_include', [])
            title_exclude = preferences.get('title_exclude', [])

            for idx, row in df.iterrows():
                title = str(row['title']).lower()
                title_has_include = any(word.lower() in title for word in title_include)
                title_has_exclude = any(word.lower() in title for word in title_exclude)

                if not title_has_include or title_has_exclude:
                    self.logger.debug(f"Job title {title} filtered out by filter 'title'")
                    df.at[idx, 'filtered'] = 1

        # Company filter
            # Exclude companies specified in the company_exclude field
        if "company" in filters:
            company_exclude = preferences.get('company_exclude', [])
            for idx, row in df.iterrows():
                company = str(row['company'])
                if company in company_exclude:
                    self.logger.debug(f"Job company {company} filtered out by filter 'company'")
                    df.at[idx, 'filtered'] = 1

        # Max age filter
            # Filter if the job is older than the max age corresponding to the preferences
        if "max_age" in filters:
            max_age_days = preferences.get('max_age', 7)
            cutoff_date = datetime.now() - timedelta(days = max_age_days)
            for idx, row in df.iterrows():
                if pd.notna(row['date']) and row['date'] < cutoff_date:
                    self.logger.debug(f"Job date {row['date']} filtered out by filter 'max_age'")
                    df.at[idx, 'filtered'] = 1
        

        # Language filter
            # Filter if the job description is not in the languages corresponding to the preferences
        if "languages" in filters:
            allowed_languages = preferences.get('languages', ['en'])
            for idx, row in df.iterrows():
                description_value = row.get('description')
                if description_value is not None:
                    try:
                        description = str(description_value)
                        if description.strip() and description.lower() not in ['nan', 'none', '']:
                            detected_lang = self.safe_detect(description)
                            if detected_lang not in allowed_languages:
                                self.logger.debug("Job description filtered out by filter 'languages'")
                                df.at[idx, 'filtered'] = 1
                    except (ValueError, TypeError):
                        self.logger.debug("Job description filtered out by filter 'languages' (invalid data)")
                        df.at[idx, 'filtered'] = 1


        # Description filter
            # Filter if the job description does not contain any of the words in the description_words_include corresponding to the preferences
        if "description" in filters:
            description_words_include = preferences.get('description_words_include', [])
            for idx, row in df.iterrows():
                description_value = row.get('description')
                if description_value is not None:
                    try:
                        description = str(description_value)
                        if description.strip() and description.lower() not in ['nan', 'none', '']:
                            has_required_word = any(word.lower() in description.lower() for word in description_words_include)
                            if not has_required_word:
                                self.logger.debug("Job description filtered out by filter 'description'")
                                df.at[idx, 'filtered'] = 1
                    except (ValueError, TypeError):
                        self.logger.debug("Job description filtered out by filter 'description' (invalid data)")
                        df.at[idx, 'filtered'] = 1


        # Remove filtered jobs from DataFrame
        if remove_filtered:
            df = df[df['filtered'] == 0].copy()
            df = df.drop(columns = ['filtered'])

        # Return
        return df


    def remove_existing_jobs(self, df: pd.DataFrame, es_index: str) -> pd.DataFrame:
        """
        Remove existing jobs from the DataFrame.
        Args:
            df (pd.DataFrame): The DataFrame to remove existing jobs from.
            es_index (str): The index to remove existing jobs from.
        Returns:
            pd.DataFrame: The DataFrame with existing jobs removed.
        """
        # Query to find already existing jobs (based on title, company and date)
        should_clauses = []
        for _, job in df.iterrows():
            should_clauses.append({
                "bool": {
                    "must": [
                        {"match": {"title": job['title']}},
                        {"match": {"company": job['company']}},
                        {"match": {"date": job['date']}}
                    ]
                }
            })
        
        if should_clauses:
            query = {
                "query": {
                    "bool": {
                        "should": should_clauses,
                        "minimum_should_match": 1
                    }
                },
                "size": 10000
            }
        
        else:
            return df

        existing_results = self.backend.search(query = query, index = es_index)
        existing_combinations = set()

        if existing_results.get('hits', {}).get('hits'):
            for hit in existing_results['hits']['hits']:
                source = hit['_source']
                existing_combinations.add((source.get('title', ''), source.get('company', ''), source.get('date', '')))
        
        # Filter out jobs that already exist (same title, company and date)
        df = df[~df.apply(lambda row: (row['title'], row['company'], row['date']) in existing_combinations, axis=1)]

        return df

    
    @ExecutionTime
    def execute_scraper(self, preferences: dict) -> None:
        # Get job cards (one shot research)
        self.logger.info("Starting job scraping")
        with self.scrap_engine as bs_engine:
            job_cards = bs_engine.get_jobcards(preferences)

        # Insert jobs in a DataFrame
        self.logger.debug("Inserting jobs in a DataFrame")
        jobs_df = pd.DataFrame(job_cards)
        self.logger.debug(f"Jobs DataFrame: {jobs_df.head()}")

        # DF check length checkpoint
        if not self.check_len_df(jobs_df):
            return

        # Continue if jobs found
        self.logger.debug(f"Found {len(jobs_df)} job cards from scraping")
        # Convert date to datetime
        jobs_df['date'] = pd.to_datetime(jobs_df['date'], format = '%Y-%m-%d', errors = 'coerce')
        # Create col for filtered jobs (False by default)
        jobs_df['filtered'] = 0

        # Apply a first batch of filters to avoid duplicates and scraping job descriptions that are already in the database
        self.logger.debug("Applying first batch of filters to avoid duplicates and scraping job descriptions that are already in the database")
        jobs_df = jobs_df.drop_duplicates(subset = ['title', 'company'], keep = 'first')
        jobs_df = jobs_df.drop_duplicates(subset = ['job_url'], keep = 'first')
        jobs_df = self.apply_filters(jobs_df,
                                     preferences,
                                     filters = ["title", "company", "max_age"],
                                     remove_filtered = True)
        
        # DF check length checkpoint
        if not self.check_len_df(jobs_df):
            return
        
        # Remove existing jobs from the DataFrame
        self.logger.debug("Removing existing jobs from the DataFrame")
        jobs_df = self.remove_existing_jobs(jobs_df,
                                            es_index = "jobs")
        
        
        # DF check length checkpoint
        if not self.check_len_df(jobs_df):
            return

        # Request job descriptions
        self.logger.debug("Requesting job descriptions")
        with self.scrap_engine as bs_engine:
            job_descriptions = bs_engine.get_job_descriptions([url for url in jobs_df['job_url']])

        jobs_df['description'] = job_descriptions


        # Apply filters: language, description
        self.logger.debug("Applying filters: language, description")
        filters = ["languages", "description"]
        jobs_df = self.apply_filters(jobs_df,
                                     preferences,
                                     filters)
        
        # Add additional columns: interest, applied, interview, rejected, hidden
        self.logger.debug("Adding additional columns: interest, applied, interview, rejected, hidden")
        jobs_df['interest'] = 0
        jobs_df['applied'] = 0
        jobs_df['interview'] = 0
        jobs_df['rejected'] = 0
        jobs_df['hidden'] = 0



        # Insert jobs into the database
        self.logger.debug("Inserting jobs into the database")
        self.backend.insert_bulk_data(data = jobs_df.to_dict(orient = 'records'),
                                      index = "jobs")

        self.logger.info(f"Successfully inserted {len(jobs_df)} new jobs into database")
        return