from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for, make_response
import os
import urllib.parse
from werkzeug.utils import secure_filename


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 设置最大上传限制 2GB
app.config['MAX_CONTENT_LENGTH'] = 2000 * 1024 * 1024 

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件传输站</title>
    <style>
        body { font-family: -apple-system, sans-serif; margin: 20px; background: #f4f4f9; }
        .container { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .upload-section { margin-bottom: 30px; border: 2px dashed #ccc; padding: 20px; text-align: center; border-radius: 8px; }
        .progress-wrapper { display: none; margin-top: 20px; text-align: left; }
        .progress-bar { width: 100%; background-color: #e0e0e0; border-radius: 10px; overflow: hidden; }
        .progress-fill { width: 0%; height: 20px; background-color: #28a745; transition: width 0.1s; }
        .file-item { display: flex; justify-content: space-between; align-items: center; padding: 12px; border-bottom: 1px solid #eee; }
        .btn { padding: 8px 15px; text-decoration: none; border-radius: 6px; font-size: 14px; cursor: pointer; border: none; }
        .btn-download { background: #007bff; color: white; }
        .btn-delete { background: #dc3545; color: white; margin-left: 5px; }
        .btn-upload { background: #333; color: white; width: 100%; margin-top: 10px; padding: 12px; font-size: 16px; }
        span { word-break: break-all; padding-right: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 文件传输站</h2>
        <div class="upload-section">
            <input type="file" id="fileInput">
            <button class="btn btn-upload" onclick="uploadFile()">开始上传</button>
            <div class="progress-wrapper" id="progressWrapper">
                <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
                <div id="status" style="font-size: 12px; margin-top:5px;">准备中...</div>
            </div>
        </div>
        <h3>文件列表</h3>
        <div id="fileList">
            {% for file in files %}
            <div class="file-item">
    <span>{{ file }}</span>
    <div style="display: flex;">
        <a href="/download/{{ file }}" class="btn btn-download">下载/保存</a>
        <a href="/delete/{{ file }}" class="btn btn-delete" onclick="return confirm('确定要删除吗？')">删除</a>
    </div>
</div>
            {% endfor %}
        </div>
    </div>

    <script>
    function uploadFile() {
        var fileInput = document.getElementById('fileInput');
        if (fileInput.files.length === 0) { alert("请先选择文件！"); return; }
        var file = fileInput.files[0];
        var formData = new FormData();
        formData.append("file", file);
        var xhr = new XMLHttpRequest();
        document.getElementById('progressWrapper').style.display = 'block';
        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                var percent = (e.loaded / e.total) * 100;
                document.getElementById('progressFill').style.width = percent + '%';
                document.getElementById('status').innerHTML = "已上传 " + Math.round(percent) + "%";
            }
        };
        xhr.onload = function() {
            if (xhr.status == 200) { location.reload(); }
            else { alert("上传失败"); }
        };
        xhr.open("POST", "/upload", true);
        xhr.send(formData);
    }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template_string(HTML_TEMPLATE, files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return "No file", 400
    file = request.files['file']
    if file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
    return "OK", 200

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return "文件不存在", 404

    encoded_filename = urllib.parse.quote(filename)
    
    from flask import send_file
    response = make_response(send_file(file_path))

    content_disposition = f"attachment; filename=\"{encoded_filename}\"; filename*=UTF-8''{encoded_filename}"
    
    response.headers["Content-Disposition"] = content_disposition
    response.headers["Content-Type"] = "application/octet-stream"
    response.headers["Cache-Control"] = "no-cache"

    return response

@app.route('/delete/<filename>')
def delete_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)