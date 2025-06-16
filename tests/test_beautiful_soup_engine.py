# tests/test_beautiful_soup_engine.py

import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup
import requests
from src.job_scraping.BeautifulSoupEngine import BeautifulSoupEngine


class TestBeautifulSoupEngine:
    """Test suite for BeautifulSoupEngine class."""
    
    @pytest.fixture
    def sample_config(self):
        """Fixture providing sample configuration."""
        return {
            'max_retry': 3,
            'retry_delay': 1,
            'request_timeout': 30,
            'headers': {'User-Agent': 'test-agent'},
            'proxies': [],
            'rounds': 1,
            'pages_to_scrape': 2,
            'max_age': 'r86400'
        }
    
    @pytest.fixture
    def sample_preferences(self):
        """Fixture providing sample user preferences."""
        return {
            'search_queries': [
                {
                    'keywords': 'python developer',
                    'location': 'New York',
                    'f_WT': '2'  # Remote work
                },
                {
                    'keywords': 'data scientist',
                    'location': 'San Francisco',
                    'f_WT': '1'  # On-site work
                }
            ]
        }
    
    @pytest.fixture
    def engine(self, sample_config, sample_preferences):
        """Fixture providing initialized BeautifulSoupEngine instance."""
        return BeautifulSoupEngine(sample_config, sample_preferences)
    
    def test_init_creates_logger_and_stores_config(self, sample_config, sample_preferences):
        """Test that initialization properly sets up logger and stores config."""
        with patch('src.job_scraping.BeautifulSoupEngine.LoggerManager') as mock_logger_manager:
            mock_logger = Mock()
            mock_logger_manager.configure_logger.return_value = mock_logger
            
            engine = BeautifulSoupEngine(sample_config, sample_preferences)
            
            assert engine.config == sample_config
            assert engine.logger == mock_logger
            mock_logger_manager.configure_logger.assert_called_once_with(
                name='BeautifulSoupEngine', 
                verbose=True
            )
    
    def test_context_manager_enter_returns_self(self, engine):
        """Test that context manager __enter__ returns the engine instance."""
        result = engine.__enter__()
        assert result is engine
    
    def test_context_manager_exit_calls_close(self, engine):
        """Test that context manager __exit__ calls close method."""
        with patch.object(engine, 'close') as mock_close:
            engine.__exit__(None, None, None)
            mock_close.assert_called_once()
    
    def test_close_closes_session_if_exists(self, engine):
        """Test that close method closes session if it exists."""
        mock_session = Mock()
        engine.session = mock_session
        
        engine.close()
        
        mock_session.close.assert_called_once()
    
    def test_close_handles_no_session_gracefully(self, engine):
        """Test that close method handles missing session gracefully."""
        # Should not raise an exception
        engine.close()
    
    def test_unload_soup_sets_soup_to_none(self, engine):
        """Test that unload_soup clears the soup object."""
        engine.soup = Mock()
        engine.unload_soup()
        assert engine.soup is None
    
    @patch('src.job_scraping.BeautifulSoupEngine.requests.get')
    @patch('src.job_scraping.BeautifulSoupEngine.bs')
    def test_get_with_retry_success_on_first_attempt(self, mock_bs, mock_get, engine):
        """Test successful request on first attempt."""
        url = "https://example.com"
        mock_response = Mock()
        mock_response.text = "<html>test</html>"
        mock_get.return_value = mock_response
        mock_soup = Mock()
        mock_bs.return_value = mock_soup
        
        result = engine.get_with_retry(url)
        
        assert result == mock_soup
        mock_get.assert_called_once_with(
            url,
            proxies=None,
            headers=engine.config['headers'],
            timeout=engine.config['request_timeout']
        )
        mock_response.raise_for_status.assert_called_once()
        mock_bs.assert_called_once_with("<html>test</html>", 'html.parser')
    
    @patch('src.job_scraping.BeautifulSoupEngine.requests.get')
    @patch('src.job_scraping.BeautifulSoupEngine.time.sleep')
    def test_get_with_retry_handles_timeout_with_retry(self, mock_sleep, mock_get, engine):
        """Test retry logic on timeout exception."""
        url = "https://example.com"
        mock_get.side_effect = [requests.exceptions.Timeout(), requests.exceptions.Timeout(), requests.exceptions.Timeout()]
        
        result = engine.get_with_retry(url)
        
        assert result is None
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep called between retries
        mock_sleep.assert_called_with(engine.config['retry_delay'])
    
    @patch('src.job_scraping.BeautifulSoupEngine.requests.get')
    def test_get_with_retry_handles_unexpected_error(self, mock_get, engine):
        """Test handling of unexpected errors."""
        url = "https://example.com"
        mock_get.side_effect = Exception("Unexpected error")
        
        result = engine.get_with_retry(url)
        
        assert result is None
        mock_get.assert_called_once()
    
    @patch('src.job_scraping.BeautifulSoupEngine.requests.get')
    def test_get_with_retry_uses_proxies_when_configured(self, mock_get, engine):
        """Test that proxies are used when configured."""
        engine.config['proxies'] = ['http://proxy1.com:8080']
        url = "https://example.com"
        mock_response = Mock()
        mock_response.text = "<html>test</html>"
        mock_get.return_value = mock_response
        
        with patch('src.job_scraping.BeautifulSoupEngine.bs'):
            engine.get_with_retry(url)
        
        mock_get.assert_called_once_with(
            url,
            proxies=['http://proxy1.com:8080'],
            headers=engine.config['headers'],
            timeout=engine.config['request_timeout']
        )
    
    def test_cook_soup_job_cards_success(self, engine):
        """Test successful parsing of job cards from soup."""
        html_content = """
        <div data-entity-urn="urn:li:fsd_jobPosting:123456">
            <div class="base-search-card__info">
                <h3>Software Engineer</h3>
                <a class="hidden-nested-link">Tech Company</a>
                <span class="job-search-card__location">New York, NY</span>
                <time class="job-search-card__listdate" datetime="2024-01-15"></time>
            </div>
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = engine.cook_soup(soup, 'job_cards')
        
        expected = [{
            'title': 'Software Engineer',
            'company': 'Tech Company',
            'location': 'New York, NY',
            'date': '2024-01-15',
            'job_url': 'https://www.linkedin.com/jobs/view/123456/'
        }]
        assert result == expected
    
    def test_cook_soup_job_cards_empty_page(self, engine):
        """Test handling of empty page with no job cards."""
        soup = BeautifulSoup("<html></html>", 'html.parser')
        
        result = engine.cook_soup(soup, 'job_cards')
        
        assert result == []
    
    def test_cook_soup_job_cards_handles_parsing_errors(self, engine):
        """Test handling of parsing errors in job cards."""
        html_content = """
        <div class="base-search-card__info">
            <!-- Missing required elements -->
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = engine.cook_soup(soup, 'job_cards')
        
        assert result == []
    
    def test_cook_soup_job_descriptions_success(self, engine):
        """Test successful parsing of job description."""
        html_content = """
        <div class="description__text description__text--rich">
            <p>We are looking for a <span>great</span> developer.</p>
            <ul>
                <li>Python experience</li>
                <li>Team player</li>
            </ul>
            <a href="#">Apply now</a>
        </div>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = engine.cook_soup(soup, 'job_descriptions')
        
        # Should remove spans and links, format list items
        assert "We are looking for a" in result
        assert "developer." in result
        assert "- Python experience" in result
        assert "- Team player" in result
        assert "Apply now" not in result
    
    def test_cook_soup_job_descriptions_no_description(self, engine):
        """Test handling when no job description is found."""
        soup = BeautifulSoup("<html></html>", 'html.parser')
        
        result = engine.cook_soup(soup, 'job_descriptions')
        
        assert result is None
    
    def test_cook_soup_invalid_type_raises_error(self, engine):
        """Test that invalid type parameter raises ValueError."""
        soup = BeautifulSoup("<html></html>", 'html.parser')
        
        with pytest.raises(ValueError, match="Invalid type: invalid"):
            engine.cook_soup(soup, 'invalid')
    
    def test_generate_urls_creates_correct_urls(self, engine, sample_preferences):
        """Test that generate_urls creates properly formatted LinkedIn URLs."""
        urls = engine.generate_urls(sample_preferences)
        
        # Should create URLs for each query and page
        expected_url_count = len(sample_preferences['search_queries']) * engine.config['pages_to_scrape'] * engine.config['rounds']
        assert len(urls) == expected_url_count
        
        # Check URL format
        for url in urls:
            assert url.startswith("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search")
            assert "keywords=" in url
            assert "location=" in url
            assert "f_WT=" in url
            assert f"f_TPR={engine.config['max_age']}" in url
    
    def test_generate_urls_url_encodes_parameters(self, engine):
        """Test that URL parameters are properly encoded."""
        preferences = {
            'search_queries': [{
                'keywords': 'python & data science',
                'location': 'New York, NY',
                'f_WT': '2'
            }]
        }
        
        urls = engine.generate_urls(preferences)
        
        # Should contain URL-encoded keywords and location
        assert "python%20%26%20data%20science" in urls[0]
        assert "New%20York%2C%20NY" in urls[0]
    
    @patch.object(BeautifulSoupEngine, 'get_with_retry')
    @patch.object(BeautifulSoupEngine, 'cook_soup')
    def test_process_url_job_cards_success(self, mock_cook_soup, mock_get_with_retry, engine):
        """Test successful processing of URL for job cards."""
        url = "https://example.com"
        mock_soup = Mock()
        mock_get_with_retry.return_value = mock_soup
        mock_cook_soup.return_value = [{'title': 'Test Job'}]
        
        result = engine.process_url(url, 'job_cards')
        
        assert result == [{'title': 'Test Job'}]
        mock_get_with_retry.assert_called_once_with(url)
        mock_cook_soup.assert_called_once_with(mock_soup, 'job_cards')
    
    @patch.object(BeautifulSoupEngine, 'get_with_retry')
    def test_process_url_returns_empty_list_on_failed_request(self, mock_get_with_retry, engine):
        """Test that process_url returns empty list when request fails."""
        mock_get_with_retry.return_value = None
        
        result = engine.process_url("https://example.com", 'job_cards')
        
        assert result == []
    
    def test_process_url_invalid_type_raises_error(self, engine):
        """Test that invalid type parameter raises ValueError."""
        with pytest.raises(ValueError, match="Invalid type: invalid"):
            engine.process_url("https://example.com", 'invalid')
    
    @patch.object(BeautifulSoupEngine, 'generate_urls')
    @patch.object(BeautifulSoupEngine, 'process_url')
    def test_get_jobcards_aggregates_results(self, mock_process_url, mock_generate_urls, engine, sample_preferences):
        """Test that get_jobcards properly aggregates results from all URLs."""
        mock_generate_urls.return_value = ["url1", "url2", "url3"]
        mock_process_url.side_effect = [
            [{'title': 'Job 1'}],
            [{'title': 'Job 2'}, {'title': 'Job 3'}],
            [{'title': 'Job 4'}]
        ]
        
        result = engine.get_jobcards(sample_preferences)
        
        expected = [
            {'title': 'Job 1'},
            {'title': 'Job 2'},
            {'title': 'Job 3'},
            {'title': 'Job 4'}
        ]
        assert result == expected
        mock_generate_urls.assert_called_once_with(sample_preferences)
        assert mock_process_url.call_count == 3
    
    @patch.object(BeautifulSoupEngine, 'process_url')
    def test_get_job_descriptions_processes_all_urls(self, mock_process_url, engine):
        """Test that get_job_descriptions processes all provided URLs."""
        urls = ["url1", "url2", "url3"]
        mock_process_url.side_effect = ["Description 1", "Description 2", "Description 3"]
        
        result = engine.get_job_descriptions(urls)
        
        assert result == ["Description 1", "Description 2", "Description 3"]
        assert mock_process_url.call_count == 3
        for i, url in enumerate(urls):
            mock_process_url.assert_any_call(url, 'job_descriptions')


class TestBeautifulSoupEngineIntegration:
    """Integration tests for BeautifulSoupEngine."""
    
    @pytest.fixture
    def engine_config(self):
        """Configuration for integration tests."""
        return {
            'max_retry': 2,
            'retry_delay': 0.1,
            'request_timeout': 5,
            'headers': {'User-Agent': 'test-agent'},
            'proxies': [],
            'rounds': 1,
            'pages_to_scrape': 1,
            'max_age': 'r86400'
        }
    
    def test_engine_as_context_manager(self, engine_config):
        """Test that engine works properly as a context manager."""
        with patch('src.job_scraping.BeautifulSoupEngine.LoggerManager'):
            with BeautifulSoupEngine(engine_config, {}) as engine:
                assert engine is not None
                assert hasattr(engine, 'config')
                assert hasattr(engine, 'logger')
    
    @patch('src.job_scraping.BeautifulSoupEngine.requests.get')
    def test_full_job_card_extraction_flow(self, mock_get, engine_config):
        """Test the complete flow of extracting job cards."""
        # Mock HTML response that resembles LinkedIn structure
        mock_html = """
        <html>
            <div class="base-search-card__info">
                <h3>Senior Python Developer</h3>
                <a class="hidden-nested-link">Amazing Tech Co</a>
                <span class="job-search-card__location">Remote</span>
                <time class="job-search-card__listdate" datetime="2024-01-20"></time>
            </div>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = mock_html
        mock_get.return_value = mock_response
        
        preferences = {
            'search_queries': [{
                'keywords': 'python',
                'location': 'remote',
                'f_WT': '2'
            }]
        }
        
        with patch('src.job_scraping.BeautifulSoupEngine.LoggerManager'):
            engine = BeautifulSoupEngine(engine_config, preferences)
            
            # Mock the parent element for data-entity-urn  
            with patch('src.job_scraping.BeautifulSoupEngine.bs') as mock_bs:
                mock_html_with_parent = """
                <html>
                    <div data-entity-urn="urn:li:fsd_jobPosting:987654">
                        <div class="base-search-card__info">
                            <h3>Senior Python Developer</h3>
                            <a class="hidden-nested-link">Amazing Tech Co</a>
                            <span class="job-search-card__location">Remote</span>
                            <time class="job-search-card__listdate" datetime="2024-01-20"></time>
                        </div>
                    </div>
                </html>
                """
                mock_soup = BeautifulSoup(mock_html_with_parent, 'html.parser')
                mock_bs.return_value = mock_soup
                
                results = engine.get_jobcards(preferences)
                
                assert len(results) == 1
                job = results[0]
                assert job['title'] == 'Senior Python Developer'
                assert job['company'] == 'Amazing Tech Co'
                assert job['location'] == 'Remote'
                assert job['date'] == '2024-01-20'
                assert job['job_url'] == 'https://www.linkedin.com/jobs/view/987654/' 