from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 设置最大上传限制（例如 2GB，方便上传视频）
app.config['MAX_CONTENT_LENGTH'] = 2000 * 1024 * 1024 

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件传输站 - 含进度条</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background: #f4f4f9; }
        .container { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .upload-section { margin-bottom: 30px; border: 2px dashed #ccc; padding: 20px; text-align: center; border-radius: 8px; }
        
        /* 进度条样式 */
        .progress-wrapper { display: none; margin-top: 20px; text-align: left; }
        .progress-bar { width: 100%; background-color: #e0e0e0; border-radius: 10px; overflow: hidden; }
        .progress-fill { width: 0%; height: 20px; background-color: #28a745; transition: width 0.1s; }
        #status { margin-top: 5px; font-size: 14px; color: #555; }

        .file-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #eee; }
        .btn { padding: 5px 12px; text-decoration: none; border-radius: 4px; font-size: 14px; margin-left: 5px; cursor: pointer; border: none; }
        .btn-download { background: #007bff; color: white; }
        .btn-delete { background: #dc3545; color: white; }
        .btn-upload { background: #333; color: white; width: 100%; margin-top: 10px; padding: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 视频/文件传输站</h2>
        
        <div class="upload-section">
            <input type="file" id="fileInput">
            <button class="btn btn-upload" onclick="uploadFile()">开始上传</button>
            
            <div class="progress-wrapper" id="progressWrapper">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div id="status">准备中...</div>
            </div>
        </div>

        <h3>文件列表</h3>
        <div id="fileList">
            {% for file in files %}
            <div class="file-item">
                <span>{{ file }}</span>
                <div>
                    <a href="/download/{{ file }}" class="btn btn-download">下载</a>
                    <a href="/delete/{{ file }}" class="btn btn-delete" onclick="return confirm('确定要删除吗？')">删除</a>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
    function uploadFile() {
        var fileInput = document.getElementById('fileInput');
        if (fileInput.files.length === 0) {
            alert("请先选择文件！");
            return;
        }

        var file = fileInput.files[0];
        var formData = new FormData();
        formData.append("file", file);

        var xhr = new XMLHttpRequest();
        
        // 显示进度条
        document.getElementById('progressWrapper').style.display = 'block';
        
        // 监听进度事件
        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                var percentComplete = (e.loaded / e.total) * 100;
                document.getElementById('progressFill').style.width = percentComplete + '%';
                document.getElementById('status').innerHTML = "已上传 " + Math.round(percentComplete) + "%";
            }
        };

        xhr.onload = function() {
            if (xhr.status == 200) {
                document.getElementById('status').innerHTML = "上传成功！正在刷新...";
                setTimeout(function(){ location.reload(); }, 1000);
            } else {
                alert("上传失败，请检查网络或文件大小限制。");
            }
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
    if 'file' not in request.files:
        return "No file", 400
    file = request.files['file']
    if file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
    return "OK", 200

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/delete/<filename>')
def delete_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)