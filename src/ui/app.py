# src/ui/app.py

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from src.ui.flask_functions import get_jobs_from_es, update_job_status, delete_job, get_companies, get_job_stats



# App initialization
app = Flask(__name__)
CORS(app)
app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True,
)



# Routes
@app.route('/')
def index():
    """Main page showing jobs"""
    return render_template('index.html')

@app.route('/api/jobs')
def api_jobs():
    """API endpoint to get jobs with filters and search"""
    search_query = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    # Get filters
    filters = {}
    for field in ['filtered', 'interest', 'applied', 'interview', 'rejected', 'not_interested']:
        value = request.args.get(field)
        if value is not None:
            filters[field] = value.lower() == 'true'
    
    filters['company'] = request.args.get('company')
    filters['date_from'] = request.args.get('date_from')
    filters['date_to'] = request.args.get('date_to')
    
    result = get_jobs_from_es(search_query, filters, page, per_page)
    return jsonify(result)

@app.route('/api/jobs/<job_id>/update', methods=['POST'])
def api_update_job(job_id):
    """API endpoint to update job status"""
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')
    
    if field not in ['filtered', 'interest', 'applied', 'interview', 'rejected', 'not_interested']:
        return jsonify({'error': 'Invalid field'}), 400
    
    if not isinstance(value, bool):
        return jsonify({'error': 'Value must be boolean'}), 400
    
    result = update_job_status(job_id, field, value)
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

@app.route('/api/stats')
def api_stats():
    """API endpoint to get job statistics"""
    stats = get_job_stats()
    return jsonify(stats)



if __name__ == "__main__":
    app.run(debug=True, port=5001)
