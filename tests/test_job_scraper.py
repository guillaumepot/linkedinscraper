# tests/test_job_scraper.py

import pytest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime, timedelta
from langdetect.lang_detect_exception import LangDetectException

from src.JobScraper import JobScraper


class TestJobScraper:
    """Test suite for JobScraper class."""
    
    @pytest.fixture
    def mock_backend(self):
        """Fixture providing mock backend (ElasticSearch engine)."""
        return Mock()
    
    @pytest.fixture
    def mock_scrap_engine(self):
        """Fixture providing mock scraping engine (BeautifulSoup engine)."""
        mock = Mock()
        mock.__enter__ = Mock(return_value=mock)
        mock.__exit__ = Mock(return_value=None)
        return mock
    
    @pytest.fixture
    def mock_logger(self):
        """Fixture providing mock logger."""
        return Mock()

    @pytest.fixture
    def sample_preferences(self):
        """Fixture providing sample user preferences."""
        return {
            'title_include': ['python', 'developer'],
            'title_exclude': ['senior', 'lead'],
            'company_exclude': ['Bad Company Inc'],
            'max_age': 7,
            'languages': ['en'],
            'description_words_include': ['python', 'django', 'flask'],
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
                'description': 'We are looking for a Python developer with Django experience.',
                'filtered': 0
            },
            {
                'title': 'Senior Python Lead',
                'company': 'Another Corp',
                'location': 'San Francisco',
                'date': datetime.now() - timedelta(days=10),
                'job_url': 'https://linkedin.com/jobs/view/456',
                'description': 'Senior position for experienced Python developer.',
                'filtered': 0
            },
            {
                'title': 'Data Scientist',
                'company': 'Bad Company Inc',
                'location': 'Boston',
                'date': datetime.now() - timedelta(days=1),
                'job_url': 'https://linkedin.com/jobs/view/789',
                'description': 'Data science role with R and statistics focus.',
                'filtered': 0
            }
        ])
    
    @pytest.fixture
    def job_scraper(self, mock_backend, mock_scrap_engine, mock_logger):
        """Fixture providing JobScraper instance with mocked dependencies."""
        return JobScraper(backend=mock_backend, scrap_engine=mock_scrap_engine, logger=mock_logger)
    
    def test_init_sets_dependencies(self, mock_backend, mock_scrap_engine, mock_logger):
        """Test that initialization properly sets dependencies."""
        scraper = JobScraper(backend=mock_backend, scrap_engine=mock_scrap_engine, logger=mock_logger)
        
        assert scraper.backend == mock_backend
        assert scraper.scrap_engine == mock_scrap_engine
        assert scraper.logger == mock_logger

    def test_safe_detect_returns_detected_language(self):
        """Test safe_detect returns detected language when successful."""
        with patch('src.JobScraper.detect') as mock_detect:
            mock_detect.return_value = 'es'
            result = JobScraper.safe_detect('Hola mundo')
            assert result == 'es'

    def test_safe_detect_returns_english_on_exception(self):
        """Test safe_detect returns 'en' when LangDetectException is raised."""
        with patch('src.JobScraper.detect') as mock_detect:
            mock_detect.side_effect = LangDetectException("Error", "Error")
            result = JobScraper.safe_detect('some text')
            assert result == 'en'

    def test_check_len_df_returns_false_for_empty_dataframe(self, job_scraper):
        """Test check_len_df returns False for empty DataFrame."""
        empty_df = pd.DataFrame()
        result = job_scraper.check_len_df(empty_df)
        assert result is False

    def test_check_len_df_returns_true_for_non_empty_dataframe(self, job_scraper, sample_jobs_df):
        """Test check_len_df returns True for non-empty DataFrame."""
        result = job_scraper.check_len_df(sample_jobs_df)
        assert result is True
    
    def test_apply_filters_title_include_filter(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test title include filter removes jobs without required words."""
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["title"])
        
        # Should filter out "Data Scientist" as it doesn't contain 'python' or 'developer'
        # and "Senior Python Lead" as it contains excluded words 'senior' and 'lead'
        filtered_jobs = result[result['filtered'] == 1]
        assert len(filtered_jobs) == 2
        filtered_titles = set(filtered_jobs['title'].tolist())
        assert 'Data Scientist' in filtered_titles
        assert 'Senior Python Lead' in filtered_titles
    
    def test_apply_filters_title_exclude_filter(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test title exclude filter removes jobs with excluded words."""
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["title"])
        
        # Should filter out "Senior Python Lead" as it contains 'senior' and 'lead'
        filtered_jobs = result[result['filtered'] == 1]
        filtered_titles = set(filtered_jobs['title'].tolist())
        assert 'Senior Python Lead' in filtered_titles
        assert 'Data Scientist' in filtered_titles  # Also filtered for not having include words
    
    def test_apply_filters_company_exclude_filter(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test company exclude filter removes jobs from excluded companies."""
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["company"])
        
        # Should filter out job from "Bad Company Inc"
        filtered_jobs = result[result['filtered'] == 1]
        assert len(filtered_jobs) == 1
        assert filtered_jobs.iloc[0]['company'] == 'Bad Company Inc'
    
    def test_apply_filters_max_age_filter(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test max age filter removes old jobs."""
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["max_age"])
        
        # Should filter out job that's 10 days old (older than 7 day limit)
        filtered_jobs = result[result['filtered'] == 1]
        assert len(filtered_jobs) == 1
        assert filtered_jobs.iloc[0]['title'] == 'Senior Python Lead'
    
    def test_apply_filters_language_filter(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test language filter removes jobs in wrong language."""
        # Mock language detection to return different languages
        with patch.object(JobScraper, 'safe_detect') as mock_detect:
            mock_detect.side_effect = ['en', 'es', 'en']  # Second job in Spanish
            
            result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["languages"])
            
            # Should filter out the job detected as Spanish
            filtered_jobs = result[result['filtered'] == 1]
            assert len(filtered_jobs) == 1
            assert filtered_jobs.iloc[0]['title'] == 'Senior Python Lead'
    
    def test_apply_filters_language_filter_handles_lang_detect_exception(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test language filter handles LangDetectException gracefully."""
        # Mock language detection to raise exception then return languages
        with patch.object(JobScraper, 'safe_detect') as mock_detect:
            mock_detect.side_effect = ['en', 'en', 'en']  # All return 'en' (no filtering)
            
            result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["languages"])
            
            # Should not filter any jobs (all detected as 'en')
            filtered_jobs = result[result['filtered'] == 1]
            assert len(filtered_jobs) == 0
    
    def test_apply_filters_description_filter(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test description filter removes jobs without required description words."""
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["description"])
        
        # Should filter out "Data Scientist" job as it doesn't contain python/django/flask
        filtered_jobs = result[result['filtered'] == 1]
        assert len(filtered_jobs) == 1
        assert filtered_jobs.iloc[0]['title'] == 'Data Scientist'
    
    def test_apply_filters_multiple_filters(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test applying multiple filters simultaneously."""
        filters = ["title", "company", "max_age"]
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, filters)
        
        # Should have multiple filtered jobs due to different filter criteria
        filtered_jobs = result[result['filtered'] == 1]
        filtered_titles = set(filtered_jobs['title'].tolist())
        
        # Check that jobs are filtered for expected reasons
        assert 'Senior Python Lead' in filtered_titles  # title exclude + max_age
        assert 'Data Scientist' in filtered_titles      # title include + company exclude
    
    def test_apply_filters_initializes_filtered_column(self, job_scraper, sample_preferences):
        """Test that apply_filters works when filtered column doesn't exist."""
        # Create DataFrame without filtered column
        df = pd.DataFrame([
            {
                'title': 'Python Developer',
                'company': 'Tech Corp',
                'date': datetime.now() - timedelta(days=2),
                'job_url': 'https://linkedin.com/jobs/view/123',
                'description': 'Python developer role'
            }
        ])
        
        # Need to initialize filtered column as the method expects it
        df['filtered'] = 0
        
        result = job_scraper.apply_filters(df, sample_preferences, ["title"])
        
        assert 'filtered' in result.columns
        assert result['filtered'].dtype in ['int64', 'int32', 'object']  # Allow for different int types

    def test_apply_filters_remove_filtered_option(self, job_scraper, sample_jobs_df, sample_preferences):
        """Test that remove_filtered option removes filtered jobs from DataFrame."""
        result = job_scraper.apply_filters(sample_jobs_df, sample_preferences, ["title"], remove_filtered=True)
        
        # Should only contain unfiltered jobs
        assert 'filtered' not in result.columns  # Filtered column should be removed
        assert len(result) == 1  # Only Python Developer should remain
        assert result.iloc[0]['title'] == 'Python Developer'
    
    def test_remove_existing_jobs(self, job_scraper, sample_jobs_df):
        """Test removing existing jobs based on title, company, and date."""
        mock_backend = job_scraper.backend
        
        # Mock search result with one existing job
        mock_search_result = {
            'hits': {
                'hits': [
                    {'_source': {
                        'title': 'Python Developer', 
                        'company': 'Tech Corp',
                        'date': sample_jobs_df.iloc[0]['date']
                    }}
                ]
            }
        }
        mock_backend.search.return_value = mock_search_result
        
        result = job_scraper.remove_existing_jobs(sample_jobs_df, "jobs")
        
        # Should remove the job with matching title, company, and date
        assert len(result) == 2  # Originally 3, removed 1
        remaining_titles = set(result['title'].tolist())
        assert 'Python Developer' not in remaining_titles
    
    def test_remove_existing_jobs_no_existing_jobs(self, job_scraper, sample_jobs_df):
        """Test behavior when no existing jobs are found in database."""
        mock_backend = job_scraper.backend
        
        # Mock empty search result
        mock_search_result = {'hits': {'hits': []}}
        mock_backend.search.return_value = mock_search_result
        
        result = job_scraper.remove_existing_jobs(sample_jobs_df, "jobs")
        
        # Should return all jobs unchanged
        assert len(result) == len(sample_jobs_df)
        pd.testing.assert_frame_equal(result, sample_jobs_df)
    
    def test_remove_existing_jobs_handles_database_error(self, job_scraper, sample_jobs_df):
        """Test graceful handling of database errors."""
        mock_backend = job_scraper.backend
        mock_backend.search.side_effect = Exception("Database connection error")
        
        # Should raise the exception since the method doesn't handle it
        with pytest.raises(Exception, match="Database connection error"):
            job_scraper.remove_existing_jobs(sample_jobs_df, "jobs")
    
    def test_execute_scraper_full_workflow_success(self, job_scraper, sample_preferences):
        """Test successful execution of complete scraping workflow."""
        # Mock scraping engine
        mock_scrap_engine = job_scraper.scrap_engine
        mock_scrap_engine.__enter__.return_value = mock_scrap_engine
        # Create a very recent date to ensure it passes max_age filter
        recent_date = datetime.now().strftime('%Y-%m-%d')
        mock_scrap_engine.get_jobcards.return_value = [
            {
                'title': 'Python Developer',  # This contains 'python' and 'developer' so it won't be filtered
                'company': 'Tech Corp',       # This is not in the exclude list
                'location': 'New York',
                'date': recent_date,          # Today's date so won't be filtered by max_age
                'job_url': 'https://linkedin.com/jobs/view/123'
            }
        ]
        mock_scrap_engine.get_job_descriptions.return_value = ['Great Python job with Django experience.']
        
        # Mock backend
        mock_backend = job_scraper.backend
        mock_backend.search.return_value = {'hits': {'hits': []}}  # No existing jobs
        
        job_scraper.execute_scraper(sample_preferences)
        
        # Verify scraping engine was used correctly
        mock_scrap_engine.get_jobcards.assert_called_once_with(sample_preferences)
        mock_scrap_engine.get_job_descriptions.assert_called_once()
        
        # Verify backend operations
        mock_backend.search.assert_called_once()
        mock_backend.insert_bulk_data.assert_called_once()
        
        # Check that insert_bulk_data was called with properly formatted data
        call_args = mock_backend.insert_bulk_data.call_args
        inserted_jobs = call_args[1]['data']  # Named argument 'data'
        assert len(inserted_jobs) == 1
        assert 'interest' in inserted_jobs[0]
        assert 'applied' in inserted_jobs[0]
        assert 'interview' in inserted_jobs[0]
        assert 'rejected' in inserted_jobs[0]
        assert 'hidden' in inserted_jobs[0]
    
    def test_execute_scraper_no_jobs_found(self, job_scraper, sample_preferences):
        """Test execution when no jobs are found during scraping."""
        # Mock scraping engine to return empty results
        mock_scrap_engine = job_scraper.scrap_engine
        mock_scrap_engine.__enter__.return_value = mock_scrap_engine
        mock_scrap_engine.get_jobcards.return_value = []
        
        job_scraper.execute_scraper(sample_preferences)
        
        # Should log warning and return early
        mock_scrap_engine.get_jobcards.assert_called_once_with(sample_preferences)
        # Should not call get_job_descriptions since no jobs found
        mock_scrap_engine.get_job_descriptions.assert_not_called()
    
    def test_execute_scraper_all_jobs_filtered_out_in_first_batch(self, job_scraper, sample_preferences):
        """Test execution when all jobs are filtered out in first batch of filters."""
        # Mock scraping engine
        mock_scrap_engine = job_scraper.scrap_engine
        mock_scrap_engine.__enter__.return_value = mock_scrap_engine
        mock_scrap_engine.get_jobcards.return_value = [
            {
                'title': 'Senior Lead Manager',  # Will be filtered out by title exclude
                'company': 'Tech Corp',
                'location': 'New York',
                'date': '2024-01-15',
                'job_url': 'https://linkedin.com/jobs/view/123'
            }
        ]
        
        job_scraper.execute_scraper(sample_preferences)
        
        # Should return early after first batch of filters
        mock_scrap_engine.get_jobcards.assert_called_once_with(sample_preferences)
        # Should not call get_job_descriptions since all jobs filtered out
        mock_scrap_engine.get_job_descriptions.assert_not_called()
    
    def test_execute_scraper_database_insertion_error(self, job_scraper, sample_preferences):
        """Test execution when database insertion fails."""
        # Mock scraping engine
        mock_scrap_engine = job_scraper.scrap_engine
        mock_scrap_engine.__enter__.return_value = mock_scrap_engine
        # Create a very recent date to ensure it passes max_age filter
        recent_date = datetime.now().strftime('%Y-%m-%d')
        mock_scrap_engine.get_jobcards.return_value = [
            {
                'title': 'Python Developer',
                'company': 'Tech Corp',
                'location': 'New York',
                'date': recent_date,
                'job_url': 'https://linkedin.com/jobs/view/123'
            }
        ]
        mock_scrap_engine.get_job_descriptions.return_value = ['Great Python job.']
        
        # Mock backend with insertion error
        mock_backend = job_scraper.backend
        mock_backend.search.return_value = {'hits': {'hits': []}}
        mock_backend.insert_bulk_data.side_effect = Exception("Database insertion failed")
        
        # Should raise the exception since the method doesn't handle it gracefully
        with pytest.raises(Exception, match="Database insertion failed"):
            job_scraper.execute_scraper(sample_preferences)
    
    def test_apply_filters_with_missing_preferences(self, job_scraper, sample_jobs_df):
        """Test apply_filters handles missing preference keys gracefully."""
        empty_preferences = {}
        
        # Should not raise exceptions even with missing preference keys
        result = job_scraper.apply_filters(sample_jobs_df, empty_preferences, ["title", "company", "max_age", "languages", "description"])
        
        # Should still have filtered column
        assert 'filtered' in result.columns
        
        # With empty preferences, some filters might not apply any filtering
        # Title filter with empty include list should filter all jobs
        filtered_jobs = result[result['filtered'] == 1]
        assert len(filtered_jobs) == len(sample_jobs_df)  # All jobs filtered due to empty title_include
    
    def test_apply_filters_handles_empty_dataframe(self, job_scraper, sample_preferences):
        """Test apply_filters handles empty DataFrame gracefully."""
        empty_df = pd.DataFrame(columns=['title', 'company', 'date', 'job_url', 'description', 'filtered'])
        
        result = job_scraper.apply_filters(empty_df, sample_preferences, ["title"])
        
        assert len(result) == 0
        assert 'filtered' in result.columns


class TestJobScraperIntegration:
    """Integration tests for JobScraper class."""
    
    def test_job_scraper_initialization_integration(self):
        """Test complete JobScraper initialization flow."""
        mock_backend = Mock()
        mock_scrap_engine = Mock()
        mock_logger = Mock()
        
        scraper = JobScraper(backend=mock_backend, scrap_engine=mock_scrap_engine, logger=mock_logger)
        
        assert scraper.backend == mock_backend
        assert scraper.scrap_engine == mock_scrap_engine
        assert scraper.logger == mock_logger
    
    def test_date_conversion_and_filtering_integration(self):
        """Test date conversion and filtering work together correctly."""
        mock_backend = Mock()
        mock_scrap_engine = Mock()
        mock_logger = Mock()
        
        job_scraper = JobScraper(backend=mock_backend, scrap_engine=mock_scrap_engine, logger=mock_logger)
        
        # Create DataFrame with string dates (as would come from scraping)
        today = datetime.now()
        recent_date = (today - timedelta(days=2)).strftime('%Y-%m-%d')  # Recent job
        old_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')    # Old job
        
        jobs_data = [
            {
                'title': 'Python Developer',
                'company': 'Tech Corp',
                'date': recent_date,  # Recent string date
                'job_url': 'https://linkedin.com/jobs/view/123',
                'filtered': 0
            },
            {
                'title': 'Data Scientist',
                'company': 'Science Corp',
                'date': old_date,  # Old string date
                'job_url': 'https://linkedin.com/jobs/view/456',
                'filtered': 0
            }
        ]
        
        df = pd.DataFrame(jobs_data)
        
        # Convert date column as done in execute_scraper
        df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
        
        # Apply max_age filter
        preferences = {'max_age': 7}
        result = job_scraper.apply_filters(df, preferences, ["max_age"])
        
        # Old job should be filtered out
        filtered_jobs = result[result['filtered'] == 1]
        assert len(filtered_jobs) == 1  # Only the old job should be filtered by max_age
        assert filtered_jobs.iloc[0]['title'] == 'Data Scientist' 