from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import logging
import time
import json
import asyncio
from multiprocessing import Process, Manager
from typing import Dict
import uvicorn
import pymysql
import sql

# -------------------------- 配置 --------------------------

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UnifiedServer")

# 安全配置
ALLOWED_IPS = {'127.0.0.1', '192.168.1.100'}       # ip白名单
API_KEY = "secure-api-key-123"
RATE_LIMIT_SECONDS = 5                             # 频率最大： 距上次时间

# 管理数据结构


rate_limit = {}
active_connections: Dict[str, WebSocket] = {}

# 连接数据库

db = pymysql.connect(
    host="47.108.169.120", 
    user="remote", 
    password="123456",
    database="trx"
)

cursor=db.cursor()

# -------------------------- 通用工具函数 --------------------------

# 检查用户名是否合理
def check_auth(request: Request):
    auth = request.headers.get('Authorization')
    return auth == f"Bearer {API_KEY}"

# 检查ip是否正常
def check_ip(request: Request):
    ip = request.client.host
    return ip in ALLOWED_IPS

# 频率检测
def rate_limit_check(ip):
    now = time.time()
    if ip in rate_limit and now - rate_limit[ip] < RATE_LIMIT_SECONDS:
        return False
    rate_limit[ip] = now
    return True



def create_rest_app(clients):
    rest_app = FastAPI()
    
    # 注册
    @rest_app.post("/api/register")
    async def register(request: Request):
        if not check_auth(request) or not check_ip(request):
            return JSONResponse(status_code=401, content={"status": "error", "message": "Unauthorized"})

        ip = request.client.host
        if not rate_limit_check(ip):
            return JSONResponse(status_code=429, content={"status": "error", "message": "Too many requests"})

        data = await request.json()
        user_id = data.get("user_id")
        if not user_id:
            return JSONResponse(status_code=400, content={"status": "error", "message": "Missing user_id"})

        now_time = datetime.now().isoformat()
        clients[ip] = {
            "last_heartbeat": now_time,
            "online": True,
            "user_id": user_id,
            "register_time": now_time
        }
        
        sql.update_user_status(db,cursor,user_id,"online",now_time)
        logger.info(f"[REGISTER] Client {user_id} ({ip}) registered and online.")
        logger.info(f"Current clients: {clients}")
        return {"status": "success", "message": "Client registered and online", "user_id": user_id}

    # 上线
    @rest_app.post("/api/online")
    async def online(request: Request):
        if not check_auth(request) or not check_ip(request):
            return JSONResponse(status_code=401, content={"status": "error", "message": "Unauthorized"})

        ip = request.client.host
        if not rate_limit_check(ip):
            return JSONResponse(status_code=429, content={"status": "error", "message": "Too many requests"})

        data = await request.json()
        user_id = data.get("user_id")
        if not user_id:
            return JSONResponse(status_code=400, content={"status": "error", "message": "Missing user_id"})

        now_time = datetime.now().isoformat()
        clients[ip] = {
            "last_heartbeat": now_time,
            "online": True,
            "user_id": user_id,
            "register_time": clients[ip].get("register_time") if ip in clients else now_time
        }

        sql.update_user_status(db,cursor,user_id,"online",now_time)
        logger.info(f"[ONLINE] Client {user_id} ({ip}) is online and heartbeat updated.")
        return {"status": "success", "message": "Client online and heartbeat updated", "user_id": user_id}

    # 心跳
    @rest_app.post("/api/heartbeat")
    async def heartbeat(request: Request):
        if not check_auth(request) or not check_ip(request):
            return JSONResponse(status_code=401, content={"status": "error", "message": "Unauthorized"})

        ip = request.client.host
        if not rate_limit_check(ip):
            return JSONResponse(status_code=429, content={"status": "error", "message": "Too many requests"})

        data = await request.json()
        user_id = data.get("user_id")
        if not user_id:
            return JSONResponse(status_code=400, content={"status": "error", "message": "Missing user_id"})

        realnow = datetime.now()
        now_time = realnow.isoformat()
        clients[ip] = {
            "last_heartbeat": now_time,
            "online": True,
            "user_id": user_id,
            "register_time": clients[ip].get("register_time") if ip in clients else now_time
        }

        sql.update_user_status(db,cursor,user_id,"online",realnow.strftime("%Y-%m-%d %H:%M:%S"))
        logger.info(f"[HEARTBEAT] Client {user_id} ({ip}) heartbeat received.")
        return {
            "status": "success",
            "message": "Heartbeat received, client online",
            "now_policy": "default_policy",
            "user_id": user_id,
            "last_heartbeat": clients[ip]["last_heartbeat"]
        }

    # @rest_app.get("/api/status")
    # async def status(request: Request):
    #     ip = request.client.host
    #     if not check_auth(request) or ip not in clients:
    #         return JSONResponse(status_code=404, content={"status": "error", "message": "Not found"})
    #     return {"status": "success", "client_status": clients[ip]}
    
    return rest_app

# -------------------------- WebSocket 服务 --------------------------

def create_ws_app(clients):
        
    ws_app = FastAPI()

    @ws_app.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: str):
        await websocket.accept()
        ip = websocket.client.host
        if ip not in ALLOWED_IPS:
            await websocket.close()
            return
        
        active_connections[user_id] = websocket
        logger.info(f"[WS] Client {user_id} connected from {ip}")
        
        await websocket.send_text(json.dumps({
            "status": "connected",
            "message": "WebSocket connection established",
            "user_id": user_id,
            "IP": ip,
        }))

        try:
            while True:
                await websocket.receive_text()  # 接收但忽略消息
        except WebSocketDisconnect:
            logger.info(f"[WS] Client {user_id} disconnected")
            active_connections.pop(user_id, None)

    @ws_app.post("/push_policy/{user_id}")
    async def push_policy(user_id: str):
        if user_id not in active_connections:
            return {"status": "error", "message": "Client not connected"}
        
        policy_id=sql.get_max_policyid(cursor)[0][0]
        rules=sql.get_all_rules(cursor,policy_id)

        policy_data = {
            "type": "policy_update",
            "policy_id": policy_id,
            "rules": rules
        }
        try:
            await active_connections[user_id].send_text(json.dumps(policy_data))
            return {"status": "success", "message": "Policy pushed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
    return ws_app
    

# -------------------------- 启动 --------------------------

def start_rest(clients):
    
    rest_app = create_rest_app(clients)
    uvicorn.run(rest_app, host="0.0.0.0", port=5000)

def start_ws(clients):
    ws_app = create_ws_app(clients)
    uvicorn.run(ws_app, host="0.0.0.0", port=6100)

if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()
   
    with Manager() as manager:
        clients = manager.dict()
        p1 = Process(target=start_rest, args=(clients,))
        p2 = Process(target=start_ws, args=(clients,))
        p1.start()
        p2.start()
        p1.join()
        p2.join()

