# Use a Node.js base image that supports apt-get
FROM node:20-slim

# Install FFmpeg for video/audio conversion
RUN apt-get update && apt-get install -y ffmpeg \
    # Clean up cache
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

# Copy package files and install dependencies
COPY package.json .
RUN npm install

# Copy application code
COPY . .

EXPOSE 3000
CMD [ "node", "server.js" ]