from flask import Flask, render_template_string, send_file, request
import requests
import io
import os
from PIL import Image

app = Flask(__name__)
DOWNLOAD_SVC_URL = os.environ.get('DOWNLOAD_SVC_URL', 'http://localhost:5002')

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>S3 Cloud Drive</title>
    <style>
        body { margin: 0; font-family: 'Segoe UI', Tahoma, sans-serif; display: flex; height: 100vh; background: #f4f7f6; }
        #left-panel { width: 250px; background-color: #2c3e50; color: white; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        .user-box { background: #34495e; padding: 10px; border-radius: 5px; }
        .user-box input { width: 100%; padding: 5px; margin-top: 5px; box-sizing: border-box; }
        button.nav-btn { background: #18bc9c; color: white; border: none; padding: 12px; cursor: pointer; border-radius: 4px; font-weight: bold; text-align: left; }
        
        #right-panel { flex-grow: 1; padding: 40px; overflow-y: auto; }
        .content-section { display: none; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .content-section.active { display: block; }
        
        select, input[type="file"] { margin-top: 5px; padding: 8px; width: 100%; max-width: 400px; display: block; margin-bottom: 15px; }
        button.action-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 16px; }
        #upload-status { margin-top: 15px; font-weight: bold; color: #d35400; }
        #collage-img { max-width: 100%; margin-top: 20px; border: 5px solid #bdc3c7; border-radius: 5px; display: none; }
    </style>
</head>
<body>
    <div id="left-panel">
        <h2>S3 Cloud Drive</h2>
        <div class="user-box">
            <label>Current User:</label>
            <input type="text" id="username" value="alice">
        </div>
        <button class="nav-btn" onclick="showSection('upload-section')">☁️ Upload File</button>
        <button class="nav-btn" onclick="showSection('collage-section')">🖼️ View Collage</button>
    </div>

    <div id="right-panel">
        <div id="upload-section" class="content-section active">
            <h2>Upload File</h2>
            <label>File Type:</label>
            <select id="fileType"><option value="image">Image</option><option value="video">Video</option></select>
            <label>Select File:</label>
            <input type="file" id="fileInput">
            <button class="action-btn" onclick="uploadFile()">Start Upload</button>
            <div id="upload-status"></div>
        </div>

        <div id="collage-section" class="content-section">
            <h2>Your Image Collage</h2>
            <button class="action-btn" onclick="loadCollage()">Generate Collage</button>
            <br>
            <img id="collage-img" alt="User Collage" />
        </div>
    </div>

    <script>
        function showSection(sectionId) {
            document.querySelectorAll('.content-section').forEach(sec => sec.classList.remove('active'));
            document.getElementById(sectionId).classList.add('active');
        }

        async function uploadFile() {
            const user = document.getElementById('username').value;
            const fileInput = document.getElementById('fileInput');
            const fileType = document.getElementById('fileType').value;
            const statusDiv = document.getElementById('upload-status');
            
            if (!user || fileInput.files.length === 0) return;
            const file = fileInput.files[0];
            
            try {
                statusDiv.innerText = "Requesting secure upload URL...";
                const urlResp = await fetch(`http://localhost:5001/generate-presigned-url?filename=${file.name}&file_type=${fileType}`, {
                    headers: { 'user': user }
                });
                const urlData = await urlResp.json();
                
                statusDiv.innerText = "Uploading directly to S3...";
                const uploadResp = await fetch(urlData.presigned_url, { method: 'PUT', body: file });

                if (uploadResp.ok) {
                    statusDiv.innerText = "✅ Upload completed successfully!";
                    fileInput.value = "";
                } else { throw new Error("Upload Failed"); }
            } catch (error) { statusDiv.innerText = "❌ Error: " + error.message; }
        }

        function loadCollage() {
            const user = document.getElementById('username').value;
            const img = document.getElementById('collage-img');
            img.src = `/collage-image?user=${user}&t=${new Date().getTime()}`;
            img.style.display = 'block';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/collage-image')
def generate_collage():
    user = request.args.get('user')
    resp = requests.get(f"{DOWNLOAD_SVC_URL}/images", headers={"user": user})
    
    if resp.status_code != 200 or not resp.json().get('images'):
        return f"No images found", 404
    
    image_keys = resp.json()['images']
    images = []
    for key in image_keys:
        img_resp = requests.get(f"{DOWNLOAD_SVC_URL}/download/{key}")
        if img_resp.status_code == 200:
            try:
                img = Image.open(io.BytesIO(img_resp.content))
                img = img.resize((300, 300))
                images.append(img)
            except Exception:
                pass
            
    if not images: return "Failed to process", 500

    widths, heights = zip(*(i.size for i in images))
    collage = Image.new('RGB', (sum(widths), max(heights)))
    x_offset = 0
    for img in images:
        collage.paste(img, (x_offset,0))
        x_offset += img.size[0]

    img_io = io.BytesIO()
    collage.save(img_io, 'JPEG', quality=85)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)