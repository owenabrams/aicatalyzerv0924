# app/blueprints/vector_manager/views.py

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os

from .vector_processing import create_vector_store, list_existing_stores

vector_manager_bp = Blueprint('vector_manager', __name__)

# Directory to save uploaded files for the new interface
UPLOAD_FOLDER = 'uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed extensions for file uploads
ALLOWED_EXTENSIONS = {'pdf'}

# Utility function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Existing Streamlit-based routes
@vector_manager_bp.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    try:
        pdf_file = request.files.get('pdf')
        store_type = request.form.get('store_type')

        if not pdf_file or not store_type:
            return jsonify({"error": "PDF file and store_type are required."}), 400

        # Save the uploaded file temporarily
        pdf_path = f"/tmp/{secure_filename(pdf_file.filename)}"
        pdf_file.save(pdf_path)

        # Create or update the vector store
        status_message = create_vector_store(pdf_path, store_type)
        return jsonify({"message": status_message}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@vector_manager_bp.route('/list_stores', methods=['GET'])
def list_stores():
    try:
        stores = list_existing_stores()
        return jsonify({"existing_stores": stores}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# New Flask-based upload form route
@vector_manager_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Handle file upload
        if 'pdf_file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['pdf_file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            try:
                # Call the vector store creation function
                status_message = create_vector_store(file_path, store_type='chunks')  # Adjust store_type as needed
                flash(status_message)
            except Exception as e:
                flash(f'Error creating vector stores: {str(e)}')

            return redirect(url_for('vector_manager.upload'))

    # Render the upload form for GET requests
    return render_template('upload.html')

# You may keep other routes and logic as needed
