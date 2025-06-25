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
  - 🔒 Hide - Hide irrelevant jobs or not interested jobs
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
