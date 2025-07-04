# src/BeautifulSoupEngine.py

from bs4 import BeautifulSoup as bs
import requests
import time
from typing import List, Dict, Optional
from urllib.parse import quote

from src.utils.LoggerManager import LoggerManager



class BeautifulSoupEngine:
    """Engine for scraping LinkedIn job data using BeautifulSoup and requests."""
    
    def __init__(self, config: dict, preferences: dict):
        """Initialize the BeautifulSoup engine with configuration and preferences.
        
        Args:
            config (dict): Configuration dictionary containing settings like max_retry, headers, etc.
            preferences (dict): User preferences for job searching.
        """
        self.config = config
        self.preferences = preferences
        self.logger = LoggerManager.configure_logger(name='BeautifulSoupEngine')
        self.session = None

    def __enter__(self):
        """Context manager entry point."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit point."""
        self.close()

    def close(self):
        """Close any open resources like sessions."""
        if hasattr(self, 'session') and self.session:
            self.session.close()

    def unload_soup(self):
        """Clear the soup object from memory."""
        self.soup = None

    def get_with_retry(self, url: str) -> Optional[bs]:
        """Fetch a URL with retry logic and return BeautifulSoup object.
        
        Args:
            url (str): The URL to fetch.
            
        Returns:
            Optional[bs]: BeautifulSoup object if successful, None otherwise.
        """
        proxies = None
        if self.config.get('proxies') and len(self.config['proxies']) > 0:
            proxies = self.config['proxies']

        for attempt in range(self.config['max_retry']):
            try:
                response = requests.get(url,
                                        proxies = proxies,
                                        headers = self.config['headers'],
                                        timeout = self.config['request_timeout'])
                response.raise_for_status()
                return bs(response.text, 'html.parser')
            
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout occurred for URL: {url}, attempt {attempt + 1}/{self.config['max_retry']}")
                if attempt < self.config['max_retry'] - 1:
                    time.sleep(self.config['retry_delay'])

            except Exception as e:
                self.logger.error(f"Unexpected error for URL: {url}: {e}")
                break

    def cook_soup(self, soup: bs, type: str) -> List[Dict]:
        """Parse BeautifulSoup object and extract data based on type.
        
        Args:
            soup (bs): BeautifulSoup object to parse.
            type (str): Type of data to extract ('job_cards' or 'job_descriptions').
            
        Returns:
            List[Dict]: List of extracted job data or job description text.
        """
        if type == 'job_cards':
            joblist = []
            try:
                divs = soup.find_all('div', class_='base-search-card__info')
            except AttributeError:
                self.logger.warning("Empty page, no jobs found")
                return joblist
            
            for item in divs:
                try:
                    title_elem = item.find('h3')
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    company_elem = item.find('a', class_='hidden-nested-link')
                    location_elem = item.find('span', class_='job-search-card__location')
                    
                    parent_div = item.parent
                    if not parent_div or 'data-entity-urn' not in parent_div.attrs:
                        continue
                        
                    entity_urn = parent_div['data-entity-urn']
                    job_posting_id = entity_urn.split(':')[-1]
                    job_url = f'https://www.linkedin.com/jobs/view/{job_posting_id}/'

                    # Handle date extraction
                    date_tag_new = item.find('time', class_='job-search-card__listdate--new')
                    date_tag = item.find('time', class_='job-search-card__listdate')
                    date = ''
                    
                    if date_tag and 'datetime' in date_tag.attrs:
                        date = date_tag['datetime']
                    elif date_tag_new and 'datetime' in date_tag_new.attrs:
                        date = date_tag_new['datetime']

                    job = {
                        'title': title,
                        'company': company_elem.text.strip().replace('\n', ' ') if company_elem else '',
                        'location': location_elem.text.strip() if location_elem else '',
                        'date': date,
                        'job_url': job_url
                    }
                    joblist.append(job)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing job item: {e}")
                    continue
    
            return joblist            

        elif type == 'job_descriptions':
            try:
                div = soup.find('div', class_='description__text description__text--rich')
            except AttributeError:
                self.logger.warning("No description found for this job")
                return "No description found"
            else:
                if div:
                    for element in div.find_all(['span', 'a']):
                        element.decompose()

                    for ul in div.find_all('ul'):
                        for li in ul.find_all('li'):
                            li.insert(0, '-')

                    text = div.get_text(separator='\n').strip()
                    text = text.replace('\n\n', '')
                    text = text.replace('::marker', '-')
                    text = text.replace('-\n', '- ')
                    text = text.replace('Show less', '').replace('Show more', '')
                    return text
                else:
                    return None
        else:
            raise ValueError(f"Invalid type: {type}")

    def generate_urls(self, preferences: dict) -> List[str]:
        """Generate LinkedIn job search URLs based on preferences.
        
        Args:
            preferences (dict): User preferences containing search queries and filters.
            
        Returns:
            List[str]: List of LinkedIn job search URLs.
        """
        urls = []
        for i in range(self.config['rounds']):
            for query in preferences['search_queries']:
                # URL Encode keywords and location
                keywords = quote(query['keywords'])
                location = quote(query['location'])
                for j in range(self.config['pages_to_scrape']):
                    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords}&location={location}&f_TPR=&f_WT={query['f_WT']}&geoId=&f_TPR={self.config['max_age']}&start={25*j}"
                    urls.append(url)
        return urls

    def process_url(self, url: str, type: str) -> List[Dict]:
        """Process a single URL and extract data based on type.
        
        Args:
            url (str): URL to process.
            type (str): Type of data to extract ('job_cards' or 'job_descriptions').
            
        Returns:
            List[Dict]: Extracted data from the URL.
        """
        if type == 'job_cards':
            self.logger.info(f"Processing job cards from: {url}")
            soup = self.get_with_retry(url)
            if soup is None:
                return []
            else:
                jobs = self.cook_soup(soup, type)
                return jobs

        elif type == 'job_descriptions':
            self.logger.info(f"Processing job descriptions from: {url}")
            soup = self.get_with_retry(url)
            if soup is None:
                return []
            else:
                job_descriptions = self.cook_soup(soup, type)
                return job_descriptions

        else:
            raise ValueError(f"Invalid type: {type}")

    def get_jobcards(self, preferences: dict) -> List[Dict]:
        """Get job cards from LinkedIn based on user preferences.
        
        Args:
            preferences (dict): User preferences for job searching.
            
        Returns:
            List[Dict]: List of job card dictionaries.
        """
        job_cards = []

        # Generate urls
        urls = self.generate_urls(preferences)

        # Process urls to get job cards
        for url in urls:
            job_cards.extend(self.process_url(url, 'job_cards'))

        return job_cards
    
    def get_job_descriptions(self, urls: List[str]) -> List[str]:
        """Get job descriptions from a list of job URLs.
        
        Args:
            urls (List[str]): List of job URLs to scrape descriptions from.
            
        Returns:
            List[str]: List of job descriptions.
        """
        job_descriptions = []

        for url in urls:
            job_descriptions.append(self.process_url(url, 'job_descriptions'))

        return job_descriptions