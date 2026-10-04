from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class FileMetadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    s3_key = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/records', methods=['POST'])
def add_record():
    data = request.json
    new_file = FileMetadata(
        username=data['user'],
        filename=data['filename'],
        s3_key=data['s3_key'],
        file_type=data.get('file_type', 'image')
    )
    db.session.add(new_file)
    db.session.commit()
    return jsonify({"message": "Metadata saved"}), 201

@app.route('/records', methods=['GET'])
def get_records():
    user = request.headers.get('user')
    files = FileMetadata.query.filter_by(username=user).all()
    result = [{"filename": f.filename, "s3_key": f.s3_key, "file_type": f.file_type} for f in files]
    return jsonify({"files": result}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)