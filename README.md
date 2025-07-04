<!-- BADGES -->
[contributors_badge]: https://img.shields.io/github/contributors/guillaumepot/linkedinscraper.svg?style=for-the-badge
[contributors_url]: https://github.com/guillaumepot/linkedinscraper/graphs/contributors
[forks_badge]: https://img.shields.io/github/forks/guillaumepot/linkedinscraper.svg?style=for-the-badge
[forks_url]: https://github.com/guillaumepot/linkedinscraper/network/members
[stars_badge]: https://img.shields.io/github/stars/guillaumepot/linkedinscraper.svg?style=for-the-badge
[stars_url]: https://github.com/guillaumepot/linkedinscraper/stargazers
[issues_badge]: https://img.shields.io/github/issues/guillaumepot/linkedinscraper.svg?style=for-the-badge
[issues_url]: https://github.com/guillaumepot/linkedinscraper/issues
[license_badge]: https://img.shields.io/github/license/guillaumepot/linkedinscraper.svg?style=for-the-badge
[license_url]: https://github.com/guillaumepot/linkedinscraper/blob/master/LICENSE.txt
[linkedin_badge]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin_url]: https://linkedin.com/in/guillaumepot

<!-- PROJECT URLS -->
[repo_url]: https://github.com/guillaumepot/linkedinscraper
[logo_path]: images/logo.jpg
[docs_url]: https://github.com/guillaumepot/linkedinscraper/blob/main/docs/README.md
[bug_report_url]: https://github.com/guillaumepot/linkedinscraper/issues/new?labels=bug&template=bug-report---.md
[feature_request_url]: https://github.com/guillaumepot/linkedinscraper/issues/new?labels=enhancement&template=feature-request---.md

<!-- TECHNOLOGY BADGES -->
[python_badge]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[python_url]: https://www.python.org/
[beautiful_soup_badge]: https://img.shields.io/badge/BeautifulSoup-59666C?style=for-the-badge&logo=python&logoColor=white
[beautiful_soup_url]: https://www.crummy.com/software/BeautifulSoup/
[scikitlearn_badge]: https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white
[scikitlearn_url]: https://scikit-learn.org/ 
[elasticsearch_badge]: https://img.shields.io/badge/Elasticsearch-005571?style=for-the-badge&logo=elasticsearch&logoColor=white
[elasticsearch_url]: https://www.elastic.co/
[flask_badge]: https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white
[flask_url]: https://flask.palletsprojects.com/
[docker_badge]: https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white
[docker_url]: https://www.docker.com/


<!-- README -->
<a id="readme-top"></a>

# 🎯 LinkedIn Job Scraper

<!-- PROJECT BADGES -->
[![Contributors][contributors_badge]][contributors_url]
[![Forks][forks_badge]][forks_url]
[![Stargazers][stars_badge]][stars_url]
[![Issues][issues_badge]][issues_url]
[![MIT License][license_badge]][license_url]
[![LinkedIn][linkedin_badge]][linkedin_url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/guillaumepot/linkedinscraper">
    <img src="images/logo.jpg" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">🎯 LinkedIn Job Scraper</h3>

  <p align="center">
    A comprehensive LinkedIn job scraper with advanced filtering, Elasticsearch storage, and a modern Flask-based web UI for job management.
    <br />
    <a href="https://github.com/guillaumepot/linkedinscraper/blob/main/README.md"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="#demo">View Demo</a>
    ·
    <a href="https://github.com/guillaumepot/linkedinscraper/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/guillaumepot/linkedinscraper/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>


## About The Project

This tool automatically scrapes job postings from LinkedIn based on your preferences, applies intelligent filtering, and provides a clean interface to manage your job applications. Perfect for job seekers who want to automate their job search process and never miss relevant opportunities.

Initilly designed by **cwwmbm** (https://github.com/cwwmbm/linkedinscraper) and forked to make it better. Initial repo seems outdated and not maintened so I keep my changes here.


### Built With

* [![Python][python_badge]][python_url]
* [![BeautifulSoup4][beautiful_soup_badge]][beautiful_soup_url]
* [![Scikit-Learn][scikitlearn_badge]][scikitlearn_url]
* [![Flask][flask_badge]][flask_url]
* [![ElasticSearch][elasticsearch_badge]][elasticsearch_url]
* [![Docker][docker_badge]][docker_url]



## Table of Contents

<details>
  <summary>Click to expand</summary>
  <ol>
    <li><a href="#about-the-project">About The Project</a></li>
    <li><a href="#features">Features</a></li>
    <li><a href="#installation">Installation</a></li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#configuration">Configuration</a></li>
    <li><a href="#project-structure">Project Structure</a></li>
    <li><a href="#development">Development</a></li>
    <li><a href="#troubleshooting">Troubleshooting</a></li>
    <li><a href="#security--privacy">Security & Privacy</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>


## Features

### Core Functionality
- **🔍 Automated Job Scraping**: Scrapes LinkedIn job postings based on configurable search queries
- **🎯 Intelligent Filtering**: Advanced filtering system for job titles, companies, descriptions, languages, and age
- **🌐 Language Detection**: Filters jobs by detected language in job descriptions
- **🔄 Duplicate Prevention**: Automatically detects and prevents duplicate job entries
- **📊 Elasticsearch Integration**: Stores and indexes job data for fast search and retrieval
- **🔒 Proxy Support**: Optional proxy connection support for enhanced scraping reliability

### Web Interface
- **💻 Modern Flask UI**: Responsive web interface for job management
- **📈 Job Status Tracking**: Track application status (Interested, Applied, Interview, Rejected)
- **🔎 Advanced Search**: Search and filter jobs by multiple criteria
- **📊 Real-time Statistics**: Dashboard with job counts and analytics
- **📱 Mobile Responsive**: Works seamlessly on desktop, tablet, and mobile devices

### Data Management
- **🗄️ Elasticsearch Storage**: High-performance search and analytics
- **📈 Kibana Integration**: Visualize job data with Kibana dashboards (optional)
- **📤 Export Capabilities**: Data can be exported and analyzed
- **💾 Backup Support**: Docker-based persistent storage

### Advanced Filtering System

#### Multi-Level Filtering
1. **Title Filtering**: Include/exclude based on job titles
2. **Company Filtering**: Exclude specific companies
3. **Age Filtering**: Filter jobs older than specified days
4. **Language Detection**: Filter by detected language
5. **Description Filtering**: Filter based on description keywords

#### Elasticsearch Features
- **Full-text Search**: Search across all job fields
- **Aggregations**: Generate statistics and analytics
- **Real-time Updates**: Immediate data availability
- **Scalable Storage**: Handle thousands of job entries

#### Proxy Features
- **Connection Testing**: Verify proxy connectivity before scraping
- **Rotation Support**: Use multiple proxies for enhanced reliability
- **Error Handling**: Graceful fallback when proxies fail

<p align="right">(<a href="#readme-top">back to top</a>)</p>



## Installation

### Prerequisites

- **Python**: 3.12.3+ (recommended to use [uv](https://docs.astral.sh/uv/))
- **Docker**: Latest version with Docker Compose

### Quick Start

```bash
# Clone the repository
git clone https://github.com/guillaumepot/linkedinscraper.git
cd linkedinscraper

# Start services (Flask UI, ElasticSearch Database, [optional] Kibana (with --profile kibana))
docker compose up -d

# Set up Python environment (recommended: use uv)
uv sync

# Configure your preferences
cp preferences.yaml.example preferences.yaml # Edit preferences.yaml with your job search criteria
# Run the scraper
uv run scrap.py
```


### 🔧 Detailed Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/guillaumepot/linkedinscraper.git
cd linkedinscraper
```

#### 2. Set Up Python Environment

**Option A: Using uv (Recommended)**
```bash
uv sync
```

**Option B: Using traditional venv**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
# Requirements must be generated from pyproject.toml: 
pip install pip-tools
pip-compile pyproject.toml
pip install -r requirements.txt
```

#### 3. Configure Your Job Search

Copy and edit the preferences file:
```bash
mv config/preferences.yaml.example config/preferences.yaml
```

Edit `preferences.yaml` to customize your job search:
```yaml
search_queries:
  - keywords: "Data Engineer"
    location: "San Francisco, CA"
    f_WT: "2"  # Work type: "" (Any), "0" (On-Site), "1" (Hybrid), "2" (Remote)
  - keywords: "Machine Learning Engineer"
    location: "New York, NY"
    f_WT: ""

# Filtering preferences
title_include: ["Data", "Engineer", "Scientist", "Machine Learning"]
title_exclude: ["frontend", "react.js", "internship", "junior"]
company_exclude: ["CompanyToAvoid", "SpamCompany"]
languages: ["en", "fr"]
max_age: 7  # Maximum job age in days
```

#### 4. Start Services
```bash
docker compose up -d
```

This will start:
- 🔍 **Elasticsearch** on `http://localhost:9200`
- 🌐 **Flask Web UI** on `http://localhost:5001`
- 📊 **Kibana** on `http://localhost:5601`  (optional if --profile kibana)

#### 5. Verify Installation
```bash
# Check Elasticsearch
curl http://localhost:9200/_cluster/health

# Check if all containers are running
docker compose ps
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

### Web Interface

1. **Access the Dashboard**: Navigate to `http://localhost:5001`
2. **View Jobs**: Browse scraped jobs with filtering options
3. **Manage Applications**: Update job status (Applied, Interview, etc.)
4. **Search & Filter**: Use advanced search to find specific jobs

More informations about the UI [here](docs/FLASK_UI.md)

### Scripts

You can run diffrents scripts to:
- Check your proxy connection
- Export you job data to a csv file for further analysis

```bash
uv run ./scripts/proxy_connection_tester.py
uv run ./scripts/export_jobs_data.py
```


<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Configuration

Navigate to ./config dir to find an change default configuration

### preferences.yaml

Edit your job search preferences following this pattern, you can use preferances.yaml.example to help you.
```yaml
# Search queries
search_queries:
  - keywords: "Your Job Title"
    location: "Your Location"
    f_WT: ""  # "" (Any), "0" (On-Site), "1" (Hybrid), "2" (Remote)

# Filtering
title_include: ["keyword1", "keyword2"]
title_exclude: ["exclude1", "exclude2"]
company_exclude: ["company1", "company2"]
languages: ["en", "fr", "de"]
desciption_words_include: ["Data", "Engineer", "Scientist", "Python"]
max_age: 7

# Optional: OpenAI Integration (Future feature)
# OpenAI:
#   API_KEY: "your-openai-api-key"
#   Model: "gpt-3.5-turbo"
#   resume_path: "/path/to/your/resume.pdf"
```

### config.json

- This file is used to configure BeautifulSoupEngine (used when scraping jobs) and ElasticSearchEngine
- You can let this vars by default if you don't change the default container configuration for ElasticSearch.
- Logger config isn't meant to be changed.
**/!\ It's recommended to set proxies (http & https), default is null.**
```json
{
  "BeautifulSoupEngine": {
    "proxies": {
      "http": "http://proxy:port",
      "https": "https://proxy:port"
    },
    "headers": {
      "User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)"
    },
    "rounds": 3,
    "pages_to_scrape": 10,
    "max_age": "r84600",
    "request_timeout": 10,
    "max_retry": 3,
    "retry_delay": 5
  },
  "ElasticsearchEngine": {
    "hosts": "http://localhost:9200",
    "verify_certs": false,
    "use_ssl": false,
    "ca_certs": null,
    "basic_auth": null,
    "indexes": ["jobs"]
  }
}
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



## 📁 Project Structure

```
linkedinscraper/
├── 📁 .github/                       # Workflows and templates
├── 📁 changelogs/                    # Changelogs md documents
├── 📁 config/                        # Configuration files
│   ├── 📄 config.json                # Utilities configuration file
│   └── 📄 preferences.yaml.example   # User preferences for job scraping
├── 📁 data/
│   ├── 📁 elasticsearch/             # elasticsearch volume
│   └── 📁 kibana/                    # kibana volume
├── 📁 images/                        # Various images used for the repo
├── 📁 logs/                          # Application logs
├── 📁 scripts/
│   ├── export_jobs_data.py           # elasticsearch data export script
│   └── proxy_connection_tester.py    # Proxy testing utility
├── 📁 src/


│   └── 📁 utils/
│       ├── LoggerManager.py          # Logging configuration
│       └── tools                     # Utility functions


├── 📁 tests/                      # Test files


│   ├── 📁 job_scraping/
│   │   ├── JobScraper.py          # Main scraping logic
│   │   ├── BeautifulSoupEngine.py # Web scraping engine
│   │   ├── ElasticSearchEngine.py # Elasticsearch interface
│   │   └── config.json            # Scraper configuration
│   ├── 📁 ui/
│   │   ├── app.py                 # Flask web application
│   │   ├── 📁 templates/          # HTML templates
│   │   └── 📁 static/             # CSS, JS, images

│       ├── ArgParser.py           # Command line argument parsing



├── 📄 docker-compose.yaml         # Docker services
├── 📄 pyproject.toml              # Python project config
└── 📄 main.py                     # Application entry point
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Development

### Setting Up Development Environment

```bash
# Clone and setup
git clone https://github.com/guillaumepot/linkedinscraper.git
cd linkedinscraper
uv sync --dev

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check .
ruff format .
```

### Code Quality Tools

- **🔍 Ruff**: Fast Python linter and formatter
- **🪝 Pre-commit**: Git hooks for code quality
- **🧪 Pytest**: Testing framework
- **📝 Type Hints**: Enhanced code documentation

### Contributing Guidelines

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🔒 Security & Privacy

- **🔐 No Personal Data Storage**: Only public job posting information is stored
- **⏱️ Respectful Scraping**: Implements delays to avoid rate limiting
- **🏠 Local Storage**: All data is stored locally by default
- **🛡️ Proxy Support**: Enhanced privacy with proxy support
- **📝 Minimal Logging**: Only essential information is logged

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## 🐛 Troubleshooting

### Common Issues

#### Elasticsearch Connection Issues
```bash
# Check if Elasticsearch is running
curl http://localhost:9200/_cluster/health

# Restart Elasticsearch
docker compose restart elasticsearch

# Check logs
docker compose logs elasticsearch
```

#### No Jobs Found
- ✅ Check your search preferences in `preferences.yaml`
- ✅ Verify LinkedIn is accessible from your network
- ✅ Check proxy configuration if using proxies
- ✅ Ensure search keywords are not too restrictive

#### Web UI Not Loading
- ✅ Ensure Flask app is running on port 5001
- ✅ Check browser console for JavaScript errors
- ✅ Verify Elasticsearch connection
- ✅ Check Docker containers are running: `docker compose ps`

#### Python Environment Issues
```bash
# Reset virtual environment
rm -rf .venv
uv sync

# Check Python version
python --version  # Should be 3.12.3+
```

#### Docker Issues
```bash
# Reset Docker containers
docker compose down
docker compose up -d

# Check Docker logs
docker compose logs
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🗺️ Roadmap

### Upcoming Features

- [ ] **🤖 OpenAI Integration**: Match your CV with job offers and get personalized advice
- [X] **🔍 Enhanced Matching**: Elasticsearch-based CV-job matching algorithm

### Long-term Goals

- [ ] **📚 Skill Gap Analysis**: Identify missing skills for desired roles

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🤝 Contributing

### Top contributors

<a href="https://github.com/guillaumepot/linkedinscraper/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=guillaumepot/linkedinscraper" alt="contrib.rocks image" />
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>



Contributions make the open source community amazing! Any contributions you make are **greatly appreciated**.

1. **Fork** the Project
2. **Create** your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your Changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the Branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

## 🤝 Changelogs

- [V1.0.0](./changelogs/1.0.0.md)

## 📄 License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🙏 Acknowledgments

* [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - Web scraping library
* [Elasticsearch](https://www.elastic.co/) - Search and analytics engine
* [Flask](https://flask.palletsprojects.com/) - Web framework
* [Docker](https://www.docker.com/) - Containerization platform
* [uv](https://docs.astral.sh/uv/) - Fast Python package manager
* [Img Shields](https://shields.io) - README badges

<p align="right">(<a href="#readme-top">back to top</a>)</p>