from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime
import time
import pytesseract
from PIL import Image
import io
import PyPDF2
import docx
import tempfile

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure Tesseract path (update this path according to your installation)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Dummy storage for processed data
processed_data = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        message_type = data.get('type', 'text')
        content = data.get('content', '')
        file_data = data.get('file')
        
        # Process based on type
        if message_type == 'text':
            # Process text message
            response = "I received your message: " + content
        elif message_type == 'file':
            # Process file message
            response = "File processed successfully: " + content
        else:
            response = "Unknown message type"
        
        # Add processing steps for logging
        steps = [{
            'domain': 'Message Processing',
            'details': f'Processed {message_type} message',
            'output': response
        }]
        
        return jsonify({
            'success': True,
            'response': response,
            'steps': steps
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/process_image', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    
    try:
        # Open image with PIL
        image = Image.open(file.stream)
        
        # Extract text using Tesseract
        text = pytesseract.image_to_string(image)
        
        if not text.strip():
            text = "No text could be extracted from the image."
        
        return jsonify({
            'success': True,
            'text': text,
            'steps': [{
                'domain': 'Image Processing',
                'details': f'Processed image file: {file.filename}',
                'output': 'Text extracted successfully'
            }]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No PDF file provided'}), 400
    
    file = request.files['pdf']
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file.save(temp_file.name)
            
            # Extract text from PDF
            with open(temp_file.name, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ''
                for page in pdf_reader.pages:
                    text += page.extract_text()
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        if not text.strip():
            text = "No text could be extracted from the PDF."
        
        return jsonify({
            'success': True,
            'text': text,
            'steps': [{
                'domain': 'PDF Processing',
                'details': f'Processed PDF file: {file.filename}',
                'output': 'Text extracted successfully'
            }]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/process_document', methods=['POST'])
def process_document():
    if 'document' not in request.files:
        return jsonify({'error': 'No document file provided'}), 400
    
    file = request.files['document']
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as temp_file:
            file.save(temp_file.name)
            
            # Extract text from document
            doc = docx.Document(temp_file.name)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        return jsonify({
            'success': True,
            'text': text
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@app.route('/process', methods=['POST'])
def process_input():
    data = request.get_json()
    
    # Process the input
    processed_entry = {
        'timestamp': datetime.now().isoformat(),
        'type': data.get('type', 'text'),
        'content': data.get('content', ''),
        'processed': True,
        'steps': [
            {
                'domain': 'Text Analysis',
                'details': 'Analyzing input content',
                'output': 'Input analyzed successfully'
            },
            {
                'domain': 'Context Processing',
                'details': 'Processing context and relationships',
                'output': 'Context processed successfully'
            },
            {
                'domain': 'Response Generation',
                'details': 'Generating appropriate response',
                'output': 'Response generated successfully'
            }
        ]
    }
    
    # If there's a file, add file processing steps
    if 'file' in data:
        processed_entry['steps'].append({
            'domain': 'File Processing',
            'details': f"Processing {data['file']['type']} file",
            'output': 'File processed successfully'
        })
    
    processed_data.append(processed_entry)
    
    # Save to JSON file
    with open('processed_data.json', 'w') as f:
        json.dump(processed_data, f, indent=2)
    
    return jsonify({
        'status': 'success',
        'message': 'Processing complete',
        'response': 'I have processed your input and understood it.',
        'steps': processed_entry['steps']
    })

@app.route('/generate/<feature>', methods=['POST'])
def generate_feature(feature):
    # Simulate feature generation
    time.sleep(2)
    
    return jsonify({
        'status': 'success',
        'message': f'{feature} generated successfully',
        'downloadUrl': f'/download/{feature}'
    })

if __name__ == '__main__':
    app.run(debug=True)
