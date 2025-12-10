import os
import subprocess
import time
import threading
import glob
from flask import Flask, request, render_template, send_file, redirect, url_for, g

app = Flask(__name__)

# --- 配置 ---
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', '/app/data/uploads')
app.config['OUTPUT_FOLDER'] = os.environ.get('OUTPUT_FOLDER', '/app/data/outputs')
# 文件大小限制（已在 Dockerfile 中修复）
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024 # 20MB 默认值
# 文件保留时间：3600秒 = 1小时
CLEANUP_INTERVAL = 3600 

# 确保在启动前创建目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)


# --- 异步文件清理函数 ---
def cleanup_files():
    """定期扫描上传和输出目录，删除超过保留时间的文件。"""
    while True:
        now = time.time()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] Running cleanup task...")
        
        folders = [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]
        
        for folder in folders:
            # 搜索文件夹中的所有文件
            for filepath in glob.glob(os.path.join(folder, '*')):
                # 检查文件是否为文件，并且是否超过保留时间
                if os.path.isfile(filepath):
                    file_age = now - os.path.getmtime(filepath)
                    if file_age > CLEANUP_INTERVAL:
                        try:
                            os.remove(filepath)
                            print(f"Cleaned up old file: {filepath}")
                        except OSError as e:
                            print(f"Error deleting file {filepath}: {e}")
                            
        time.sleep(CLEANUP_INTERVAL) # 每小时执行一次


# --- 辅助函数：确定语言 ---
def get_locale():
    """根据请求头确定用户偏好的语言"""
    # 简单的逻辑：检查 Accept-Language 头是否包含 'zh'
    accept_language = request.headers.get('Accept-Language', '')
    if 'zh' in accept_language.lower():
        return 'zh'
    return 'en'


# --- 路由 ---

@app.before_request
def before_request():
    """在每个请求前确定语言"""
    g.locale = get_locale()

@app.route('/')
def index():
    """主页：根据语言加载不同的模板"""
    if g.locale == 'zh':
        return render_template('index_zh.html')
    # 默认或英文环境使用英文模板
    return render_template('index_en.html')


@app.route('/convert', methods=['POST'])
def convert_video():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    if file:
        # 检查文件类型：允许所有视频或音频文件
        if not (file.mimetype.startswith('video/') or file.mimetype.startswith('audio/')):
             return f"Invalid file type: {file.mimetype}. Only video or audio files are supported.", 400
        
        original_filename = file.filename
        
        # 1. 保存上传文件
        input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        file.save(input_filepath)
        
        # 2. 定义输出路径
        base_name = os.path.splitext(original_filename)[0]
        output_filename = base_name + '.mp3'
        output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # 3. 调用 FFmpeg 进行转换
        try:
            # -i 输入文件, -vn 禁用视频流, -acodec libmp3lame MP3编码器, -q:a 2 质量
            subprocess.run([
                'ffmpeg', '-i', input_filepath, '-acodec', 'libmp3lame', '-q:a', '2', 
                output_filepath
            ], check=True, capture_output=True, text=True)
            
        except subprocess.CalledProcessError as e:
            # 清理失败的文件
            os.remove(input_filepath)
            print(f"!!! FFmpeg Failed !!!")
            print(f"STDOUT: {e.stdout}") 
            print(f"STDERR: {e.stderr}")
            # 返回 FFmpeg 报告的错误信息
            return f"Conversion failed. FFmpeg reports: {e.stderr}", 500
        
        # 4. 提供文件下载
        # 注意：文件将在后台清理线程中删除
        return send_file(
            output_filepath, 
            as_attachment=True, 
            download_name=output_filename,
            mimetype='audio/mp3'
        )

if __name__ == '__main__':
    # 启动后台清理线程
    cleanup_thread = threading.Thread(target=cleanup_files, daemon=True)
    cleanup_thread.start()
    
    app.run(host='0.0.0.0', port=5000)