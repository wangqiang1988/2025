import requests
import datetime
import json
import time
# 假设 config_env.py 已经修复，可以成功导入以下变量
from utils.config_env import client_id, client_secret, refresh_token
from utils.pusher import WeChat


# --- 全局常量 ---
TOKEN_REFRESH_URL = "https://www.strava.com/oauth/token"
ACTIVITY_URL = "https://www.strava.com/api/v3/athlete/activities"
ATHLETE_URL = "https://www.strava.com/api/v3/athlete/"
GEAR_URL = "https://www.strava.com/api/v3/gear/"
PER_PAGE_MAX = 200


def refresh_access_token():
    """使用 refresh_token 获取新的 access_token"""
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    try:
        response = requests.post(TOKEN_REFRESH_URL, data=payload)
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Token refresh failed. Error: {e}")
        return None

def format_data_for_display(data):
    """
    将 JSON 数据结构转换为易于阅读的字符串格式，方便推送。
    """
    output = ["--- Strava 运动数据报告 ---"]
    
    # --- 1. 跑步总距离 ---
    total_km = 0.0
    latest_run = {}
    if data["runs"]:
        latest_run = data["runs"][0]
        total_km = latest_run.get("本周跑步", 0.0) # 获取本周总距离
        
        output.append(f"📅 本周总跑步距离：{total_km:.2f} 公里")
        output.append("----------------------------")
        
        # --- 2. 最近一次跑步详情 ---
        output.append("🏃 最近一次跑步活动：")
        output.append(f"  > 距离: {latest_run.get('距离', 'N/A')} km")
        output.append(f"  > 耗时: {latest_run.get('跑步时间', 'N/A')} 分钟")
        output.append(f"  > 配速: {latest_run.get('配速', 'N/A')} (分秒)")
        
        # 处理心率，如果存在
        heartrate = latest_run.get('平均心率')
        if heartrate:
            output.append(f"  > 平均心率: {int(heartrate)} bpm")
        output.append("")

    # --- 3. 装备里程 ---
    gear_items = data.get("gear", [])
    if gear_items:
        output.append("👟 装备累计里程 (km)：")
        # 对装备进行分类和排序，让输出更整洁
        shoes = []
        bikes = []
        
        for item in gear_items:
            # item 是一个字典，如 {"Saucony K13": 646.4}
            name = list(item.keys())[0]
            distance = list(item.values())[0]
            
            # 简单判断是跑鞋还是自行车（基于你提供的名称示例）
            if 'bike' in name.lower() or 'allez' in name.lower() or 'brompton' in name.lower() or 'k3plus' in name.lower() or 'af105' in name.lower():
                 bikes.append((name, distance))
            else:
                 shoes.append((name, distance))

        # 输出跑鞋
        if shoes:
            output.append("  [跑鞋里程]")
            for name, distance in shoes:
                output.append(f"  - {name}: {distance:.2f} km")
        
        # 输出自行车
        if bikes:
            output.append("  [自行车里程]")
            for name, distance in bikes:
                output.append(f"  - {name}: {distance:.2f} km")
    
    output.append("----------------------------")
    output.append(f"📝 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(output)

def get_strava_data(new_access_token):
    """
    执行所有数据获取和计算逻辑，
    并按照你要求的结构（data["runs"] 和 data["gear"]）返回结果。
    """
    data = {
        "runs": [],
        "gear": []
    }
    
    headers = {"Authorization": f"Bearer {new_access_token}"}

    # --- 1. 计算本周时间戳 ---
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    start_of_week_timestamp = int(time.mktime(start_of_week.timetuple()))
    end_of_week_timestamp = start_of_week_timestamp + 7 * 24 * 3600

    # --- 2. 获取本周跑步总距离 ---
    params_weekly = {
        "after": start_of_week_timestamp,
        "before": end_of_week_timestamp,
        "per_page": PER_PAGE_MAX
    }
    try:
        response_ac_weekly = requests.get(ACTIVITY_URL, headers=headers, params=params_weekly)
        response_ac_weekly.raise_for_status()
        activities_weekly = response_ac_weekly.json()
        
        # 计算本周总距离
        total_distance_m = sum(activity["distance"] for activity in activities_weekly if activity["type"] == "Run")
        total_distance_km = round(total_distance_m / 1000.0, 2)
        print(f"本周跑步总距离为：{total_distance_km:.2f} 公里")

    except requests.exceptions.RequestException as e:
        print(f"获取本周活动数据失败: {e}")
        total_distance_km = 0.0


    # --- 3. 获取最近的活动和装备信息 ---
    # 这一步将获取所有的活动，用于找到最近的 Run 活动作为 'runs' 列表数据源
    params_all = {"per_page": 30} # 只获取最近的30条活动，减少数据量
    try:
        response_ac_all = requests.get(ACTIVITY_URL, headers=headers, params=params_all)
        response_ac_all.raise_for_status()
        activities_all = response_ac_all.json()
    except requests.exceptions.RequestException as e:
        print(f"获取最近活动数据失败: {e}")
        activities_all = []


    # --- 4. 处理最近的跑步活动（仅取最近一次 Run 作为 data["runs"] 的数据源） ---
    for run in activities_all:
        if run['type'] == 'Run':
            # 距离、时间、配速计算
            runtime = round(run['moving_time'] / 60)
            runkm = round(run['distance'] / 1000, 1)
            
            runsec = float(run['moving_time']) / float(runkm) if runkm > 0 else 0
            m, s = divmod(runsec, 60)
            runpace = "%01d%02d" % (m, s) # 保留你原有的 mmss 格式
            
            run_info = {
                "本周跑步": total_distance_km,  # 使用步骤2计算出的本周总距离
                "跑步时间": runtime,
                "距离": runkm,
                "配速": runpace,
                "平均心率": run.get('average_heartrate', 'N/A')
            } 
            data["runs"].append(run_info)
            break # 找到最近一次跑步活动后立即退出循环

    # --- 5. 获取装备信息（保留原有的循环请求方式，但仅执行一次） ---
    try:
        # 1) 获取运动员信息（包含装备 ID）
        response_ath = requests.get(ATHLETE_URL, headers=headers)
        response_ath.raise_for_status()
        geardata = response_ath.json()
        # 2) 循环获取自行车里程
        # 2) 循环获取自行车里程
        for bike in geardata.get('bikes', []):
            response_gear = requests.request("GET", GEAR_URL + bike['id'], headers=headers)
            response_gear.raise_for_status()
            
            gear_detail = response_gear.json()
            # *** 最终修正：将 Strava 返回的小数值乘以 1000，还原为实际公里数 ***
            distance_km = round(float(gear_detail['converted_distance']) , 2)
            bike_info = {
                gear_detail['name']: distance_km,
            } 
            data["gear"].append(bike_info)

        # 3) 循环获取跑鞋里程
        for shoe in geardata.get('shoes', []):
            response_gear = requests.request("GET", GEAR_URL + shoe['id'], headers=headers)
            response_gear.raise_for_status()
            
            gear_detail = response_gear.json()
            # *** 最终修正：将 Strava 返回的小数值乘以 1000，还原为实际公里数 ***
            distance_km = round(float(gear_detail['converted_distance']) , 2)
            shoe_info = {
                gear_detail['name']: distance_km,
            } 
            data["gear"].append(shoe_info)

    except requests.exceptions.RequestException as e:
        print(f"获取装备信息失败: {e}")
    except Exception as e:
        print(f"处理装备数据时发生错误: {e}")
    
    return data

# --- 主执行逻辑 ---
def main():
    """执行所有操作并打印最终 JSON 结果和可读性强的字符串内容"""
    # 1. 刷新 Access Token
    new_access_token = refresh_access_token()
    if not new_access_token:
        print("无法获取有效的访问令牌，程序退出。")
        return

    # 2. 获取数据
    final_data = get_strava_data(new_access_token)
    
    # 3. 打印可读性好的字符串内容
    display_string = format_data_for_display(final_data)

    print("\n" * 3) # 添加多行空行以便区分
    print("====================================")
    print("📢 【推送内容】")
    print("====================================")
    print(display_string)
    print("====================================")
    
    # 4. **【新增推送代码】**
    try:
        # 初始化企业微信推送对象
        wx_pusher = WeChat() 
        print("正在尝试将数据推送到企业微信...")
        
        # 调用 send_data 方法推送可读性高的字符串内容
        push_result = wx_pusher.send_data(display_string) 
        
        print(f"✅ 企业微信推送结果: {push_result}")
        
        # 简单检查，如果不是 'ok' 则可能有错误
        if push_result != "ok":
            print(f"⚠️ 推送可能失败，返回信息: {push_result}")

    except Exception as e:
        print(f"🚨 推送服务调用失败: {e}")
    # ------------------------------------------

    # 5. 打印最终 JSON 结果（供程序使用）
    print("\n--- 原始 JSON 结构输出（供程序使用）---")
    json_data = json.dumps(final_data, ensure_ascii=False)
    print(json_data)
    print("------------------------------------------\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An unexpected error occurred in main execution: {str(e)}")