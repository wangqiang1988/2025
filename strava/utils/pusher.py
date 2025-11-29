import time
import requests
import json
import os
from pathlib import Path
from .config_env import CORPID, CORPSECRET, AGENTID, TOUSER, BASE_URL


BASE_DIR = Path(__file__).resolve().parent
TOKEN_FILE_PATH = BASE_DIR / 'access_token.conf'
print(TOKEN_FILE_PATH)


class WeChat:
    def __init__(self):
        # ⚠️ 凭证请务必再次核对，如果仍出现40001错误，请检查这两个值
        self.CORPID = CORPID
        self.CORPSECRET = CORPSECRET
        
        # 🚨 修复：移除 AgentID 前后的空格
        self.AGENTID = AGENTID
        self.TOUSER = TOUSER  # 接收者用户名,多个用户用|分割
        
        # API 基础 URL
        self.BASE_URL = BASE_URL
 
    def _get_access_token(self):
        """内部方法：实际请求新的 access_token，并处理API错误"""
        url = f'{self.BASE_URL}/cgi-bin/gettoken'
        
        values = {'corpid': self.CORPID,
                  'corpsecret': self.CORPSECRET,
                  }
        
        # 使用 params 传递参数
        req = requests.post(url, params=values)
        print(req, '------------------------------------')
        
        try:
            data = req.json()
            if data.get("access_token"):
                return data["access_token"]
            else:
                # 如果请求成功但返回的是错误信息 (如 errcode)
                print(f"🚨 获取 Token 失败，API 返回错误: {data}")
                raise Exception(f"API 获取 Token 失败: {data.get('errmsg', '未知错误')} (Code: {data.get('errcode')})")
        except json.JSONDecodeError:
            # 如果返回的不是 JSON (如 502 错误)
            print(f"🚨 获取 Token 失败，非 JSON 响应: {req.text}")
            raise Exception("获取 Token 失败，API 响应非 JSON 格式。")
 
    def get_access_token(self):
        """外部方法：优先从文件读取，过期或失败则重新获取"""
        # 统一使用 time.time() 获取当前时间
        cur_time = time.time()
        access_token = None
        
        try:
            # 使用绝对路径读取文件
            with open(TOKEN_FILE_PATH, 'r') as f:
                t, access_token = f.read().split()
                # 检查 Token 是否过期 (7200秒有效期，使用 7260 秒缓冲)
                if float(cur_time) - float(t) < 7260:
                    return access_token
                else:
                    print("Token 已过期，重新获取...")
        except:
             # 文件不存在、内容格式错误或 Token 已过期，都需要重新获取
            print("配置文件读取失败/过期，尝试重新获取 Token...")
            pass # 走下面的重新获取逻辑
            
        # 重新获取 Token 并写入文件
        try:
            access_token = self._get_access_token()
            cur_time = time.time()
            
            # 使用绝对路径写入文件
            with open(TOKEN_FILE_PATH, 'w') as f:
                f.write('\t'.join([str(cur_time), access_token]))
            
            return access_token
        except Exception as e:
            # 如果重新获取失败，则把错误信息返回，而不是让程序崩溃
            raise Exception(f"Failed to refresh access_token: {e}")
 
    def send_data(self, message):
        """发送企业微信消息"""
        try:
            token = self.get_access_token()
        except Exception as e:
            # 如果获取 Token 失败，直接返回错误信息
            return f"获取 Token 失败: {e}"

        send_url = f'{self.BASE_URL}/cgi-bin/message/send?access_token={token}'
        
        send_values = {
            "touser": self.TOUSER,
            "msgtype": "text",
            "agentid": self.AGENTID,
            "text": {
                "content": message
                },
            "safe": 0 # 0 表示非加密
            }
        
        send_msges=(bytes(json.dumps(send_values), 'utf-8'))
        
        # 🚨 修复：确保请求以 json 形式发送 (requests.post(url, data) 是发送原始字节)
        respone = requests.post(send_url, data=send_msges)
        
        try:
            respone_data = respone.json()
        except json.JSONDecodeError:
            return f"推送服务返回非 JSON 格式响应: {respone.text}"

        # 优化：判断是否推送成功
        if respone_data.get("errcode") == 0:
             return "ok"
        else:
             # 返回完整的错误信息或 errmsg
             return respone_data.get("errmsg", f"Unknown Error (Code: {respone_data.get('errcode')})")
 
if __name__ == '__main__':
    print("--- 启动推送测试 ---")
    try:
        # 在测试时，我们强制删除旧文件以确保获取新的 Token
        if TOKEN_FILE_PATH.exists():
            os.remove(TOKEN_FILE_PATH)
            print(f"✅ 已清理旧的 {TOKEN_FILE_PATH} 文件，将强制重新获取 Token。")
            
        wx = WeChat()
        result1 = wx.send_data("这是程序发送的第1条消息！\n Python程序调用企业微信API,从自建应用“告警测试应用”发送给管理员的消息！")
        print(f"发送消息1结果: {result1}")
        
        result2 = wx.send_data("这是程序发送的第2条消息！")
        print(f"发送消息2结果: {result2}")

    except Exception as e:
        print(f"程序运行出错: {e}")
