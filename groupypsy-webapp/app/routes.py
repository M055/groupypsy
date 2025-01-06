from flask import Blueprint, render_template, request, url_for, jsonify, current_app
import os
import pandas as pd
import logging
from werkzeug.utils import secure_filename
from .data_processing import process_csv_files

# Define a Blueprint for the routes
main_bp = Blueprint('main', __name__)

# Configurations (this could be moved to a config file or app config)
UPLOAD_FOLDER = 'instance/uploads/'
PROCESSED_FOLDER = 'static/download/'
ALLOWED_EXTENSIONS = {'csv'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# Home route
@main_bp.route('/')
def index():
    return render_template('index.html')




# Upload route
@main_bp.route('/upload/<file_type>', methods=['POST'])
def upload_file(file_type):
    # Log the file_type variable to Flask logs
    logging.info(f"Received upload request for file type: {file_type}")
    allowed_types = ['students', 'projects', 'requirements', 'choices']
    if file_type not in allowed_types:
        return jsonify({'error': 'Invalid file type'}), 400
    
     # Get the sessionID from the request
    session_id = request.form.get('sessionID')
    if not session_id:
        return jsonify({'error': 'Session ID is missing'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file apparently'}), 400


    file = request.files.get('file')
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file or file type'}), 400

    # Save file to the correct location
    # filename = secure_filename(f"{file_type}.csv")
    # WITH SUFFIX
    filename = secure_filename(f"{session_id}_{file_type}.csv")
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    return jsonify({'message': f'{file_type} file uploaded successfully'}), 200


    


# Process file route
@main_bp.route('/process_files', methods=['POST'])
def process_files():
    try:
        # Get sessionID for files
        data = request.json
        session_id = data.get('sessionID')
        if not session_id:
            return jsonify({'error': 'Session ID is missing'}), 400
        
        # Generate file paths based on session ID
        required_files = ['students', 'projects', 'requirements', 'choices']
        file_paths = {
            file_type: os.path.join(UPLOAD_FOLDER, f"{session_id}_{file_type}.csv")
            for file_type in required_files
        }
        
        # Ensure all files exist
        missing_files = [file_type for file_type, path in file_paths.items() if not os.path.exists(path)]
        if missing_files:
            return jsonify({'error': f"Missing files: {', '.join(missing_files)}"}), 400


        # Process the files
        # file_paths = {file.split('.')[0]: os.path.join(UPLOAD_FOLDER, file) for file in required_files} # Dont need as we need sessionID now
        # processed_file = process_csv_files(file_paths, session_id) # Your processing function
        # download_url = url_for('main.download', filename=os.path.basename(processed_file))
        # download_url = process_csv_files(file_paths, session_id) # MO: from above 2 lines; changed to add plot below
        download_url, plot_path, column_order, check_mesg = process_csv_files(file_paths, session_id)
        plot_url = url_for('static', filename=f"plots/plot_{session_id}.png")


        return jsonify({'message': 'Files processed successfully', 'download_url': download_url, 'plot_url': plot_url, 'column_order': column_order, 'check_mesg': check_mesg}), 200

    except Exception as e:
        logging.error(f"Processing error: {e}")
        return jsonify({'error': str(e)}), 500


# CLear data route
@main_bp.route('/clear_data', methods=['POST'])
def clear_data():
    """
    Deletes all files associated with the given sessionID (sessionID as a suffix).
    """
    from flask import request, jsonify, current_app
    import glob
    
    try:
        data = request.get_json()

        # Retrieve the sessionID from the request
        session_id = request.get_json('sessionID')
        if not session_id:
            return jsonify({'error': 'Session ID is missing'}), 400

        # Define directories to search for files
        directories = [
            current_app.config['UPLOAD_FOLDER'],
            current_app.config['PROCESSED_FOLDER'],
            current_app.config['PLOT_FOLDER']
        ]

        # Find and delete files related to the sessionID
        deleted_files = []
        for directory in directories:
            files_to_delete = [x for x in glob.glob(directory+'/*') if session_id['sessionID'] in x]
            for file in files_to_delete:
                os.remove(file)
                deleted_files.append(file)

        # Log and return success
        current_app.logger.info(f"Deleted files: {deleted_files}")
        return jsonify({'message': 'All session data cleared successfully', 'deleted_files': deleted_files}), 200

    except Exception as e:
        current_app.logger.error(f"Error clearing data: {e}")
        return jsonify({'error': str(e)}), 500




# Table display route
@main_bp.route('/display_csv', methods=['GET'])
def display_csv():
    """
    Reads the processed CSV file and returns its content as JSON.
    """
    try:
        # Get the sessionID from query parameters
        session_id = request.args.get('sessionID')
        if not session_id:
            return jsonify({'error': 'Session ID is missing'}), 400

        # Define the path to the processed CSV file
        csv_path = os.path.join(current_app.config['PROCESSED_FOLDER'], f"Assignments_{session_id}.csv")
        if not os.path.exists(csv_path):
            return jsonify({'error': 'Processed file not found'}), 404

        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(csv_path)

        # Convert the DataFrame to a list of dictionaries (JSON serializable)
        data = df.to_dict(orient='records')
        column_order = list(df.columns)

        return jsonify({'data': data, 'column_order': column_order}), 200

    except Exception as e:
        current_app.logger.error(f"Error displaying CSV: {e}")
        return jsonify({'error': str(e)}), 500
    


# Help page route
@main_bp.route('/help', methods=['GET'])
def help():
    return render_template('help.html')



# Load examples
@main_bp.route('/examples', methods=['GET'])
def examples():
    """
    Serves example data for each input file in JSON format, including column order.
    """
    try:
        # Define the paths to the example files
        examples_folder = "static/examples"  # Adjust this to the actual folder
        example_files = {
            'students': os.path.join(examples_folder, 'Students.csv'),
            'projects': os.path.join(examples_folder, 'Projects.csv'),
            'requirements': os.path.join(examples_folder, 'Requirements.csv'),
            'choices': os.path.join(examples_folder, 'Choices.csv')
        }

        # Read and convert each file to JSON
        data = {}
        column_order = {}
        for key, file_path in example_files.items():
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                data[key] = df.to_dict(orient='records')  # Convert data to JSON
                column_order[key] = list(df.columns)      # Save column order

        return jsonify({'data': data, 'column_order': column_order}), 200

    except Exception as e:
        current_app.logger.error(f"Error serving examples: {e}")
        return jsonify({'error': str(e)}), 500



