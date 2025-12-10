# ----------------------------------------------------------------------
# 前端服务 Dockerfile (多阶段构建: React + Nginx)
# ----------------------------------------------------------------------

# === 第一阶段: 构建 React 应用 ===
FROM node:20-alpine AS build

# 设置工作目录
WORKDIR /app

# 复制依赖清单
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 执行构建命令 (假设 React 项目的构建输出在 build 目录)
RUN npm run build

# === 第二阶段: 部署到 Nginx 服务器 ===
# 使用轻量级 Nginx 镜像提供静态文件服务
FROM nginx:stable-alpine

# 1. 复制自定义 Nginx 配置
# 这个配置 (nginx.conf) 将处理静态文件服务和 API 路由转发。
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 2. 复制第一阶段构建的静态文件
# 将 React 构建产物 (通常在 /app/build) 复制到 Nginx 的默认静态文件目录
COPY --from=build /app/build /usr/share/nginx/html

# 3. 暴露端口
EXPOSE 80

# 4. 容器启动时自动运行 Nginx (默认行为)
# CMD ["nginx", "-g", "daemon off;"] # Nginx 基础镜像已包含此命令