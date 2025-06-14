from flask import Flask, render_template, request, jsonify
from policy_analyzer import PolicyAnalyzer
from use_case_analyzer import UseCaseAnalyzer
import os
from werkzeug.utils import secure_filename
from utils import load_documents
import tempfile
import logging
from pathlib import Path
import time
from datetime import datetime, timedelta
import glob

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure upload directory exists and is writable
upload_dir = Path(app.config['UPLOAD_FOLDER'])
upload_dir.mkdir(exist_ok=True)
if not os.access(upload_dir, os.W_OK):
    logger.error(f"Upload directory {upload_dir} is not writable!")

# Initialize analyzers
policy_analyzer = PolicyAnalyzer(os.getenv('OPENROUTER_API_KEY'))
use_case_analyzer = UseCaseAnalyzer(os.getenv('OPENROUTER_API_KEY'))

# Initialize databases
policy_analyzer.initialize_databases(
    internal_path="data/internal",
    global_path="data/global"
)
use_case_analyzer.set_internal_db(policy_analyzer.internal_db)

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def cleanup_old_files():
    """Remove files older than 1 hour from the upload directory"""
    try:
        one_hour_ago = datetime.now() - timedelta(hours=1)
        for file_path in glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], '*')):
            if os.path.getmtime(file_path) < one_hour_ago.timestamp():
                os.remove(file_path)
                logger.info(f"Removed old file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up old files: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        language = request.form.get('language', 'en')
        
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename.endswith('.pdf'):
                # Save the file temporarily
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Analyze the policy
                result = policy_analyzer.analyze_new_policy(filepath, language)
                
                # Clean up
                os.remove(filepath)
                
                if result:
                    return jsonify(result)
                else:
                    return jsonify({'error': 'Failed to analyze policy'}), 500
            else:
                return jsonify({'error': 'Invalid file type'}), 400
        
        # Handle text input
        elif 'policy_text' in request.form:
            policy_text = request.form.get('policy_text')
            if policy_text:
                result = policy_analyzer.analyze_new_policy_from_text(policy_text, language)
                if result:
                    return jsonify(result)
                else:
                    return jsonify({'error': 'Failed to analyze policy text'}), 500
            else:
                return jsonify({'error': 'No policy text provided'}), 400
        
        return jsonify({'error': 'No valid input provided'}), 400
        
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-usecase', methods=['POST'])
def analyze_usecase():
    try:
        language = request.form.get('language', 'en')
        use_case = request.form.get('use_case')
        is_cis = request.form.get('is_cis') == 'true'
        
        if not use_case:
            return jsonify({'error': 'No use case provided'}), 400
            
        # Analyze the use case
        result = use_case_analyzer.analyze_use_case(use_case, language)
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to analyze use case'}), 500
            
    except Exception as e:
        logger.error(f"Error in analyze-usecase endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Clean up old files before starting
    cleanup_old_files()
    app.run(debug=True) 