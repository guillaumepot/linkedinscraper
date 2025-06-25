// Global variables
let currentPage = 1;
let currentPerPage = 20;
let currentSearch = '';
let currentFilters = {};
let isLoading = false;
let jobsData = [];

// Init app scripts
document.addEventListener('DOMContentLoaded', function() {
    loadCompanies();
    loadStats();
    loadJobs();
    checkCvStatus();
    
    // Set up event listeners
    setupEventListeners();
});

function setupEventListeners() {
    // Search input with debounce
    let searchTimeout;
    document.getElementById('searchInput').addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentSearch = this.value;
            currentPage = 1;
            loadJobs();
        }, 500);
    });
    
    // Enter key for search
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchJobs();
        }
    });
    
    // Filter change events
    document.getElementById('companyFilter').addEventListener('change', function() {
        currentPage = 1;
        loadJobs();
    });
    
    document.getElementById('dateFromFilter').addEventListener('change', function() {
        currentPage = 1;
        loadJobs();
    });
    
    document.getElementById('dateToFilter').addEventListener('change', function() {
        currentPage = 1;
        loadJobs();
    });
    
    // Status filter checkboxes
    const statusFilters = ['filterApplied', 'filterInterview', 'filterInterested', 'filterHidden', 'filterRejected', 'filterFiltered', 'showAllJobs'];
    statusFilters.forEach(filterId => {
        document.getElementById(filterId).addEventListener('change', function() {
            currentPage = 1;
            loadJobs();
        });
    });
    
    // CV sort checkbox
    document.getElementById('sortByCvMatch').addEventListener('change', function() {
        currentPage = 1;
        loadJobs();
    });
}


// Common functions
function showLoading() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.classList.remove('d-none');
    }
    isLoading = true;
}

function hideLoading() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.classList.add('d-none');
    }
    isLoading = false;
}

async function loadJobs() {
    if (isLoading) return;
    
    showLoading();
    
    try {
        const filters = buildFilters();
        const sortByCvMatch = document.getElementById('sortByCvMatch').checked;
        const params = new URLSearchParams({
            page: currentPage,
            per_page: currentPerPage,
            search: currentSearch,
            sort_by_cv_match: sortByCvMatch
        });
        
        // Add filters to params
        Object.entries(filters).forEach(([key, value]) => {
            params.append(key, value);
        });
        
        const response = await fetch(`/api/jobs?${params}`);
        const data = await response.json();
        
        jobsData = data.jobs; // Store for modal use
        displayJobs(data.jobs);
        updatePagination(data);
        
    } catch (error) {
        console.error('Error loading jobs:', error);
        showError('Failed to load jobs. Please try again.');
    } finally {
        hideLoading();
    }
}


// Utility functions
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text ? text.replace(/[&<>"']/g, function(m) { return map[m]; }) : '';
}


function showSuccess(message) {
    showNotification(message, 'success');
}

function showError(message) {
    showNotification(message, 'danger');
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}


// Navigation
// Update pagination UI
function updatePagination(data) {
    const pagination = document.getElementById('pagination');
    const { page, total_pages, total } = data;
    
    if (total_pages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // Previous button
    paginationHTML += `
        <li class="page-item ${page <= 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${page - 1}); return false;" aria-label="Previous">
                <span aria-hidden="true">&laquo;</span>
            </a>
        </li>
    `;
    
    // Page numbers
    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(total_pages, page + 2);
    
    if (startPage > 1) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(1); return false;">1</a></li>`;
        if (startPage > 2) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `
            <li class="page-item ${i === page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    if (endPage < total_pages) {
        if (endPage < total_pages - 1) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${total_pages}); return false;">${total_pages}</a></li>`;
    }
    
    // Next button
    paginationHTML += `
        <li class="page-item ${page >= total_pages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${page + 1}); return false;" aria-label="Next">
                <span aria-hidden="true">&raquo;</span>
            </a>
        </li>
    `;
    
    pagination.innerHTML = paginationHTML;
}

// Change page
function changePage(page) {
    if (page < 1 || isLoading) return;
    currentPage = page;
    loadJobs();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Change items per page
function changePerPage() {
    currentPerPage = parseInt(document.getElementById('perPageSelect').value);
    currentPage = 1;
    loadJobs();
}


// Toggle job description expansion
function toggleDescription(jobId) {
    const descElement = document.getElementById(`desc-${jobId}`);
    const expandText = document.getElementById(`expand-text-${jobId}`);
    const job = jobsData.find(j => j._id === jobId);
    
    if (descElement.classList.contains('expanded')) {
        descElement.classList.remove('expanded');
        expandText.textContent = 'Show more';
        const truncated = job.description.length > 300 ? 
            job.description.substring(0, 300) + '...' : job.description;
        descElement.textContent = truncated;
    } else {
        descElement.classList.add('expanded');
        expandText.textContent = 'Show less';
        descElement.textContent = job.description || 'No description available';
    }
}


// Stats Cards
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('totalJobs').textContent = stats.total;
        document.getElementById('interestedJobs').textContent = stats.interested;
        document.getElementById('appliedJobs').textContent = stats.applied;
        document.getElementById('interviewJobs').textContent = stats.interview;
        document.getElementById('rejectedJobs').textContent = stats.rejected;
        document.getElementById('hiddenJobs').textContent = stats.hidden;
        document.getElementById('filteredJobs').textContent = stats.filtered;
        document.getElementById('jobCount').textContent = stats.total + ' jobs total';
    } catch (error) {
        console.error('Error loading stats:', error);
        document.getElementById('jobCount').textContent = 'Error loading stats';
    }
}



// Filters
// Clear all filters
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('companyFilter').value = '';
    document.getElementById('dateFromFilter').value = '';
    document.getElementById('dateToFilter').value = '';
    
    // Clear status filter checkboxes
    const statusFilters = ['filterApplied', 'filterInterview', 'filterInterested', 'filterHidden', 'filterRejected', 'filterFiltered', 'showAllJobs'];
    statusFilters.forEach(filterId => {
        document.getElementById(filterId).checked = false;
    });
    
    // Clear CV sort checkbox
    document.getElementById('sortByCvMatch').checked = false;
    
    currentSearch = '';
    currentPage = 1;
    loadJobs();
}

// Build filters object from current form state
function buildFilters() {
    const filters = {};
    
    // Company filter
    const company = document.getElementById('companyFilter').value;
    if (company) filters.company = company;
    
    // Date filters
    const dateFrom = document.getElementById('dateFromFilter').value;
    const dateTo = document.getElementById('dateToFilter').value;
    if (dateFrom) filters.date_from = dateFrom;
    if (dateTo) filters.date_to = dateTo;
    
    // Status filters - only include if checked
    if (document.getElementById('filterApplied').checked) {
        filters.applied = 'true';
    }
    if (document.getElementById('filterInterview').checked) {
        filters.interview = 'true';
    }
    if (document.getElementById('filterInterested').checked) {
        filters.interest = 'true';
    }
    if (document.getElementById('filterHidden').checked) {
        filters.hidden = 'true';
    }
    if (document.getElementById('filterRejected').checked) {
        filters.rejected = 'true';
    }
    

    if (document.getElementById('filterFiltered').checked) {
        filters.filtered = 'true';
    }
    
    // Handle "Show all jobs" checkbox - exclude filtered jobs by default unless this is checked
    if (!document.getElementById('showAllJobs').checked) {
        filters.exclude_filtered = 'true';
    }
    
    return filters;
}

// Load companies for filter dropdown
async function loadCompanies() {
    try {
        const response = await fetch('/api/companies');
        const companies = await response.json();
        
        const companySelect = document.getElementById('companyFilter');
        companySelect.innerHTML = '<option value="">All Companies</option>';
        
        companies.forEach(company => {
            const option = document.createElement('option');
            option.value = company;
            option.textContent = company;
            companySelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading companies:', error);
    }
}


// Jobs

// Display jobs in the UI
function displayJobs(jobs) {
    const jobsList = document.getElementById('jobsList');
    
    if (jobs.length === 0) {
        jobsList.innerHTML = `
            <div class="no-jobs-message">
                <i class="fas fa-search"></i>
                <h4>No jobs found</h4>
                <p>Try adjusting your search criteria or filters.</p>
            </div>
        `;
        return;
    }
    
    jobsList.innerHTML = jobs.map(job => createJobCard(job)).join('');
}

// Create HTML for a single job card
function createJobCard(job) {
    const statusClasses = [];
    const statusBadges = [];
    
    if (job.applied === 1) {
        statusClasses.push('applied');
        statusBadges.push('<span class="status-badge applied">Applied</span>');
    }
    if (job.rejected === 1) {
        statusClasses.push('rejected');
        statusBadges.push('<span class="status-badge rejected">Rejected</span>');
    }
    if (job.interview === 1) {
        statusClasses.push('interview');
        statusBadges.push('<span class="status-badge interview">Interview</span>');
    }
    if (job.interest === 1) {
        statusClasses.push('interested');
        statusBadges.push('<span class="status-badge interested">Interested</span>');
    }
    if (job.hidden === 1) {
        statusClasses.push('hidden');
        statusBadges.push('<span class="status-badge not-interested">Hidden</span>');
    }
    if (job.filtered === 1) {
        statusClasses.push('filtered');
        statusBadges.push('<span class="status-badge filtered">Filtered</span>');
    }
    
    const description = job.description || 'No description available';
    const truncatedDescription = description.length > 300 ? 
        description.substring(0, 300) + '...' : description;
    
    return `
        <div class="job-card ${statusClasses.join(' ')}" data-job-id="${job._id}">
            <div class="row">
                <div class="col-md-8">
                    <h3 class="job-title" onclick="showJobDetails('${job._id}')">${escapeHtml(job.title)}</h3>
                    <div class="job-company">${escapeHtml(job.company)}</div>
                    <div class="job-location"><i class="fas fa-map-marker-alt me-1"></i>${escapeHtml(job.location || 'Location not specified')}</div>
                    <div class="job-date"><i class="fas fa-calendar me-1"></i>${job.date_formatted}</div>
                    <div class="job-cv-match"><i class="fas fa-chart-line me-1"></i>CV Match: <span class="cv-match-percentage ${getCvMatchClass(job.cv_match_percentage || 0)}">${job.cv_match_percentage || 0}%</span></div>
                    <div class="job-url">
                        <a href="${job.job_url}" target="_blank" title="View on LinkedIn">
                            <i class="fab fa-linkedin me-1"></i>View on LinkedIn
                        </a>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="mb-2">
                        ${statusBadges.join('')}
                    </div>
                    <div class="job-actions">
                        <button class="btn btn-outline-success btn-sm" onclick="toggleJobStatus('${job._id}', 'applied', ${job.applied !== 1})">
                            <i class="fas fa-paper-plane me-1"></i>${job.applied === 1 ? 'Unapply' : 'Applied'}
                        </button>
                        <button class="btn btn-outline-info btn-sm" onclick="toggleJobStatus('${job._id}', 'interview', ${job.interview !== 1})">
                            <i class="fas fa-handshake me-1"></i>${job.interview === 1 ? 'No Interview' : 'Interview'}
                        </button>
                        <button class="btn btn-outline-warning btn-sm" onclick="toggleJobStatus('${job._id}', 'interest', ${job.interest !== 1})">
                            <i class="fas fa-star me-1"></i>${job.interest === 1 ? 'Hidden' : 'Interested'}
                        </button>
                        <button class="btn btn-outline-dark btn-sm" onclick="toggleJobStatus('${job._id}', 'hidden', ${job.hidden !== 1})">
                            <i class="fas fa-thumbs-down me-1"></i>${job.hidden === 1 ? 'Undo Hidden' : 'Hidden'}
                        </button>
                        <button class="btn btn-outline-danger btn-sm" onclick="toggleJobStatus('${job._id}', 'rejected', ${job.rejected !== 1})">
                            <i class="fas fa-times me-1"></i>${job.rejected === 1 ? 'Unreject' : 'Rejected'}
                        </button>
                        <button class="btn btn-outline-secondary btn-sm" onclick="toggleJobStatus('${job._id}', 'filtered', ${job.filtered !== 1})">
                            <i class="fas fa-eye-slash me-1"></i>${job.filtered === 1 ? 'Unfilter' : 'Filter'}
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deleteJob('${job._id}')" title="Remove job permanently">
                            <i class="fas fa-trash me-1"></i>Remove
                        </button>
                    </div>
                </div>
            </div>
            <div class="row mt-2">
                <div class="col-12">
                    <div class="job-description" id="desc-${job._id}">
                        ${escapeHtml(truncatedDescription)}
                    </div>
                    ${description.length > 300 ? `
                        <button class="expand-btn" onclick="toggleDescription('${job._id}')">
                            <span id="expand-text-${job._id}">Show more</span>
                        </button>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

// Search jobs
function searchJobs() {
    currentSearch = document.getElementById('searchInput').value;
    currentPage = 1;
    loadJobs();
}

// Toggle job status
async function toggleJobStatus(jobId, field, value) {
    const jobCard = document.querySelector(`[data-job-id="${jobId}"]`);
    if (!jobCard) return;
    
    // Add updating class
    jobCard.classList.add('updating');
    
    try {
        const response = await fetch(`/api/jobs/${jobId}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                field: field,
                value: value
            })
        });
        
        if (response.ok) {
            // Reload jobs to reflect changes
            await loadJobs();
            await loadStats(); // Update statistics
            showSuccess(`Job ${field} status updated successfully`);
        } else {
            const error = await response.json();
            showError(error.error || 'Failed to update job status');
        }
    } catch (error) {
        console.error('Error updating job status:', error);
        showError('Failed to update job status. Please try again.');
    } finally {
        jobCard.classList.remove('updating');
    }
}

// Delete job permanently
async function deleteJob(jobId) {
    // Find the job to get its title for confirmation
    const job = jobsData.find(j => j._id === jobId);
    const jobTitle = job ? job.title : 'this job';
    
    if (!confirm(`Are you sure you want to permanently delete "${jobTitle}"? This action cannot be undone.`)) {
        return;
    }
    
    const jobCard = document.querySelector(`[data-job-id="${jobId}"]`);
    if (!jobCard) return;
    
    // Add updating class
    jobCard.classList.add('updating');
    
    try {
        const response = await fetch(`/api/jobs/${jobId}/delete`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Remove the job card from the UI with a fade effect
            jobCard.style.transition = 'opacity 0.3s ease';
            jobCard.style.opacity = '0';
            
            setTimeout(() => {
                if (jobCard.parentNode) {
                    jobCard.remove();
                }
            }, 300);
            
            // Remove the job from our local data
            jobsData = jobsData.filter(j => j._id !== jobId);
            
            // Reload jobs to reflect changes and update stats
            await loadStats(); // Update statistics immediately
            
            // If this was the last job on the page, go to previous page
            const remainingJobs = document.querySelectorAll('.job-card').length - 1;
            if (remainingJobs === 0 && currentPage > 1) {
                currentPage--;
            }
            
            // Reload jobs after a short delay to allow for the fade animation
            setTimeout(() => {
                loadJobs();
            }, 300);
            
            showSuccess('Job deleted successfully!');
        } else {
            const error = await response.json();
            showError(error.error || 'Failed to delete job');
        }
    } catch (error) {
        console.error('Error deleting job:', error);
        showError('Failed to delete job. Please try again.');
    } finally {
        jobCard.classList.remove('updating');
    }
}


// Show job details in modal
function showJobDetails(jobId) {
    const job = jobsData.find(j => j._id === jobId);
    if (!job) return;
    
    // Populate modal
    document.getElementById('modalJobTitle').textContent = job.title;
    document.getElementById('modalJobLink').href = job.job_url;
    
    document.getElementById('modalJobContent').innerHTML = `
        <div class="mb-3">
            <h6>Company</h6>
            <p>${escapeHtml(job.company)}</p>
        </div>
        <div class="mb-3">
            <h6>Location</h6>
            <p>${escapeHtml(job.location || 'Location not specified')}</p>
        </div>
        <div class="mb-3">
            <h6>Date Posted</h6>
            <p>${job.date_formatted}</p>
        </div>
        <div class="mb-3">
            <h6>Description</h6>
            <div style="max-height: 400px; overflow-y: auto; white-space: pre-wrap; line-height: 1.6;">${escapeHtml(job.description || 'No description available')}</div>
        </div>
    `;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('jobModal'));
    modal.show();
}


// CV functions (upload, status, ...)
async function uploadCV() {
    const fileInput = document.getElementById('cvFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showError('Please select a PDF file to upload');
        return;
    }
    
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showError('Only PDF files are allowed');
        return;
    }
    
    const formData = new FormData();
    formData.append('cv_file', file);
    
    try {
        showLoading();
        const response = await fetch('/api/cv/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('CV uploaded successfully! Calculating job matches...');
            checkCvStatus();
            // Reload jobs to update CV match percentages
            loadJobs();
            // Clear the file input
            fileInput.value = '';
        } else {
            showError(result.error || 'Failed to upload CV');
        }
    } catch (error) {
        console.error('Error uploading CV:', error);
        showError('Failed to upload CV. Please try again.');
    } finally {
        hideLoading();
    }
}

async function checkCvStatus() {
    try {
        const response = await fetch('/api/cv/status');
        const result = await response.json();
        
        const statusElement = document.getElementById('cvStatus');
        if (result.cv_available) {
            statusElement.textContent = 'CV uploaded';
            statusElement.className = 'ms-3 text-success';
        } else {
            statusElement.textContent = 'No CV uploaded';
            statusElement.className = 'ms-3 text-muted';
        }
    } catch (error) {
        console.error('Error checking CV status:', error);
    }
} 

function getCvMatchClass(percentage) {
    if (percentage >= 70) {
        return 'cv-match-high';
    } else if (percentage >= 40) {
        return 'cv-match-medium';
    } else if (percentage > 0) {
        return 'cv-match-low';
    } else {
        return 'cv-match-none';
    }
}
