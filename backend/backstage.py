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
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from fastapi import FastAPI, Depends, Query
import sys
sys.path.append("..")
from log import get_upload_logs


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
DATABASE_URL = "mysql+pymysql://remote:123456@47.108.169.120/trx"
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
    # 查询文件及其命中的敏感规则
    query = text("""
        SELECT 
            f.file_id as id,
            f.file_name as title,
            f.user_id,
            f.count as pageviews,
            f.discovery_time as display_time,
            f.md5,
            GROUP_CONCAT(m.rule_id) as rule_ids
        FROM files f
        LEFT JOIN matches m ON f.file_id = m.file_id AND f.user_id = m.user_id
        GROUP BY f.file_id, f.user_id
    """)
    
    result = db.execute(query)
    files = []
    for row in result:
        files.append({
            "id": row.id,
            "title": row.title,
            "author": row.user_id,
            "pageviews": row.pageviews,
            "display_time": row.display_time.strftime("%Y-%m-%d %H:%M:%S") if row.display_time else None,
            "md5": row.md5,
            "rule_ids": [int(rid) for rid in row.rule_ids.split(',')] if row.rule_ids else []
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

# 修改策略提交接口，支持同时创建策略和规则
class StrategyWithRulesItem(BaseModel):
    strategy: str
    rule_types: List[int]  # 新增字段，接收规则类型列表

@app.post("/frontend/strategy/submit")
def strategy_submit(req: StrategyWithRulesItem, db = Depends(get_db)):
    max_id_query = text("SELECT MAX(CAST(policy_id AS UNSIGNED)) FROM policy")
    max_id_result = db.execute(max_id_query).fetchone()
    current_max = max_id_result[0] if max_id_result[0] is not None else -1
    policy_id = str(current_max + 1)
    try:
        # 1. 插入策略
        insert_policy = text("""
            INSERT INTO policy (policy_id, policy_description)
            VALUES (:policy_id, :policy_description)
        """)
        db.execute(insert_policy, {
            "policy_id": policy_id,
            "policy_description": req.strategy
        })

        # 2. 插入规则（如不存在）
        for rule_type in req.rule_types:
            if rule_type not in RULE_MAPPING:
                continue
            rule_description = RULE_MAPPING[rule_type]["description"]
            rule_id = rule_type

            # 检查规则是否已存在
            rule_exist = db.execute(
                text("SELECT 1 FROM rules WHERE rule_id = :rule_id"),
                {"rule_id": rule_id}
            ).fetchone()
            if not rule_exist:
                db.execute(
                    text("INSERT INTO rules (rule_id, rule_description) VALUES (:rule_id, :rule_description)"),
                    {"rule_id": rule_id, "rule_description": rule_description}
                )

            # 3. 插入策略-规则关联
            db.execute(
                text("INSERT INTO policy_rules (policy_id, rule_id) VALUES (:policy_id, :rule_id)"),
                {"policy_id": policy_id, "rule_id": rule_id}
            )

        db.commit()
        return {
            "code": 20000,
            "data": {
                "message": "策略和规则提交成功",
                "policy_id": policy_id
            }
        }
    except Exception as e:
        db.rollback()
        return {
            "code": 50000,
            "message": f"提交失败: {str(e)}"
        }

@app.post("/frontend/strategy/statu")
def strategy_submit():
    return  {   "code":20000
            ,   "data":"success"
            }

@app.get("/frontend/matches/list")
def matches_list(user_id: str, db = Depends(get_db)):
    # 1. 查该用户当前策略
    policy_query = text("SELECT policy_id FROM user WHERE user_id = :user_id")
    policy_row = db.execute(policy_query, {"user_id": user_id}).fetchone()
    if not policy_row:
        return {"code": 40004, "message": "用户不存在"}
    policy_id = policy_row.policy_id

    # 2. 查该策略下所有规则
    rule_query = text("SELECT rule_id FROM policy_rules WHERE policy_id = :policy_id")
    rule_rows = db.execute(rule_query, {"policy_id": policy_id}).fetchall()
    rule_ids = [row.rule_id for row in rule_rows]
    if not rule_ids:
        return {"code": 20000, "data": {"total": 0, "items": []}}

    # 3. 查matches表中该用户、这些规则的所有匹配
    user_query = text("""
        SELECT user_name
        FROM user
        WHERE user_id = :user_id
    """).bindparams(bindparam('user_id', expanding=True))
    userresult = db.execute(user_query, {"user_id": user_id}).fetchone()
    user_name= userresult.user_name
    matches_query = text("""
        SELECT file_id, rule_id
        FROM matches
        WHERE user_id = :user_id AND rule_id IN :rule_ids
    """)
    result = db.execute(matches_query, {"user_id": user_id, "rule_ids": rule_ids})
    matches = []
    for row in result:
        matches.append({
            "file_id": row.file_id,
            "rule_id": row.rule_id,
            "user_name": user_name
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
        query = text("""
            SELECT 
                policy_id,
                policy_description
            FROM policy
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


#规则展示页面的查询
@app.get("/frontend/rules/list")
def rules_list(
    policy_id: str,  # 必选参数
    db = Depends(get_db)
):
    # 通过 policy_rules 关联查询该策略下所有规则
    query = text("""
        SELECT 
            r.rule_id,
            r.rule_description
        FROM policy_rules pr
        JOIN rules r ON pr.rule_id = r.rule_id
        WHERE pr.policy_id = :policy_id
        ORDER BY CAST(r.rule_id AS UNSIGNED) ASC
    """)
    
    result = db.execute(query, {"policy_id": policy_id})
    rules = []
    for row in result:
        rules.append({
            "rule_id": row.rule_id,
            "rule_description": row.rule_description,
        })
    
    return {
        "code": 20000,
        "data": {
            "total": len(rules),
            "items": rules
        }
    }


# # 添加规则
# class RuleCreateItem(BaseModel):
#     policy_id: str
#     rule_description: str

class RuleCreateItem(BaseModel):
    policy_id: str
    rule_type: int  # 改为接收规则类型ID

RULE_MAPPING = {
    1: {"description": "phone", "name": "手机号码"},
    2: {"description": "ip", "name": "IPv4地址"},
    3: {"description": "mac", "name": "MAC地址"},
    4: {"description": "ipv6", "name": "IPv6地址"},
    5: {"description": "bank_card", "name": "银行卡号"},
    6: {"description": "email", "name": "电子邮件地址"},
    7: {"description": "passport", "name": "护照号码"},
    8: {"description": "id_number", "name": "身份证号码"},
    9: {"description": "gender", "name": "性别信息"},
    10: {"description": "national", "name": "民族信息"},
    11: {"description": "carnum", "name": "车牌号码"},
    12: {"description": "telephone", "name": "固定电话号码"},
    13: {"description": "officer", "name": "军官证号码"},
    14: {"description": "HM_pass", "name": "港澳通行证号码"},
    15: {"description": "jdbc", "name": "JDBC连接字符串"},
    16: {"description": "organization", "name": "组织机构代码"},
    17: {"description": "business", "name": "工商注册号"},
    18: {"description": "credit", "name": "统一社会信用代码"},
    19: {"description": "address_name", "name": "中文地址和姓名"},
}

# @app.post("/frontend/rules/create")
# def create_rule(req: RuleCreateItem, db = Depends(get_db)):
#     if req.rule_type not in RULE_MAPPING:
#         return {"code": 40000, "message": "无效的规则类型"}
#     rule_id = str(req.rule_type)
#     rule_description = RULE_MAPPING[req.rule_type]["description"]
#     try:
#         policy_check = text("SELECT 1 FROM policy WHERE policy_id = :policy_id")
#         if not db.execute(policy_check, {"policy_id": req.policy_id}).fetchone():
#             return {"code": 40400, "message": "策略不存在"}
#         rule_check = text("""
#             SELECT 1 FROM rules 
#             WHERE policy_id = :policy_id AND rule_description = :rule_description
#         """)
#         if db.execute(rule_check, {
#             "policy_id": req.policy_id,
#             "rule_description": rule_description
#         }).fetchone():
#             return {"code": 40000, "message": "该规则已存在"}
#         insert_query = text("""
#             INSERT INTO rules (rule_id, policy_id, rule_description)
#             VALUES (:rule_id, :policy_id, :rule_description)
#         """)
#         db.execute(insert_query, {
#             "rule_id": rule_id,
#             "policy_id": req.policy_id,
#             "rule_description": rule_description
#         })
#         db.commit()
#         return {
#             "code": 20000,
#             "data": {
#                 "rule_id": rule_id,
#                 "message": "规则创建成功"
#             }
#         }
#     except Exception as e:
#         db.rollback()
#         return {"code": 50000, "message": f"规则创建失败: {str(e)}"}

# # 更新规则
# class RuleUpdateItem(BaseModel):
#     rule_id: str
#     rule_description: str

# @app.post("/frontend/rules/update")
# def update_rule(req: RuleUpdateItem, db = Depends(get_db)):
#     try:
#         update_query = text("""
#             UPDATE rules 
#             SET rule_description = :rule_description
#             WHERE rule_id = :rule_id
#         """)
#         result = db.execute(update_query, {
#             "rule_id": req.rule_id,
#             "rule_description": req.rule_description
#         })
        
#         if result.rowcount == 0:
#             return {"code": 40400, "message": "规则不存在"}
        
#         db.commit()
#         return {"code": 20000, "data": "规则更新成功"}
#     except Exception as e:
#         db.rollback()
#         return {"code": 50000, "message": f"规则更新失败: {str(e)}"}

# # 删除规则
# @app.delete("/frontend/rules/delete")
# def delete_rule(rule_id: str, db = Depends(get_db)):
#     try:
#         # 开启事务
#         with db.begin():
#             # 1. 先删除关联的匹配记录
#             delete_matches = text("DELETE FROM matches WHERE rule_id = :rule_id")
#             db.execute(delete_matches, {"rule_id": rule_id})
            
#             # 2. 再删除规则本身
#             delete_rule = text("DELETE FROM rules WHERE rule_id = :rule_id")
#             result = db.execute(delete_rule, {"rule_id": rule_id})
            
#             if result.rowcount == 0:
#                 return {"code": 40400, "message": "规则不存在"}
            
#             return {"code": 20000, "data": "规则删除成功"}
#     except Exception as e:
#         return {"code": 50000, "message": f"规则删除失败: {str(e)}"}

# # 批量删除规则
# class BatchDeleteRulesItem(BaseModel):
#     rule_ids: List[str]

# @app.post("/frontend/rules/batch-delete")
# def batch_delete_rules(req: BatchDeleteRulesItem, db = Depends(get_db)):
#     try:
#         with db.begin():
#             # 1. 先删除关联的匹配记录
#             delete_matches = text("""
#                 DELETE FROM matches 
#                 WHERE rule_id IN :rule_ids
#             """)
#             db.execute(delete_matches, {"rule_ids": tuple(req.rule_ids)})
            
#             # 2. 再删除规则本身
#             delete_rules = text("""
#                 DELETE FROM rules 
#                 WHERE rule_id IN :rule_ids
#             """)
#             result = db.execute(delete_rules, {"rule_ids": tuple(req.rule_ids)})
            
#             return {
#                 "code": 20000,
#                 "data": {
#                     "deleted_count": result.rowcount
#                 }
#             }
#     except Exception as e:
#         return {"code": 50000, "message": f"批量删除失败: {str(e)}"}
    

@app.get("/frontend/uploadlog/list")
def uploadlog_list(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
):
    # influxdb配置
    url = "http://47.108.169.120:8086"
    token = 'YkXOflEN22TCy2cZSndeY6KIOZeatb99QwecnptwJDZ_ehVqiYGXR8ihOW9oOKFQCBtgGfhY70ww0QhNe3I8uw=='
    org = "trx"
    bucket = "log"
    logs = get_upload_logs(url, token, org, bucket)
    # 按时间倒序
    logs = sorted(logs, key=lambda x: x.get("time"), reverse=True)
    total = len(logs)
    start = (page - 1) * limit
    end = start + limit
    items = logs[start:end]
    # 转换时间为字符串
    for item in items:
        if "time" in item and item["time"]:
            item["time"] = item["time"].strftime("%Y-%m-%d %H:%M:%S")
    return {
        "code": 20000,
        "data": {
            "total": total,
            "items": items
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6099)