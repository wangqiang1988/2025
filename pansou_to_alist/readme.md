#  🎬 Quark 转存助手 (Quark-Transfer-Pro)
一个基于 Streamlit 开发的私人影音管理工具。支持全网搜索夸克云盘资源，并一键提交至 quark-auto-save 转存，最终自动入库你的 AList。

## 🌟 功能特点
直观交互：平铺式分类选择（电影/电视剧/动漫/综艺），无需深层菜单。

全网搜片：集成盘搜接口，实时获取最新夸克资源链接。

存入时间：清晰展示每个搜索结果的存入日期，方便筛选最新资源。

状态保持：深度优化 Streamlit 运行机制，点击转存后搜索列表不消失。

快捷链接：底部一键跳转 AList 存储、盘搜页面及夸克后台。

## 🛠️ 环境准备
Python 版本：推荐 3.8+

## 依赖服务：

已部署好的 AList

已部署好的 quark-auto-save 转存后端

盘搜 API 接口（如：http://localhost:8888）

# 🚀 快速开始
## 1. 克隆/下载本项目
```Bash

git clone https://github.com/your-username/pansou_to_alist.git
cd pansou_to_alist
```
## 2. 安装依赖
```Bash

pip install -r requirements.txt
```
## 3. 配置参数
修改 config_env.py 中的地址和 Token：

Python

search_api = "http://你的IP:8888/api/search"
token = "你的转存后台Token"
# 其他 AList/Quark URL 配置...
## 4. 运行程序
```Bash

streamlit run web_app.py
```
运行后，在浏览器访问 http://你的IP:8501 即可使用。

# 后台运行并将输出记录到 log.txt
nohup streamlit run web_app.py > log.txt 2>&1 &

## 📂 文件结构说明
web_app.py: Streamlit 网页主程序（前端界面）。

auto_quark.py: 核心逻辑脚本，处理搜索请求与转存任务提交。

config_env.py: 所有的 URL 地址、Token 和路径配置。

requirements.txt: 项目所需的 Python 第三方库。