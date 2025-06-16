# Job Manager - Flask UI

## Features

### 🎯 Core Functionality
- **View All Jobs**: Browse all scraped jobs in a paginated, card-based layout
- **Advanced Search**: Search jobs by keywords across title, company, and description
- **Smart Filtering**: Filter jobs by company, date range, and status
- **Status Management**: Update job statuses (Applied, Interview, Interested, Rejected, Filtered)
- **Real-time Statistics**: Dashboard showing job counts by status
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### 🔍 Search & Filter Features
- **Keyword Search**: Fuzzy search with auto-complete across job titles, companies, and descriptions
- **Company Filter**: Dropdown with all companies from your database
- **Date Range Filter**: Filter jobs by posting date
- **Status Filters**: Show only jobs with specific statuses
- **Real-time Updates**: Search results update as you type (debounced)

### 📊 Job Management
- **Status Tracking**: 
  - ✅ Applied - Mark jobs you've applied to
  - 📅 Interview - Track interview opportunities  
  - ⭐ Interested - Save jobs for later
  - ❌ Rejected - Mark rejected applications
  - 🔒 Filtered - Hide irrelevant jobs
- **Visual Indicators**: Color-coded cards and badges for easy status recognition
- **Quick Actions**: One-click status updates with confirmation

### 🎨 User Interface
- **Modern Design**: Clean, professional Bootstrap-based UI
- **Interactive Cards**: Hover effects and smooth animations
- **Modal Details**: Click job titles to view full descriptions
- **Pagination**: Navigate through large job lists efficiently
- **Loading States**: Visual feedback during data operations


## Database Information
Ensure your Elasticsearch instance is running and contains job data. The UI expects jobs with these fields:
- `title` (string)
- `company` (string) 
- `location` (string)
- `date` (datetime)
- `description` (text)
- `job_url` (string)
- `applied` (boolean)
- `interview` (boolean)
- `interest` (boolean)
- `rejected` (boolean)
- `filtered` (boolean)

## Usage Guide

### Dashboard Overview
The main dashboard shows:
- **Statistics Cards**: Total jobs and counts by status
- **Search & Filter Panel**: Tools for finding specific jobs
- **Jobs List**: Paginated cards showing job details
- **Pagination**: Navigate through multiple pages

### Searching Jobs
1. **Keyword Search**: Type in the search box to find jobs by title, company, or description
2. **Company Filter**: Select a specific company from the dropdown
3. **Date Range**: Set start and end dates to filter by posting date
4. **Status Filters**: Check boxes to show only jobs with specific statuses

### Managing Job Status
Each job card has action buttons to update status:
- **Applied**: Mark when you've submitted an application
- **Interview**: Track when you get interview invitations
- **Interested**: Save jobs you want to apply to later
- **Rejected**: Mark when applications are rejected
- **Filtered**: Hide jobs that aren't relevant

### Job Details
- Click on job titles to open a modal with full job description
- Use the "View on LinkedIn" button to open the original posting
- Status badges show current job state at a glance

### Keyboard Shortcuts
- **Enter**: Execute search
- **Escape**: Close modals

## API Endpoints

The Flask application provides these REST endpoints:

### GET `/api/jobs`
Get paginated jobs with optional filters
- Query params: `search`, `page`, `per_page`, `company`, `date_from`, `date_to`, `applied`, `interview`, `interest`, `rejected`, `filtered`

### POST `/api/jobs/<job_id>/update`
Update job status
- Body: `{"field": "applied", "value": true}`

### GET `/api/companies`
Get list of all companies

### GET `/api/stats`
Get job statistics by status

## Configuration

The application uses configuration from:
- `src/job_scraping/config.json` - Elasticsearch connection settings
- `preferences.yaml` - Application preferences

## Troubleshooting

### Common Issues

**Jobs not loading**
- Check Elasticsearch is running on localhost:9200
- Verify the 'jobs' index exists and contains data
- Check browser console for JavaScript errors

**Search not working**
- Ensure job descriptions are indexed in Elasticsearch
- Check that the multi_match query fields exist

**Status updates failing**
- Verify job IDs are correctly formatted
- Check Flask application logs for errors
- Ensure Elasticsearch write permissions

**Styling issues**
- Clear browser cache
- Check that Bootstrap CSS is loading
- Verify static files are being served correctly

### Debug Mode
The Flask app runs in debug mode by default. Check the console output for detailed error messages.