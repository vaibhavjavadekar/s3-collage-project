from flask import Flask, jsonify, send_file, request
import boto3
import requests
import os
import io

app = Flask(__name__)

s3_client = boto3.client(
    's3', endpoint_url=os.environ.get('AWS_ENDPOINT_URL', 'http://localhost:4566'),
    aws_access_key_id='test', aws_secret_access_key='test', region_name='us-east-1'
)
BUCKET_NAME = 'collage-images'
METADATA_SVC_URL = os.environ.get('METADATA_SVC_URL', 'http://metadata-service:5004')

@app.route('/images', methods=['GET'])
def list_user_images():
    user = request.headers.get('user')
    if not user:
        return jsonify({"error": "Missing user header"}), 400

    resp = requests.get(f"{METADATA_SVC_URL}/records", headers={"user": user})
    if resp.status_code != 200:
        return jsonify({"error": "Failed to fetch DB records"}), 500
    
    files = resp.json().get('files', [])
    # Only return images for the collage
    images = [f['s3_key'] for f in files if f['file_type'] == 'image']
    return jsonify({"images": images}), 200

@app.route('/download/<path:s3_key>', methods=['GET'])
def download_image(s3_key):
    try:
        file_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        return send_file(io.BytesIO(file_obj['Body'].read()), mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"error": str(e)}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)