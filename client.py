import asyncio
import websockets
import requests
import threading
import json
import time

# 配置
API_KEY = "secure-api-key-123"
USER_ID = "1"

REST_URL_BASE = "http://47.108.169.120:5000/api"
PUSH_URL = f"http://47.108.169.120:6100/push_policy/{USER_ID}"
WS_URL = f"ws://47.108.169.120:6100/ws/{USER_ID}"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def send_heartbeat(user_id=USER_ID):
    """注册 + 上线 + 定时发送心跳"""
    data = {"user_id": user_id}
    local_policy_id = 0  # 本地已知的最新策略版本号

    try:
        # 注册
        reg_resp = requests.post(f"{REST_URL_BASE}/register", headers=HEADERS, json=data)
        print(f"[REST] 注册: {reg_resp.status_code} {reg_resp.json()}")
    except Exception as e:
        print(f"[REST] 注册失败: {e}")
        return

    if reg_resp.status_code != 200:
        try:
            # 上线（当注册失败或重复注册时执行）
            online_resp = requests.post(f"{REST_URL_BASE}/online", headers=HEADERS, json=data)
            print(f"[REST] 上线: {online_resp.status_code} {online_resp.json()}")
        except Exception as e:
            print(f"[REST] 上线失败: {e}")
            return

    time.sleep(10)  # 等待注册完成

    # 持续发送心跳
    while True:
        try:
            hb_resp = requests.post(f"{REST_URL_BASE}/heartbeat", headers=HEADERS, json=data)
            resp_json = hb_resp.json()
            print(f"[REST] 心跳发送: {hb_resp.status_code} {resp_json}")

            # 检查策略版本号
            now_policy = resp_json.get("now_policy")
            if now_policy is not None and now_policy > local_policy_id:
                print(f"[REST] 检测到新策略版本: {now_policy}，请求最新策略...")
                try:
                    response = requests.post(PUSH_URL)
                    print(f"[REST->WS] 请求策略结果: {response.json()}")
                    # 更新本地策略版本号
                    local_policy_id = now_policy
                except Exception as e:
                    print(f"[REST->WS] 策略请求失败: {e}")
        except Exception as e:
            print(f"[REST] 心跳失败: {e}")
        time.sleep(10)


async def listen_ws():
    """监听 WebSocket 策略推送"""
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("[WS] 已连接服务器，等待确认...")

            # 初始连接确认
            initial_message = await websocket.recv()
            try:
                init_data = json.loads(initial_message)
                if init_data.get("status") == "connected":
                    print(f"[WS] 连接确认: {init_data.get('message')}")

                    # 模拟发起策略推送（可选）
                    print("[WS] 模拟策略拉取请求...")
                    try:
                        response = requests.post(PUSH_URL)
                        print(f"[REST->WS] 请求策略结果: {response.json()}")
                    except Exception as e:
                        print(f"[REST->WS] 策略请求失败: {e}")
                else:
                    print("[WS] 未确认连接状态，断开")
                    return
            except json.JSONDecodeError:
                print("[WS] 无法识别初始消息，断开")
                return

            # 等待服务端策略推送
            while True:
                message = await websocket.recv()
                print(f"[WS] 收到策略: {message}")
                with open("latest_policy.json", "w") as f:
                    f.write(message)

    except Exception as e:
        print(f"[WS] 连接失败或中断: {e}")


if __name__ == "__main__":
    print("[REST] 启动心跳线程...")
    threading.Thread(target=send_heartbeat, args=(USER_ID,), daemon=True).start()

    print("[WS] 启动 WebSocket 监听...")
    asyncio.run(listen_ws())
