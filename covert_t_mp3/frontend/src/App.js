import React, { useState, useCallback } from 'react';
import './index.css';

// IMPORTANT: Use the Docker Compose service name 'backend' instead of 'localhost'
const API_BASE_URL = 'http://backend:3000'; 
const MAX_FILE_SIZE_MB = 20;

function App() {
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState('ready'); // ready, uploading, converting, success, error
    const [message, setMessage] = useState('请选择一个小于 20MB 的 MP4 文件。');
    const [downloadUrl, setDownloadUrl] = useState('');
    const [progress, setProgress] = useState(0);

    const handleFileChange = (event) => {
        const selectedFile = event.target.files[0];
        setDownloadUrl('');
        setProgress(0);
        
        if (!selectedFile) {
            setFile(null);
            setMessage('请选择一个小于 20MB 的 MP4 文件。');
            setStatus('ready');
            return;
        }

        // 1. Client-side file type validation
        if (selectedFile.type !== 'video/mp4') {
            setMessage('错误: 仅支持 MP4 文件格式。');
            setStatus('error');
            return;
        }

        // 2. Client-side file size validation (20MB)
        if (selectedFile.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
            setMessage(`错误: 文件必须小于 ${MAX_FILE_SIZE_MB}MB。`);
            setStatus('error');
            return;
        }

        setFile(selectedFile);
        setStatus('ready');
        setMessage(`已选择文件: ${selectedFile.name}。点击 "开始转换" 按钮。`);
    };

    const handleUpload = useCallback(async () => {
        if (!file) {
            setMessage('请先选择 MP4 文件。');
            return;
        }

        setStatus('uploading');
        setMessage('文件上传中...');

        const formData = new FormData();
        formData.append('videoFile', file);
        
        // Custom XMLHttpRequest for progress tracking (fetch doesn't support it easily)
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE_URL}/api/convert`, true);

        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                const percent = Math.round((event.loaded / event.total) * 100);
                setProgress(percent);
                setMessage(`文件上传中: ${percent}%`);
            }
        };

        xhr.onload = function() {
            if (xhr.status === 200) {
                // Conversion success
                const data = JSON.parse(xhr.responseText);
                setDownloadUrl(`${API_BASE_URL}${data.downloadUrl}`);
                setMessage('✅ 转换成功！点击按钮下载您的 MP3 文件。');
                setStatus('success');
            } else {
                // Conversion/Upload failure
                const data = JSON.parse(xhr.responseText);
                setMessage(`转换失败: ${data.error || '后端服务错误。'}`);
                setStatus('error');
            }
            // Clean up file input state regardless of success
            setFile(null);
            document.getElementById('fileInput').value = '';
            setProgress(0);
        };

        xhr.onerror = function() {
            setMessage('网络连接错误或后端服务不可用。');
            setStatus('error');
            setFile(null);
            document.getElementById('fileInput').value = '';
            setProgress(0);
        };

        // Start conversion message after upload progress is likely complete (or on upload end)
        xhr.upload.onloadend = function() {
            if (xhr.status !== 200 && status !== 'error') {
                setMessage('文件已上传，后端正在进行 FFmpeg 转换... (请耐心等待)');
                setStatus('converting'); // Transition to converting status
            }
        };

        xhr.send(formData);

    }, [file, status]);


    const renderActionButton = () => {
        switch (status) {
            case 'uploading':
            case 'converting':
                return (
                    <div className="status-indicator">
                        <div className="loading-spinner"></div>
                        <p>{message}</p>
                        {status === 'uploading' && <div className="progress-bar-container"><div className="progress-bar" style={{width: `${progress}%`}}></div></div>}
                    </div>
                );
            case 'success':
                return (
                    <a href={downloadUrl} className="download-btn" target="_blank" rel="noopener noreferrer">
                        ⬇️ 下载 MP3 文件
                    </a>
                );
            case 'error':
                return (
                    <button className="upload-btn" onClick={() => document.getElementById('fileInput').click()}>
                        重新选择文件
                    </button>
                );
            case 'ready':
            default:
                return (
                    <>
                        <button 
                            className="upload-btn"
                            onClick={() => document.getElementById('fileInput').click()}
                        >
                            {file ? `更改文件: ${file.name.substring(0, 20)}...` : '➕ 点击上传 MP4 文件'}
                        </button>
                        {file && (
                            <button className="convert-btn" onClick={handleUpload}>
                                🚀 开始转换
                            </button>
                        )}
                    </>
                );
        }
    };


    return (
        <div className="container">
            <header className="header">
                <h1>全球 MP4 至 MP3 转换器 🌍</h1>
                <p>快速、免费、安全的视频转音频服务</p>
            </header>

            <div className="upload-box">
                <input
                    type="file"
                    id="fileInput"
                    accept="video/mp4"
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                />
                
                <p className="size-limit">
                    **文件大小限制: {MAX_FILE_SIZE_MB}MB**
                </p>
                
                {renderActionButton()}

                <p className={`message ${status}`}>{message}</p>
            </div>
            
            {/* 功能简介 */}
            <div className="features-section">
                <h2>我们的服务优势</h2>
                <div className="feature-cards">
                    <div className="card">
                        <h3>🆓 产品免费试用</h3>
                        <p>完全免费，无需注册或付费即可开始转换。</p>
                    </div>
                    <div className="card">
                        <h3>⚡️ 极速转换</h3>
                        <p>利用高性能的 FFmpeg 服务，快速完成转换。</p>
                    </div>
                    <div className="card">
                        <h3>🔒 数据安全</h3>
                        <p>您的文件在下载后将立即被自动删除，保障隐私安全。</p>
                    </div>
                </div>
            </div>

            <div className="footer-info">
                <p>面向全球用户。请务必遵守文件大小限制。</p>
            </div>
        </div>
    );
}

export default App;