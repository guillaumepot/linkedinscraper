# tests/test_job_scraper.py

import pytest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime, timedelta
from langdetect.lang_detect_exception import LangDetectException

from src.job_scraping.JobScraper import JobScraper


class TestJobScraper:
    """Test suite for JobScraper class."""
    
    @pytest.fixture
    def mock_config(self):
        """Fixture providing mock configuration."""
        return {
            'BeautifulSoupEngine': {
                'max_retry': 3,
                'retry_delay': 1,
                'request_timeout': 30,
                'headers': {'User-Agent': 'test-agent'},
                'proxies': [],
                'rounds': 1,
                'pages_to_scrape': 2,
                'max_age': 'r86400'
            },
            'ElasticsearchEngine': {
                'host': 'localhost',
                'port': 9200,
                'timeout': 30
            }
        }
    
    @pytest.fixture
    def sample_preferences(self):
        """Fixture providing sample user preferences."""
        return {
            'title_include': ['python', 'developer'],
            'title_exclude': ['senior', 'lead'],
            'company_exclude': ['Bad Company Inc'],
            'max_age': 7,
            'languages': ['en'],
            'desc_words': ['python', 'django', 'flask'],
            'search_queries': [
                {
                    'keywords': 'python developer',
                    'location': 'New York',
                    'f_WT': '2'
                }
            ]
        }
    
    @pytest.fixture
    def sample_jobs_df(self):
        """Fixture providing sample jobs DataFrame."""
        return pd.DataFrame([
            {
                'title': 'Python Developer',
                'company': 'Tech Corp',
                'location': 'New York',
                'date': datetime.now() - timedelta(days=2),
                'job_url': 'https://linkedin.com/jobs/view/123',
                'description': 'We are looking for a Python developer with Django experience.'
            },
            {
                'title': 'Senior Python Lead',
                'company': 'Another Corp',
                'location': 'San Francisco',
                'date': datetime.now() - timedelta(days=10),
                'job_url': 'https://linkedin.com/jobs/view/456',
                'description': 'Senior position for experienced Python developer.'
            },
            {
                'title': 'Data Scientist',
                'company': 'Bad Company Inc',
                'location': 'Boston',
                'date': datetime.now() - timedelta(days=1),
                'job_url': 'https://linkedin.com/jobs/view/789',
                'description': 'Data science role with R and statistics focus.'
            }
        ])
    
    @pytest.fixture
    def job_scraper(self, mock_config):
        """Fixture providing JobScraper instance with mocked dependencies."""
        with patch('src.job_scraping.JobScraper.load_configuration') as mock_load_config, \
             patch('src.job_scraping.JobScraper.LoggerManager') as mock_logger_manager:
            
            mock_load_config.return_value = mock_config
            mock_logger = Mock()
            mock_logger_manager.configure_logger.return_value = mock_logger
            
            scraper = JobScraper()
            return scraper
    
    def test_init_loads_config_and_creates_logger(self, mock_config):
        """Test that initialization properly loads config and creates logger."""
        with patch('src.job_scraping.JobScraper.load_configuration') as mock_load_config, \
             patch('src.job_scraping.JobScraper.LoggerManager') as mock_logger_manager:
            
            mock_load_config.return_value = mock_config
            mock_logger = Mock()
            mock_logger_manager.configure_logger.return_value = mock_logger
            
            scraper = JobScraper()
            
            assert scraper.config == mock_config
            assert scraper.bs_config == mock_config['BeautifulSoupEngine']
            assert scraper.es_config == mock_config['ElasticsearchEngine']
            assert scraper.logger == mock_logger
            
            mock_load_config.assert_called_once_with('src/job_scraping/config.json', type='json')
            mock_logger_manager.configure_logger.assert_called_once_with(name='JobScraper', verbose=True)
    
    def test_apply_filters_title_include_filter(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test title include filter removes jobs without required words."""
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["title"])
        
        # Should filter out "Data Scientist" as it doesn't contain 'python' or 'developer'
        # and "Senior Python Lead" as it contains excluded words 'senior' and 'lead'
        filtered_jobs = result[result['filtered']]
        assert len(filtered_jobs) == 2
        filtered_titles = set(filtered_jobs['title'].tolist())
        assert 'Data Scientist' in filtered_titles
        assert 'Senior Python Lead' in filtered_titles
    
    def test_apply_filters_title_exclude_filter(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test title exclude filter removes jobs with excluded words."""
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["title"])
        
        # Should filter out "Senior Python Lead" as it contains 'senior' and 'lead'
        filtered_jobs = result[result['filtered']]
        filtered_titles = set(filtered_jobs['title'].tolist())
        assert 'Senior Python Lead' in filtered_titles
        assert 'Data Scientist' in filtered_titles  # Also filtered for not having include words
    
    def test_apply_filters_company_exclude_filter(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test company exclude filter removes jobs from excluded companies."""
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["company"])
        
        # Should filter out job from "Bad Company Inc"
        filtered_jobs = result[result['filtered']]
        assert len(filtered_jobs) == 1
        assert filtered_jobs.iloc[0]['company'] == 'Bad Company Inc'
    
    def test_apply_filters_max_age_filter(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test max age filter removes old jobs."""
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["max_age"])
        
        # Should filter out job that's 10 days old (older than 7 day limit)
        filtered_jobs = result[result['filtered']]
        assert len(filtered_jobs) == 1
        assert filtered_jobs.iloc[0]['title'] == 'Senior Python Lead'
    
    @patch('src.job_scraping.JobScraper.detect')
    def test_apply_filters_language_filter(self, mock_detect, job_scraper, sample_jobs_df, sample_preferences):
        """Test language filter removes jobs in wrong language."""
        # Mock language detection to return different languages
        mock_detect.side_effect = ['en', 'es', 'en']  # Second job in Spanish
        
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["languages"])
        
        # Should filter out the job detected as Spanish
        filtered_jobs = result[result['filtered']]
        assert len(filtered_jobs) == 1
        assert filtered_jobs.iloc[0]['title'] == 'Senior Python Lead'
    
    @patch('src.job_scraping.JobScraper.detect')
    def test_apply_filters_language_filter_handles_lang_detect_exception(self, mock_detect, job_scraper, sample_jobs_df, sample_preferences):
        """Test language filter handles LangDetectException gracefully."""
        # Mock language detection to raise exception then return languages
        mock_detect.side_effect = [LangDetectException("Error", "Error"), 'en', 'en']
        
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["languages"])
        
        # Should not filter any jobs (exception defaults to 'en')
        filtered_jobs = result[result['filtered']]
        assert len(filtered_jobs) == 0
    
    def test_apply_filters_description_filter(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test description filter removes jobs without required description words."""
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["description"])
        
        # Should filter out "Data Scientist" job as it doesn't contain python/django/flask
        filtered_jobs = result[result['filtered']]
        assert len(filtered_jobs) == 1
        assert filtered_jobs.iloc[0]['title'] == 'Data Scientist'
    
    def test_apply_filters_multiple_filters(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test applying multiple filters simultaneously."""
        filters = ["title", "company", "max_age"]
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, filters)
        
        # Should have multiple filtered jobs due to different filter criteria
        filtered_jobs = result[result['filtered']]
        filtered_titles = set(filtered_jobs['title'].tolist())
        
        # Check that jobs are filtered for expected reasons
        assert 'Senior Python Lead' in filtered_titles  # title exclude + max_age
        assert 'Data Scientist' in filtered_titles      # title include + company exclude
    
    def test_apply_filters_initializes_filtered_column(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test that apply_filters initializes filtered column if it doesn't exist."""
        # Remove filtered column if it exists
        if 'filtered' in sample_jobs_df.columns:
            sample_jobs_df = sample_jobs_df.drop(columns=['filtered'])
        
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["title"])
        
        assert 'filtered' in result.columns
        assert result['filtered'].dtype == bool
    
    def test_remove_existing_jobs_by_url(self, job_scraper, sample_jobs_df):
        """Test removing existing jobs based on job_url."""
        mock_engine = Mock()
        
        # Mock search result with one existing job URL
        mock_search_result = {
            'hits': {
                'hits': [
                    {'_source': {'job_url': 'https://linkedin.com/jobs/view/123', 'title': 'Existing Job'}}
                ]
            }
        }
        mock_engine.search.return_value = mock_search_result
        
        result = job_scraper.remove_existing_jobs_in_database(sample_jobs_df, mock_engine, "jobs")
        
        # Should remove the job with matching URL
        assert len(result) == 2  # Originally 3, removed 1
        remaining_urls = set(result['job_url'].tolist())
        assert 'https://linkedin.com/jobs/view/123' not in remaining_urls
    
    def test_remove_existing_jobs_by_title_company(self, job_scraper, sample_jobs_df):
        """Test removing existing jobs based on title+company combination."""
        mock_engine = Mock()
        
        # Mock search result without job_url column
        mock_search_result = {
            'hits': {
                'hits': [
                    {'_source': {'title': 'Python Developer', 'company': 'Tech Corp'}}
                ]
            }
        }
        mock_engine.search.return_value = mock_search_result
        
        # Remove job_url from sample data to trigger title+company logic
        sample_df_no_url = sample_jobs_df.drop(columns=['job_url'])
        
        result = job_scraper.remove_existing_jobs_in_database(sample_df_no_url, mock_engine, "jobs")
        
        # Should remove the job with matching title+company
        assert len(result) == 2  # Originally 3, removed 1
        remaining_jobs = result[['title', 'company']].values.tolist()
        assert ['Python Developer', 'Tech Corp'] not in remaining_jobs
    
    def test_remove_existing_jobs_no_existing_jobs(self, job_scraper, sample_jobs_df):
        """Test behavior when no existing jobs are found in database."""
        mock_engine = Mock()
        
        # Mock empty search result
        mock_search_result = {'hits': {'hits': []}}
        mock_engine.search.return_value = mock_search_result
        
        result = job_scraper.remove_existing_jobs_in_database(sample_jobs_df, mock_engine, "jobs")
        
        # Should return all jobs unchanged
        assert len(result) == len(sample_jobs_df)
        pd.testing.assert_frame_equal(result, sample_jobs_df)
    
    def test_remove_existing_jobs_handles_database_error(self, job_scraper, sample_jobs_df):
        """Test graceful handling of database errors."""
        mock_engine = Mock()
        mock_engine.search.side_effect = Exception("Database connection error")
        
        result = job_scraper.remove_existing_jobs_in_database(sample_jobs_df, mock_engine, "jobs")
        
        # Should return all jobs unchanged when error occurs
        assert len(result) == len(sample_jobs_df)
        pd.testing.assert_frame_equal(result, sample_jobs_df)
    
    @patch('src.job_scraping.JobScraper.BeautifulSoupEngine')
    @patch('src.job_scraping.JobScraper.ElasticSearchEngine')
    def test_execute_scraper_full_workflow_success(self, mock_es_engine_class, mock_bs_engine_class, job_scraper, sample_preferences):
        """Test successful execution of complete scraping workflow."""
        # Mock BeautifulSoup engine
        mock_bs_engine = Mock()
        mock_bs_engine_class.return_value.__enter__.return_value = mock_bs_engine
        mock_bs_engine.get_jobcards.return_value = [
            {
                'title': 'Python Developer',
                'company': 'Tech Corp',
                'location': 'New York',
                'date': '2024-01-15',
                'job_url': 'https://linkedin.com/jobs/view/123'
            }
        ]
        mock_bs_engine.get_job_descriptions.return_value = ['Great Python job with Django experience.']
        
        # Mock Elasticsearch engine
        mock_es_engine = Mock()
        mock_es_engine_class.return_value.__enter__.return_value = mock_es_engine
        mock_es_engine.search.return_value = {'hits': {'hits': []}}  # No existing jobs
        
        job_scraper.execute_scraper(sample_preferences)
        
        # Verify BeautifulSoup engine was used correctly
        mock_bs_engine.get_jobcards.assert_called_once_with(sample_preferences)
        mock_bs_engine.get_job_descriptions.assert_called_once()
        
        # Verify Elasticsearch operations
        mock_es_engine.search.assert_called_once()
        mock_es_engine.insert_jobs.assert_called_once()
        
        # Check that insert_jobs was called with properly formatted data
        call_args = mock_es_engine.insert_jobs.call_args
        inserted_jobs = call_args[0][0]  # First positional argument
        assert len(inserted_jobs) == 1
        assert 'interest' in inserted_jobs[0]
        assert 'applied' in inserted_jobs[0]
        assert 'interview' in inserted_jobs[0]
        assert 'rejected' in inserted_jobs[0]
    
    @patch('src.job_scraping.JobScraper.BeautifulSoupEngine')
    def test_execute_scraper_no_jobs_found(self, mock_bs_engine_class, job_scraper, sample_preferences):
        """Test execution when no jobs are found during scraping."""
        # Mock BeautifulSoup engine to return empty results
        mock_bs_engine = Mock()
        mock_bs_engine_class.return_value.__enter__.return_value = mock_bs_engine
        mock_bs_engine.get_jobcards.return_value = []
        
        job_scraper.execute_scraper(sample_preferences)
        
        # Should log warning and return early
        mock_bs_engine.get_jobcards.assert_called_once_with(sample_preferences)
        # Should not call get_job_descriptions since no jobs found
        mock_bs_engine.get_job_descriptions.assert_not_called()
    
    @patch('src.job_scraping.JobScraper.BeautifulSoupEngine')
    @patch('src.job_scraping.JobScraper.ElasticSearchEngine')
    def test_execute_scraper_all_jobs_filtered_out(self, mock_es_engine_class, mock_bs_engine_class, job_scraper, sample_preferences):
        """Test execution when all jobs are filtered out."""
        # Mock BeautifulSoup engine
        mock_bs_engine = Mock()
        mock_bs_engine_class.return_value.__enter__.return_value = mock_bs_engine
        mock_bs_engine.get_jobcards.return_value = [
            {
                'title': 'Senior Lead Manager',  # Will be filtered out by title exclude
                'company': 'Tech Corp',
                'location': 'New York',
                'date': '2024-01-15',
                'job_url': 'https://linkedin.com/jobs/view/123'
            }
        ]
        
        # Mock Elasticsearch engine
        mock_es_engine = Mock()
        mock_es_engine_class.return_value.__enter__.return_value = mock_es_engine
        mock_es_engine.search.return_value = {'hits': {'hits': []}}
        
        job_scraper.execute_scraper(sample_preferences)
        
        # Note: The current implementation doesn't actually remove filtered jobs
        # It just marks them with filtered=True but still inserts them
        mock_bs_engine.get_job_descriptions.assert_called_once()
        mock_es_engine.insert_jobs.assert_called_once()
        
        # Verify that the job was marked as filtered
        call_args = mock_es_engine.insert_jobs.call_args
        inserted_jobs = call_args[0][0]  # First positional argument
        assert len(inserted_jobs) == 1
        assert inserted_jobs[0]['filtered']
    
    @patch('src.job_scraping.JobScraper.BeautifulSoupEngine')
    @patch('src.job_scraping.JobScraper.ElasticSearchEngine')
    def test_execute_scraper_database_insertion_error(self, mock_es_engine_class, mock_bs_engine_class, job_scraper, sample_preferences):
        """Test execution when database insertion fails."""
        # Mock BeautifulSoup engine
        mock_bs_engine = Mock()
        mock_bs_engine_class.return_value.__enter__.return_value = mock_bs_engine
        mock_bs_engine.get_jobcards.return_value = [
            {
                'title': 'Python Developer',
                'company': 'Tech Corp',
                'location': 'New York',
                'date': '2024-01-15',
                'job_url': 'https://linkedin.com/jobs/view/123'
            }
        ]
        mock_bs_engine.get_job_descriptions.return_value = ['Great Python job.']
        
        # Mock Elasticsearch engine with insertion error
        mock_es_engine = Mock()
        mock_es_engine_class.return_value.__enter__.return_value = mock_es_engine
        mock_es_engine.search.return_value = {'hits': {'hits': []}}
        mock_es_engine.insert_jobs.side_effect = Exception("Database insertion failed")
        
        # Should not raise exception, just log error
        job_scraper.execute_scraper(sample_preferences)
        
        mock_es_engine.insert_jobs.assert_called_once()
    
    def test_apply_filters_with_missing_preferences(self, job_scraper, sample_jobs_df):
        """Test apply_filters handles missing preference keys gracefully."""
        empty_preferences = {}
        
        # Should not raise exceptions even with missing preference keys
        result = job_scraper.apply_filters(sample_jobs_df, empty_preferences, ["title", "company", "max_age", "languages", "description"])
        
        # Should still have filtered column
        assert 'filtered' in result.columns
        
        # With empty preferences, some filters might not apply any filtering
        # Title filter with empty include list should filter all jobs
        filtered_jobs = result[result['filtered']]
        assert len(filtered_jobs) == len(sample_jobs_df)  # All jobs filtered due to empty title_include
    
    def test_apply_filters_handles_empty_dataframe(self, job_scraper, sample_preferences):
        """Test apply_filters handles empty DataFrame gracefully."""
        empty_df = pd.DataFrame(columns=['title', 'company', 'date', 'job_url', 'description'])
        
        result = job_scraper.apply_filters(empty_df, sample_preferences, ["title"])
        
        assert len(result) == 0
        assert 'filtered' in result.columns


class TestJobScraperIntegration:
    """Integration tests for JobScraper class."""
    
    @pytest.fixture
    def integration_config(self):
        """Configuration for integration tests."""
        return {
            'BeautifulSoupEngine': {
                'max_retry': 1,
                'retry_delay': 0.1,
                'request_timeout': 5,
                'headers': {'User-Agent': 'test-agent'},
                'proxies': [],
                'rounds': 1,
                'pages_to_scrape': 1,
                'max_age': 'r86400'
            },
            'ElasticsearchEngine': {
                'host': 'localhost',
                'port': 9200,
                'timeout': 5
            }
        }
    
    @patch('src.job_scraping.JobScraper.load_configuration')
    @patch('src.job_scraping.JobScraper.LoggerManager')
    def test_job_scraper_initialization_integration(self, mock_logger_manager, mock_load_config, integration_config):
        """Test complete JobScraper initialization flow."""
        mock_load_config.return_value = integration_config
        mock_logger = Mock()
        mock_logger_manager.configure_logger.return_value = mock_logger
        
        scraper = JobScraper()
        
        assert scraper.config == integration_config
        assert scraper.bs_config == integration_config['BeautifulSoupEngine']
        assert scraper.es_config == integration_config['ElasticsearchEngine']
        assert hasattr(scraper, 'logger')
    
    def test_date_conversion_and_filtering_integration(self, integration_config):
        """Test date conversion and filtering work together correctly."""
        with patch('src.job_scraping.JobScraper.load_configuration') as mock_load_config, \
             patch('src.job_scraping.JobScraper.LoggerManager') as mock_logger_manager:
            
            mock_load_config.return_value = integration_config
            mock_logger = Mock()
            mock_logger_manager.configure_logger.return_value = mock_logger
            
            job_scraper = JobScraper()
            
            # Create DataFrame with string dates (as would come from scraping)
            today = datetime.now()
            recent_date = (today - timedelta(days=2)).strftime('%Y-%m-%d')  # Recent job
            old_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')    # Old job
            
            jobs_data = [
                {
                    'title': 'Python Developer',
                    'company': 'Tech Corp',
                    'date': recent_date,  # Recent string date
                    'job_url': 'https://linkedin.com/jobs/view/123'
                },
                {
                    'title': 'Data Scientist',
                    'company': 'Science Corp',
                    'date': old_date,  # Old string date
                    'job_url': 'https://linkedin.com/jobs/view/456'
                }
            ]
            
            df = pd.DataFrame(jobs_data)
            
            # Convert date column as done in execute_scraper
            df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
            
            # Apply max_age filter
            preferences = {'max_age': 7}
            result = job_scraper.apply_filters(df, preferences, ["max_age"])
            
            # Old job should be filtered out
            filtered_jobs = result[result['filtered']]
            assert len(filtered_jobs) == 1  # Only the old job should be filtered by max_age
            assert filtered_jobs.iloc[0]['title'] == 'Data Scientist' 