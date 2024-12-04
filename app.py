from flask import Flask, request, send_file
import os
import tempfile
import zipfile

app = Flask(__name__)

def remove_extension(file):
    """Remove the file extension from a filename."""
    return ".".join(os.path.basename(file).split('.')[:-1])

def transcribe(file, outfolder='.'):
    """Transcribe the file using Transkun."""
    output_path = os.path.join(outfolder, remove_extension(file) + ".mid")
    os.system(f'transkun "{file}" "{output_path}" --device cpu')
    return output_path

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file", 400
    
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, file.filename)
        file.save(input_path)
        
        try:
            output_path = transcribe(input_path, temp_dir)
            return send_file(output_path, as_attachment=True)
        except Exception as e:
            return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)
