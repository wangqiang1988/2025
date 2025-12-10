const express = require('express');
const multer = require('multer');
const ffmpeg = require('fluent-ffmpeg');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = 3000;
// 20 MB limit
const MAX_FILE_SIZE = 20 * 1024 * 1024; 

// Directory for temporary file storage within the container
const UPLOAD_DIR = path.join(__dirname, 'temp_uploads');
if (!fs.existsSync(UPLOAD_DIR)) {
    fs.mkdirSync(UPLOAD_DIR);
}

// Configure Multer storage
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, UPLOAD_DIR);
    },
    filename: (req, file, cb) => {
        // Use original file name with timestamp to prevent collisions
        cb(null, `${Date.now()}-${file.originalname.replace(/[^a-zA-Z0-9.]/g, '_')}`);
    }
});

// Multer middleware with size and type filtering
const upload = multer({
    storage: storage,
    limits: { fileSize: MAX_FILE_SIZE },
    fileFilter: (req, file, cb) => {
        if (file.mimetype === 'video/mp4') {
            cb(null, true);
        } else {
            cb(new Error('Only MP4 files are allowed!'), false);
        }
    }
}).single('videoFile'); 

// Enable CORS for frontend communication
app.use(cors());

// Helper function to clean up files
function cleanUp(filePath) {
    if (filePath && fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        console.log(`Cleaned up: ${filePath}`);
    }
}

// POST endpoint for file upload and conversion
app.post('/api/convert', (req, res) => {
    upload(req, res, async (err) => {
        if (err instanceof multer.MulterError) {
            if (err.code === 'LIMIT_FILE_SIZE') {
                return res.status(400).json({ error: '文件大小超过 20MB 限制。' });
            }
            return res.status(400).json({ error: err.message });
        } else if (err) {
            return res.status(500).json({ error: '上传过程中发生未知错误。' });
        }

        if (!req.file) {
            return res.status(400).json({ error: '未上传文件。' });
        }

        const inputPath = req.file.path;
        const mp3FileName = `converted-${Date.now()}.mp3`;
        const outputPath = path.join(UPLOAD_DIR, mp3FileName);

        try {
            // FFmpeg conversion
            await new Promise((resolve, reject) => {
                ffmpeg(inputPath)
                    .noVideo()              // Disable video stream
                    .audioBitrate('192k')   // Set audio bitrate
                    .audioCodec('libmp3lame') // Ensure MP3 codec is used
                    .on('end', () => {
                        resolve();
                    })
                    .on('error', (err) => {
                        reject(new Error(`FFmpeg 转换失败: ${err.message}`));
                    })
                    .save(outputPath);
            });

            // Return download URL
            const downloadUrl = `/api/download/${mp3FileName}`;
            res.json({ message: 'Conversion successful!', downloadUrl: downloadUrl });

        } catch (convertError) {
            res.status(500).json({ error: convertError.message });
        } finally {
            // Delete the original uploaded MP4 file
            cleanUp(inputPath);
        }
    });
});

// GET endpoint for file download
app.get('/api/download/:filename', (req, res) => {
    const filename = req.params.filename;
    const filePath = path.join(UPLOAD_DIR, filename);

    if (fs.existsSync(filePath)) {
        res.download(filePath, filename, (err) => {
            if (err) {
                console.error('Download error:', err.message);
                res.status(500).send('无法下载文件。');
            }
            // IMPORTANT: Clean up the converted MP3 file after download starts/finishes
            cleanUp(filePath);
        });
    } else {
        res.status(404).send('文件未找到。');
    }
});

app.listen(PORT, () => {
    console.log(`Backend API listening on port ${PORT}`);
});