# Job Manager - Flask UI

## Features

### 🎯 Core Functionality
- **View All Jobs**: Browse all scraped jobs in a paginated, card-based layout
- **Advanced Search**: Search jobs by keywords across title, company, and description
- **Smart Filtering**: Filter jobs by company, date range, and status
- **CV Matching**: Upload your CV to get AI-powered job matching percentages
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

### 📄 CV Scanning & Matching
- **CV Upload**: Upload your CV in PDF format for intelligent job matching
- **AI-Powered Matching**: Uses TF-IDF vectorization and cosine similarity for accurate matching
- **Match Percentages**: Each job shows a color-coded CV match percentage:
  - 🟢 **High Match (≥70%)**: Green badge - Excellent fit for your profile
  - 🟡 **Medium Match (40-69%)**: Yellow badge - Good potential match
  - 🔴 **Low Match (1-39%)**: Red badge - Some relevance found
  - ⚪ **No Match (0%)**: Gray badge - No CV uploaded or no similarity found
- **Smart Sorting**: Sort jobs by CV match percentage to prioritize most relevant opportunities
- **Auto-Refresh**: CV matching recalculates automatically when new CV is uploaded
- **File Management**: New CV uploads replace previous files seamlessly

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
- `cv_match_percentage` (float) - Auto-generated CV matching score (0-100)

## Usage Guide

### Dashboard Overview
The main dashboard shows:
- **Statistics Cards**: Total jobs and counts by status
- **CV Matching Panel**: Upload CV and sort by relevance
- **Search & Filter Panel**: Tools for finding specific jobs
- **Jobs List**: Paginated cards showing job details with CV match percentages
- **Pagination**: Navigate through multiple pages

### CV Scanning & Matching
1. **Upload Your CV**: 
   - Click the "CV Scan" button in the CV Matching section
   - Select a PDF file containing your resume/CV
   - File is automatically saved and processed
2. **View Match Percentages**: 
   - Each job card displays a color-coded CV match percentage
   - Higher percentages indicate better alignment with your CV
3. **Sort by Relevance**:
   - Check "Sort by CV Match %" to prioritize most relevant jobs
   - Jobs will be ordered from highest to lowest match percentage
4. **Update CV**:
   - Upload a new CV file to replace the previous one
   - All job match percentages recalculate automatically

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
- Query params: `search`, `page`, `per_page`, `company`, `date_from`, `date_to`, `applied`, `interview`, `interest`, `rejected`, `filtered`, `sort_by_cv_match`

### POST `/api/jobs/<job_id>/update`
Update job status
- Body: `{"field": "applied", "value": true}`

### DELETE `/api/jobs/<job_id>/delete`
Delete job permanently

### GET `/api/companies`
Get list of all companies

### GET `/api/stats`
Get job statistics by status

### POST `/api/cv/upload`
Upload CV file for job matching
- Body: `multipart/form-data` with `cv_file` field (PDF only)
- Saves file to `/app/cv.pdf`

### GET `/api/cv/status`
Check if CV is uploaded
- Returns: `{"cv_available": boolean}`

## Configuration

The application uses configuration from:
- `src/job_scraping/config.json` - Elasticsearch connection settings
- `preferences.yaml` - Application preferences

### Dependencies
The CV matching feature requires:
- `scikit-learn` - For TF-IDF vectorization and cosine similarity
- `PyPDF2` - For PDF text extraction
- Elasticsearch with indexed job descriptions

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

**CV upload failing**
- Ensure `/app` directory has write permissions
- Check file size limits (default Flask limit is 16MB)
- Verify only PDF files are being uploaded
- Check Flask application logs for detailed errors

**CV matching not working**
- Ensure scikit-learn is installed (`pip install scikit-learn`)
- Check that job descriptions contain text content
- Verify CV file was uploaded successfully to `/app/cv.pdf`
- Check console for CV processing errors

**CV match percentages showing 0%**
- Verify CV file contains readable text (not just images)
- Check that job descriptions are properly indexed
- Ensure CV and job descriptions are in the same language
- Try uploading a different CV format or content

**Styling issues**
- Clear browser cache
- Check that Bootstrap CSS is loading
- Verify static files are being served correctly

### Debug Mode
The Flask app runs in debug mode by default. Check the console output for detailed error messages.