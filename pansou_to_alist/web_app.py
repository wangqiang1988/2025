import streamlit as st
import requests
import time
import config_env
from auto_quark import add_and_run_task

# 页面基础配置
st.set_page_config(page_title="Quark 转存助手", page_icon="🎬", layout="wide")

# --- 1. 初始化状态 (确保点击转存时结果不消失) ---
if 'results' not in st.session_state:
    st.session_state.results = []
if 'last_search' not in st.session_state:
    st.session_state.last_search = ""

def search_api(keyword):
    """从接口获取资源"""
    payload = {"kw": keyword, "cloud_types": ["quark"]}
    try:
        response = requests.post(config_env.search_api, json=payload, timeout=10)
        return response.json().get("data", {}).get("merged_by_type", {}).get("quark", [])
    except Exception as e:
        st.error(f"搜索失败: {e}")
        return []

# --- 2. 顶部分类选择 (直接显示，不使用折叠菜单) ---
st.title("🎬 私人影音转存助手")

# 使用 columns 布局让顶层选择更整齐
col_cat, col_info = st.columns([2, 1])
with col_cat:
    # 直接平铺单选框
    category = st.radio(
        "**📁 第一步：选择入库分类**",
        ["电影", "电视剧", "动漫", "综艺"],
        horizontal=True,
        index=0 # 默认选电影
    )

with col_info:
    save_root = f"/alist/{category}"
    st.info(f"📍 当前目标路径: `{save_root}`")

st.markdown("---")

# --- 3. 搜索区域 ---
st.markdown("**🔍 第二步：搜索资源**")
col_input, col_btn = st.columns([4, 1])
with col_input:
    kw = st.text_input("请输入资源名称", value=st.session_state.last_search, label_visibility="collapsed", placeholder="输入关键词，例如：巨洪")
with col_btn:
    if st.button("开始搜索", use_container_width=True, type="primary"):
        if kw:
            with st.spinner('正在搜寻资源...'):
                st.session_state.results = search_api(kw)
                st.session_state.last_search = kw
        else:
            st.warning("内容不能为空")

# --- 4. 结果展示 (包含时间显示) ---
if st.session_state.results:
    st.subheader(f"✅ 找到 {len(st.session_state.results)} 条结果")
    
    # 标题行
    st.markdown("""
        <div style="display: flex; background-color: #f0f2f6; padding: 10px; border-radius: 5px; font-weight: bold;">
            <div style="flex: 5;">资源名称 / 存入时间</div>
            <div style="flex: 3;">链接预览</div>
            <div style="flex: 2; text-align: center;">操作</div>
        </div>
    """, unsafe_allow_html=True)

    for idx, item in enumerate(st.session_state.results):
        title = item.get('note', '未知标题').replace("/", "_")
        url = item.get('url', '')
        # 提取时间字段
        pub_time = item.get('datetime') or item.get('pub_time') or "时间未知"
        
        with st.container():
            c1, c2, c3 = st.columns([5, 3, 2])
            
            with c1:
                st.write(f"**{title}**")
                st.caption(f"📅 存入时间: {pub_time}")
            
            with c2:
                st.text_input("url", value=url, key=f"url_{idx}", label_visibility="collapsed", disabled=True)
            
            with c3:
                # 传入 category 动态生成 save_path
                if st.button("📥 转存入库", key=f"btn_{idx}", use_container_width=True):
                    final_path = f"{save_root}/{title}"
                    with st.spinner('提交中...'):
                        success = add_and_run_task(url, title, final_path)
                        if success:
                            st.toast(f"✅ 已存入{category}：{title}")
                            st.success(f"成功提交至 {final_path}")
                        else:
                            st.error("后端拒绝请求，请检查日志")
        st.divider()

# --- 5. 底部快捷工具栏 ---
st.markdown(
    f"""
    <div style="text-align: center; padding: 20px; color: gray; font-size: 0.8rem;">
        <a href="{config_env.alist_url}" target="_blank">📂 AList</a> | 
        <a href="{config_env.pansou_url}" target="_blank">🔍 盘搜</a> | 
        <a href="{config_env.quark_auto_save_url}" target="_blank">⚙️ 转存后台</a> | 
        <a href="{config_env.quark_url}" target="_blank">☁️ 夸克云盘</a>
    </div>
    """, 
    unsafe_allow_html=True
)