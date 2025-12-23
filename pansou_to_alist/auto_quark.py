import requests
import config_env
import time

def add_and_run_task(share_url, title, save_path):
    """
    接收 Streamlit 传来的参数并执行 API 调用
    """
    task_name = f"Auto_{title}_{int(time.time())}" # 增加时间戳防止任务名冲突
    
    # 构造完整数据
    task_item = {
        "taskname": task_name,
        "shareurl": share_url,
        "savepath": save_path,
        "pattern": r"(.*)\.(mp4|mkv|zip|rar|7z)",
        "replace": "",
        "addition": {
            "alist_strm_gen": {"auto_gen": True},
            "alist_sync": {"enable": False, "save_path": "", "verify_path": "", "full_path_mode": False},
            "aria2": {"auto_download": False, "pause": False},
            "emby": {"try_match": True, "media_id": ""},
            "fnv": {"auto_refresh": False, "mdb_name": "", "mdb_dir_list": ""}
        }
    }

    params = {"token": config_env.token}
    headers = {"Content-Type": "application/json"}

    try:
        # 1. 提交添加任务 (注意接口是否有 /api)
        #print(f"📡 提交 Add Task: {task_name}")
        #add_res = requests.post(config_env.base_url, params=params, json=task_item, timeout=10)
        #if add_res.status_code != 200:
        #    return False

        # 2. 触发执行 (必须带全量字段以防后端 KeyError)
        run_payload = {"tasklist": [task_item]}
        print(f"🚀 触发 Run Task")
        run_res = requests.post(config_env.run_task_url, params=params, json=run_payload, headers=headers, timeout=10)

        # 3. 结果判断（关键：防止空响应报错）
        if run_res.status_code == 200:
            return True
        return False

    except Exception as e:
        print(f"💥 后端抛出异常: {e}")
        return False