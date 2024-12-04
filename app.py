from flask import Flask, request, jsonify
import os
import tempfile
import subprocess
from google.cloud import storage
from datetime import datetime

app = Flask(__name__)

# Google Cloud Storage setup
BUCKET_NAME = 'aira-bucket-backup'
GCS_CREDENTIALS_PATH = 'storageAdmin.json'

def remove_extension(file):
    """Remove the file extension from a filename."""
    return ".".join(os.path.basename(file).split('.')[:-1])

def transcribe(file, temp_dir):
    """Transcribe the file using Transkun."""
    output_path = os.path.join(temp_dir, remove_extension(file) + ".mid")
    try:
        subprocess.run(
            ['transkun', file, output_path, '--device', 'cpu'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Transcription failed: {e.stderr}")
    return output_path

def upload_to_gcs(local_file_path, bucket_name, destination_blob_name):
    """Uploads a file to Google Cloud Storage."""
    storage_client = storage.Client.from_service_account_json(GCS_CREDENTIALS_PATH)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_file_path)
    return f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file", 400
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    folder_name = f"output/{timestamp}"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, file.filename)
        file.save(input_path)
        try:
            output_path = transcribe(input_path, temp_dir)
            # Upload the transcribed file to the GCS folder
            gcs_url = upload_to_gcs(output_path, BUCKET_NAME, f"{folder_name}/{os.path.basename(output_path)}")
        except Exception as e:
            return str(e), 500
    
    # Return a success message with GCS URL
    return jsonify({"message": "Audio successfully transcribed", "file": gcs_url}), 200

if __name__ == '__main__':
    app.run(debug=True)
