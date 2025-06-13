from flask import Flask, render_template, request, jsonify
from policy_analyzer import PolicyAnalyzer
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

# Initialize PolicyAnalyzer
analyzer = PolicyAnalyzer(os.getenv('OPENROUTER_API_KEY'))
analyzer.initialize_databases(
    internal_path="data/internal",
    global_path="data/global"
)

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
    logger.debug("Received analyze request")
    logger.debug(f"Request files: {request.files}")
    logger.debug(f"Request form: {request.form}")
    
    try:
        # Get language preference (default to English)
        language = request.form.get('language', 'en')
        logger.debug(f"Language preference: {language}")
        
        if 'file' in request.files:
            logger.debug("File upload detected")
            # Handle file upload
            file = request.files['file']
            logger.debug(f"File details - filename: {file.filename}, content_type: {file.content_type}")
            
            # Validate file
            if file.filename == '':
                logger.warning("No file selected")
                return jsonify({'error': 'No file selected'}), 400
                
            if not allowed_file(file.filename):
                logger.warning(f"Invalid file type: {file.filename}")
                return jsonify({'error': 'Only PDF files are allowed'}), 400
            
            try:
                # Save file temporarily
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                logger.debug(f"Attempting to save file to: {filepath}")
                
                # Ensure the upload directory exists
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # Save the file
                file.save(filepath)
                logger.info(f"File saved successfully to: {filepath}")
                
                # Verify file was saved
                if not os.path.exists(filepath):
                    raise Exception(f"File was not saved successfully to {filepath}")
                
                # Analyze the policy
                logger.debug("Starting policy analysis")
                result = analyzer.analyze_new_policy(filepath, language=language)
                
                if result is None:
                    logger.error(f"Analysis failed for file: {filepath}")
                    return jsonify({'error': 'Analysis failed'}), 500
                
                logger.info("Analysis completed successfully")
                return jsonify(result)
                
            finally:
                # Clean up
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        logger.info(f"Temporary file removed: {filepath}")
                except Exception as e:
                    logger.error(f"Error removing temporary file {filepath}: {str(e)}")
            
        elif 'policy_text' in request.form:
            logger.debug("Text input detected")
            # Handle text input
            policy_text = request.form['policy_text']
            if not policy_text.strip():
                return jsonify({'error': 'Policy text cannot be empty'}), 400
                
            result = analyzer.analyze_new_policy_from_text(policy_text, language=language)
            if result is None:
                return jsonify({'error': 'Analysis failed'}), 500
                
            return jsonify(result)
            
        else:
            logger.warning("No file or text provided in request")
            return jsonify({'error': 'No file or text provided'}), 400
            
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': 'An error occurred during analysis'}), 500

if __name__ == '__main__':
    # Clean up old files before starting
    cleanup_old_files()
    app.run(debug=True) 