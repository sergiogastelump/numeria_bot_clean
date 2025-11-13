from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    txt = data.get('input', '')
    return jsonify({
        'prediction': f'Base para: {txt}',
        'confidence': 0.82,
        'market': 'over 2.5'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10001)
