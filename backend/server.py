import asyncio
import json
import uuid
from pydantic import BaseModel
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from datetime import datetime, timedelta
import uvicorn

app = FastAPI()
origins = [
    "http://localhost:6099",  # Vue 开发服务器地址
    "http://localhost:9528"
]
# app.debug = True
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储在线客户端连接
active_connections: Dict[str, WebSocket] = {}
# 存储客户端状态（如最后心跳时间）
client_status: Dict[str, Dict] = {}

# 心跳超时时间（秒）
HEARTBEAT_TIMEOUT = 30

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections[client_id] = websocket
    client_status[client_id] = {
        "last_heartbeat": datetime.now(),
        "policy_version": None
    }
    print(f"Client {client_id} connected")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "heartbeat":
                client_status[client_id]["last_heartbeat"] = datetime.now()
                client_status[client_id]["policy_version"] = message.get("version")
                await websocket.send_text(json.dumps({"status": "ok"}))

            elif msg_type == "file_report":
                print(f"Received file report from {client_id}: {message.get('changes')}")
                await websocket.send_text(json.dumps({"status": "received"}))

            elif msg_type == "ack_policy":
                print(f"Client {client_id} confirmed policy {message.get('policy_id')}")

            # 可扩展更多消息类型...

    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
        active_connections.pop(client_id, None)
        client_status.pop(client_id, None)

@app.post("/send_policy/{client_id}")
async def send_policy(client_id: str):
    if client_id not in active_connections:
        return {"error": "client not connected"}

    policy = {
        "type": "policy_update",
        "policy_id": f"policy_{uuid.uuid4()}",
        "content": {
            "rules": ["*.key", "*.conf", "/etc/passwd"]
        }
    }
    try:
        await active_connections[client_id].send_text(json.dumps(policy))
        return {"status": "sent", "policy_id": policy["policy_id"]}
    except Exception as e:
        return {"error": str(e)}

@app.get("/status")
def get_client_status():
    now = datetime.now()
    return {
        cid: {
            "last_heartbeat": str(info["last_heartbeat"]),
            "status": "online" if now - info["last_heartbeat"] < timedelta(seconds=HEARTBEAT_TIMEOUT) else "offline",
            "policy_version": info["policy_version"]
        }
        for cid, info in client_status.items()
    }

@app.get("/")
def index():
    return 'Hello World!'

class admin_login_Item(BaseModel):
    username: str
    password: str

@app.post("/frontend/user/login")
def admin_login(req:admin_login_Item):
    print(req)
    return  {   "code": 20000
            ,   "data":
                {   "token": "admin-token"
                }
            }

@app.get("/frontend/user/info")
def admin_info():
    return  {   "code": 20000
            ,   "data":
                {   "roles":
                    [   "admin"
                    ]
                ,   "introduction": "I am a super administrator"
                ,   "avatar": "https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif"
                ,   "name": "你好管理员"
                }
            }

@app.post("/frontend/user/logout")
def admin_logout():
    return  {   "code":20000
            ,   "data":"success"
            }

@app.get("/frontend/table/list")
def table_list():
    return  {   "code": 20000
            ,   "data":
                {   "total": 3
                ,   "items":
                    [   {   "id": "710000198110032753"
                        ,   "title": "Nfkwyzic cliqkwfey rnds ojovjvc ygjnhvrz lswplim qqid kdwkrpwqj vbdkttl dmwjonwqye ttfe."
                        ,   "status": "draft"
                        ,   "author": "name"
                        ,   "display_time": "1978-12-19 23:54:55"
                        ,   "pageviews": 4140
                        }
                    ,   {
                            "id": "210000197712046498",
                            "title": "Qalm vjfnxrwe yignld coxhqmonv nfvgpgaty zjxy higxrpww lvbbjvrzv uuiddzv gfugwno bzkj qthntayo lbdg fumtrqne otjsu bksq bwqy vpz otonvqbu.",
                            "status": "deleted",
                            "author": "name",
                            "display_time": "1985-11-12 10:20:29",
                            "pageviews": 3484
                        }
                    ,   {
                            "id": "230000199408228118",
                            "title": "Keew ucjsksrw uhhzmys vvsyo extwvlmepu vkluygk cqw cvbpxhbea ojoiwpih skbu slkbxr mqh zgqvkthcs mpyt byfuopocs komvxnk wvgudsuo nmczoe odfnkixl llufdhdf.",
                            "status": "published",
                            "author": "name",
                            "display_time": "1999-05-28 12:26:41",
                            "pageviews": 2559
                        }
                    ]
                }
            }

@app.get("/frontend/statusinfo")
def statusinfo():
    return  {   "code": 20000
            ,   "data":
                {   "total": 5
                ,   "items":
                    [   {   "id": 1001
                        ,   "name": "张三"
                        ,   "status": "在线"
                        }
                    ,   {   "id": 1002
                        ,   "name": "李四"
                        ,   "status": "离线"
                        }
                    ,   {   "id": 1003
                        ,   "name": "王五"
                        ,   "status": "在线"
                        }
                    ,   {   "id": 1004
                        ,   "name": "赵六"
                        ,   "status": "离线"
                        }
                    ,   {   "id": 1005
                        ,   "name": "钱七"
                        ,   "status": "在线"
                        }
                    ]
                }
            }

class strategy_Item(BaseModel):
    strategy: str

@app.post("/frontend/strategy/submit")
def strategy_submit(req:strategy_Item):
    # print(req)
    return  {   "code":20000
            ,   "data":"success"
            }

@app.post("/frontend/strategy/statu")
def strategy_submit():
    return  {   "code":20000
            ,   "data":"success"
            }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6099)