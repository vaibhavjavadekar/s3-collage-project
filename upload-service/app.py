from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import requests
import os

app = Flask(__name__)
CORS(app) # Allows browser to talk directly to this service

s3_client_internal = boto3.client(
    's3', endpoint_url=os.environ.get('AWS_ENDPOINT_URL', 'http://localhost:4566'),
    aws_access_key_id='test', aws_secret_access_key='test', region_name='us-east-1'
)
s3_client_external = boto3.client(
    's3', endpoint_url='http://localhost:4566',
    aws_access_key_id='test', aws_secret_access_key='test', region_name='us-east-1'
)

BUCKET_NAME = 'collage-images'
METADATA_SVC_URL = os.environ.get('METADATA_SVC_URL', 'http://metadata-service:5004')

@app.route('/init', methods=['POST'])
def init_bucket():
    try:
        s3_client_internal.create_bucket(Bucket=BUCKET_NAME)
        # Configure CORS for LocalStack so browsers can upload large files directly
        cors_config = {
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['PUT', 'POST', 'GET', 'HEAD'],
                'AllowedOrigins': ['*']
            }]
        }
        s3_client_internal.put_bucket_cors(Bucket=BUCKET_NAME, CORSConfiguration=cors_config)
        return jsonify({"message": f"Bucket '{BUCKET_NAME}' created with CORS."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/generate-presigned-url', methods=['GET'])
def generate_presigned_url():
    user = request.headers.get('user')
    filename = request.args.get('filename')
    file_type = request.args.get('file_type', 'image')

    if not user or not filename:
        return jsonify({"error": "Missing user or filename"}), 400

    s3_key = f"{user}/{filename}"

    # Get URL from LocalStack
    presigned_url = s3_client_external.generate_presigned_url(
        'put_object', Params={'Bucket': BUCKET_NAME, 'Key': s3_key}, ExpiresIn=3600
    )

    # Save details to Postgres via Metadata service
    requests.post(f"{METADATA_SVC_URL}/records", json={
        "user": user, "filename": filename, "s3_key": s3_key, "file_type": file_type
    })

    return jsonify({"presigned_url": presigned_url, "s3_key": s3_key}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)