from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from audio_processor import load_audio, identify_swaras, get_audio_features
from raaga_matcher import RaagaMatcher

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

try:
    matcher = RaagaMatcher('ragas_complete.json')
except Exception as e:
    print(f"Error initializing matcher: {e}")
    matcher = None

@app.route('/api/identify', methods=['POST'])
def identify_raaga():
    try:
        if matcher is None:
            return jsonify({'error': 'Database not loaded'}), 500
        
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        audio_path = f'/tmp/{audio_file.filename}'
        os.makedirs('/tmp', exist_ok=True)
        audio_file.save(audio_path)
        
        y, sr = load_audio(audio_path)
        if y is None:
            return jsonify({'error': 'Could not load audio file'}), 400
        
        swaras = identify_swaras(y, sr)
        
        if not swaras or len(swaras) < 3:
            return jsonify({'error': 'Could not identify enough swaras'}), 400
        
        features = get_audio_features(y, sr)
        matches = matcher.match_to_melakartas(swaras)
        
        if not matches or matches[0][1]['score'] == 0:
            return jsonify({'error': 'Could not match to any raaga'}), 400
        
        top_match = matches[0]
        response = {
            'status': 'success',
            'identified_swaras': swaras,
            'top_match': {
                'raaga': top_match[0],
                'melakartha': top_match[1]['melakartha_num'],
                'confidence': round(top_match[1]['score'], 2),
            },
            'alternatives': [
                {
                    'raaga': m[0],
                    'melakartha': m[1]['melakartha_num'],
                    'confidence': round(m[1]['score'], 2)
                } for m in matches[1:4]
            ],
        }
        
        try:
            os.remove(audio_path)
        except:
            pass
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/feedback', methods=['POST'])
def store_feedback():
    try:
        data = request.json
        with open('feedback.json', 'a') as f:
            f.write(json.dumps(data) + '\n')
        return jsonify({'status': 'Feedback saved'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'API is running', 'version': '1.0.0', 'service': 'Music Prajna'}), 200

@app.route('/', methods=['GET'])
def home():
    return jsonify({'name': 'Music Prajna API', 'version': '1.0.0'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
```

**STEP 4:** Save (Ctrl + S) and close

**STEP 5:** Push:
```
git add app.py
git commit -m "fix app completely"
git push origin main