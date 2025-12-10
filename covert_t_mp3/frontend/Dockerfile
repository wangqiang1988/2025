# Stage 1: Build the React application
FROM node:20-alpine as build
WORKDIR /app
COPY package.json .
COPY yarn.lock .
# Install dependencies
RUN npm install
# Copy source code and build
COPY . .
# Run Vite build command (assuming Vite is used)
RUN npm run build 

# Stage 2: Serve using Nginx
FROM nginx:alpine
# Copy static files from the build stage to Nginx content root
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80 (default HTTP port)
EXPOSE 80 
CMD ["nginx", "-g", "daemon off;"]