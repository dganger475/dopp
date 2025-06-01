from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from utils.files.utils import allowed_file, generate_face_filename
from utils.db.storage import get_storage
from models.face import Face
from utils.face.indexing import index_face
import logging

face_upload = Blueprint('face_upload', __name__)
logger = logging.getLogger(__name__)

@face_upload.route('/upload', methods=['POST'])
def upload_face():
    """Upload a face image."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
        
    try:
        # Get the next face ID from the database
        next_id = Face.get_next_id()
        
        # Generate anonymized filename
        filename = generate_face_filename(next_id)
        
        # Get storage backend (B2)
        storage = get_storage()
        
        # Save file to B2
        success, result = storage.save(file, filename, folder='faces')
        if not success:
            return jsonify({'error': f'Failed to save file: {result}'}), 500
            
        # Create face record in database
        face = Face(
            filename=filename,  # Store the anonymized filename
            year=request.form.get('year'),
            state=request.form.get('state'),
            school=request.form.get('school'),
            page=request.form.get('page')
        )
        face.save()
        
        # Index the face
        index_face(face)
        
        return jsonify({
            'success': True,
            'face_id': face.id,
            'filename': filename
        })
        
    except Exception as e:
        logger.error(f"Error uploading face: {str(e)}")
        return jsonify({'error': str(e)}), 500 