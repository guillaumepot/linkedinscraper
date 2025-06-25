# src/flask/app.py

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os

from app_functions import get_job_stats, get_jobs_from_es, update_job_status, delete_job, get_companies


# App initialization
app = Flask(__name__)
CORS(app)
app.config.update(
    DEBUG = True,
    TEMPLATES_AUTO_RELOAD = True,
)

# Routes
@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

# Stats cards
@app.route('/api/stats')
def api_stats():
    """API endpoint to get job statistics"""
    stats = get_job_stats()
    return jsonify(stats)

# Jobs
@app.route('/api/jobs')
def api_jobs():
    """API endpoint to get jobs with filters and search"""
    search_query = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    sort_by_cv_match = request.args.get('sort_by_cv_match', 'false').lower() == 'true'
    
    # Get filters
    filters = {}
    for field in ['filtered', 'interest', 'applied', 'interview', 'rejected', 'hidden']:
        value = request.args.get(field)
        if value is not None and value.lower() == 'true':
            filters[field] = 'true'
    
    filters['company'] = request.args.get('company')
    filters['date_from'] = request.args.get('date_from')
    filters['date_to'] = request.args.get('date_to')
    
    result = get_jobs_from_es(search_query, filters, page, per_page, sort_by_cv_match)
    return jsonify(result)


@app.route('/api/jobs/<job_id>/update', methods=['POST'])
def api_update_job(job_id):
    """API endpoint to update job status"""
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')
    
    if field not in ['filtered', 'interest', 'applied', 'interview', 'rejected', 'hidden']:
        return jsonify({'error': 'Invalid field'}), 400
    
    if not isinstance(value, bool):
        return jsonify({'error': 'Value must be boolean'}), 400
    
    int_value = 1 if value else 0
    result = update_job_status(job_id, field, int_value)
    if result:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to update job'}), 500


@app.route('/api/jobs/<job_id>/delete', methods=['DELETE'])
def api_delete_job(job_id):
    """API endpoint to delete a job"""
    result = delete_job(job_id)
    if result:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to delete job'}), 500


@app.route('/api/companies')
def api_companies():
    """API endpoint to get all companies"""
    companies = get_companies()
    return jsonify(companies)


# CV routes
@app.route('/api/cv/upload', methods=['POST'])
def api_upload_cv():
    """API endpoint to upload CV file"""
    try:
        if 'cv_file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['cv_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and file.filename.lower().endswith('.pdf'):
            cv_path = 'cv.pdf'
            file.save(cv_path)
            return jsonify({'success': True, 'message': 'CV uploaded successfully'})
        else:
            return jsonify({'error': 'Only PDF files are allowed'}), 400
            
    except Exception as e:
        print(f"Error uploading CV: {e}")
        return jsonify({'error': 'Failed to upload CV'}), 500


@app.route('/api/cv/status')
def api_cv_status():
    """API endpoint to check if CV is uploaded"""
    cv_path = '/app/cv.pdf'
    cv_exists = os.path.exists(cv_path)
    return jsonify({'cv_available': cv_exists})



if __name__ == "__main__":
    app.run(debug = True, host = '0.0.0.0', port = 5001)