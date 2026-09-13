import datetime
import random
import time

import ddddocr
import requests


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def login(base_url, username, password, max_retries=3):
    """
    登录函数（带重试机制）
    :param username: 用户名
    :param password: 密码
    :param max_retries: 最大重试次数，默认为3
    :return: (success, session, message)
    """
    
    for attempt in range(1, max_retries + 1):
        print(f"\n========== 第 {attempt}/{max_retries} 次尝试登录 ==========")
        
        session = requests.Session()
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        try:
            print("[1] 访问登录页...")
            session.get(f"{base_url}/login", headers=HEADERS, timeout=10)
            
            print("[2] 获取验证码...")
            captcha_res = session.get(f"{base_url}/captcha?_r={random.random()}", headers=HEADERS, timeout=10)
            
            print("[3] 识别验证码...")
            ocr = ddddocr.DdddOcr(show_ad=False)
            captcha_code = ocr.classification(captcha_res.content)
            print(f"验证码识别结果: {captcha_code}")
            
            print("[4] 提交登录信息...")
            login_data = {
                "username": username,
                "password": password,
                "captcha": captcha_code,
                "busiDate": today,
                "ctype": "c",
                "macAddress": "",
                "superDogId": "",
            }
            
            login_resp = session.post(f"{base_url}/login", data=login_data, headers=HEADERS, timeout=10)
            
            # 判断登录是否成功
            if "index" in login_resp.url or "main" in login_resp.url:
                print("✅ 登录成功")
                return True, session, "登录成功"
            elif login_resp.status_code == 200 and "登录" not in login_resp.text:
                print("✅ 登录成功")
                return True, session, "登录成功"
            else:
                print(f"❌ 登录失败（第{attempt}次），验证码可能识别错误，准备重试...")
                # 如果不是最后一次尝试，等待一下再重试
                if attempt < max_retries:
                    time.sleep(1)
                continue
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ 网络请求异常: {e}")
            if attempt < max_retries:
                print("准备重试...")
                time.sleep(2)
                continue
            else:
                return False, None, f"网络请求异常，已重试{max_retries}次: {e}"
        except Exception as e:
            print(f"⚠️ 登录异常: {e}")
            if attempt < max_retries:
                print("准备重试...")
                time.sleep(1)
                continue
            else:
                return False, None, f"登录异常，已重试{max_retries}次: {e}"
    
    # 所有重试都失败，提示可能是账号或密码错误
    return False, None, f"连续{max_retries}次登录失败，可能是用户名或密码错误"
