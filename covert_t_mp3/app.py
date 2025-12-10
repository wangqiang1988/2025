import os
import subprocess
from flask import Flask, request, render_template, send_file, redirect, url_for

app = Flask(__name__)

# 从环境变量加载配置
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', '/app/data/uploads')
app.config['OUTPUT_FOLDER'] = os.environ.get('OUTPUT_FOLDER', '/app/data/outputs')
# 设置文件大小限制为 20MB
# 获取环境变量值。如果设置了环境变量，则尝试转换；否则使用默认计算值。
max_size_env = os.environ.get('MAX_FILE_SIZE')

if max_size_env:
    # 如果环境变量被设置，清理字符串并尝试转换
    try:
        # 移除空格和注释部分，只保留数字
        clean_size = max_size_env.split('#')[0].strip()
        app.config['MAX_CONTENT_LENGTH'] = int(clean_size)
    except ValueError:
        # 如果转换失败，使用默认值
        app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024 # 20MB 默认值
else:
    # 环境变量未设置，直接使用默认计算值
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

# 简单路由：主页
@app.route('/')
def index():
    # 渲染主页模板，展示功能和上传按钮
    return render_template('index.html')

# 转换路由：处理文件上传和转换
@app.route('/convert', methods=['POST'])
def convert_video():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    if file:
        original_filename = file.filename
        
        # 1. 检查文件类型（简单的MIME类型检查）
        if not file.mimetype.startswith('video/'):
     # 如果不是视频MIME类型，则拒绝
            return f"Invalid file type: {file.mimetype}. Only video files are supported.", 400

        # 2. 保存上传文件
        input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        file.save(input_filepath)
        
        # 3. 定义输出路径
        output_filename = os.path.splitext(original_filename)[0] + '.mp3'
        output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # 4. 调用 FFmpeg 进行转换
        try:
            # -i 输入文件
            # -vn 禁用视频流
            # -acodec libmp3lame 使用高质量 MP3 编码器
            # -q:a 2 设定音频质量
            subprocess.run([
                'ffmpeg', '-i', input_filepath, '-vn', 
                '-acodec', 'libmp3lame', '-q:a', '2', 
                output_filepath
            ], check=True, capture_output=True, text=True)
            
        except subprocess.CalledProcessError as e:
            # 清理失败的文件
            os.remove(input_filepath)
            print(f"FFmpeg Error: {e.stderr}")
            return "Video conversion failed.", 500
        
        # 5. 提供文件下载
        # 注意：此处提供下载后，建议实现一个异步任务清理 input_filepath 和 output_filepath
        return send_file(
            output_filepath, 
            as_attachment=True, 
            download_name=output_filename,
            mimetype='audio/mp3'
        )

# 6. 文件清理 (可选，但推荐)
# 这是一个更复杂的功能，通常使用后台任务实现，此处省略。

if __name__ == '__main__':
    # 确保在启动前创建目录
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000)