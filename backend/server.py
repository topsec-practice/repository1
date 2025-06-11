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
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from fastapi import FastAPI, Depends


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


# 数据库配置
DATABASE_URL = "mysql+pymysql://root:yjydmm520@localhost/test"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 添加数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
def table_list(db = Depends(get_db)):
    # 查询数据库获取文件列表（仅从files表）
    query = text("""
        SELECT 
            file_id as id,
            file_name as title,
            user_id,
            count as pageviews,
            discovery_time as display_time,
            md5
        FROM files
    """)
    
    result = db.execute(query)
    files = []
    for row in result:
        files.append({
            "id": row.id,
            "title": row.title,
            "author": row.user_id,  # 使用实际的user_id作为author
            "pageviews": row.pageviews,
            "display_time": row.display_time.strftime("%Y-%m-%d %H:%M:%S") if row.display_time else None,
            "md5": row.md5
        })
    
    return {
        "code": 20000,
        "data": {
            "total": len(files),
            "items": files
        }
    }

# 修改后的statusinfo函数
@app.get("/frontend/statusinfo")
def statusinfo(db = Depends(get_db)):
    # 查询数据库获取用户状态
    query = text("""
        SELECT user_id as id, user_name as name, status, 
               LastEchoTime, LastScanTime, IP, user_key
        FROM user
    """)
    
    result = db.execute(query)
    users = []
    for row in result:
        users.append({
            "id": row.id,
            "name": row.name,
            "status": row.status,
            "LastEchoTime": row.LastEchoTime.strftime("%Y-%m-%d %H:%M:%S") if row.LastEchoTime else None,
            "LastScanTime": row.LastScanTime.strftime("%Y-%m-%d %H:%M:%S") if row.LastScanTime else None,
            "IP": row.IP,
            "key": row.user_key
        })
    
    return {
        "code": 20000,
        "data": {
            "total": len(users),
            "items": users
        }
    }

class strategy_Item(BaseModel):
    strategy: str

@app.post("/frontend/strategy/submit")
def strategy_submit(req: strategy_Item, db = Depends(get_db)):
    # 生成唯一的policy_id
    policy_id = str(uuid.uuid4())
    
    # 检查policy_id是否已存在（虽然UUID冲突概率极低，但为了安全还是检查）
    check_query = text("SELECT 1 FROM policy WHERE policy_id = :policy_id")
    while db.execute(check_query, {"policy_id": policy_id}).fetchone():
        policy_id = str(uuid.uuid4())  # 如果冲突，重新生成
    
    # 插入策略到数据库
    insert_query = text("""
        INSERT INTO policy (policy_id, policy_description)
        VALUES (:policy_id, :policy_description)
    """)
    
    try:
        db.execute(insert_query, {
            "policy_id": policy_id,
            "policy_description": req.strategy
        })
        db.commit()
        return {
            "code": 20000,
            "data": {
                "message": "策略提交成功",
                "policy_id": policy_id
            }
        }
    except Exception as e:
        db.rollback()
        return {
            "code": 50000,
            "message": f"策略提交失败: {str(e)}"
        }

@app.post("/frontend/strategy/statu")
def strategy_submit():
    return  {   "code":20000
            ,   "data":"success"
            }

@app.get("/frontend/matches/list")
# def matches_list(
#     search: str = None,  # 添加搜索参数
#     db = Depends(get_db)
# ):
def matches_list(db = Depends(get_db)):
    # 基础查询
    query = text("""
        SELECT 
            policy_id,
            file_id,
            rule_id,
            user_id
        FROM matches
    """)
    
    # 添加搜索条件
    # params = {}
    # if search:
    #     query = text(f"""
    #         {query}
    #         AND (policy_id LIKE :search 
    #         OR file_id LIKE :search 
    #         OR rule_id LIKE :search 
    #         OR user_id LIKE :search)
    #     """)
    #     params["search"] = f"%{search}%"
    
    result = db.execute(query)
    matches = []
    for row in result:
        matches.append({
            "rule_id": row.rule_id,
            "policy_id": row.policy_id,
            "file_id": row.file_id,
            "user_id": row.user_id,
        })
    
    return {
        "code": 20000,
        "data": {
            "total": len(matches),
            "items": matches
        }
    }


@app.get("/frontend/policy/list")
def policy_list(
    search: str = None,  # 可选搜索参数
    db = Depends(get_db)
):
    # 基础查询
    query = text("""
        SELECT 
            policy_id,
            policy_description
        FROM policy
    """)
    
    # 添加搜索条件
    params = {}
    if search:
        query = text(f"""
            {query}
            WHERE policy_id LIKE :search 
            OR policy_description LIKE :search
        """)
        params["search"] = f"%{search}%"
    
    result = db.execute(query, params)
    policies = []
    for row in result:
        policies.append({
            "policy_id": row.policy_id,
            "description": row.policy_description,
        })
    
    return {
        "code": 20000,
        "data": {
            "total": len(policies),
            "items": policies
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6099)