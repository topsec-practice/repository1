# coding=utf-8
import pika
import pymysql
import json
from datetime import datetime
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# 连接数据库
db = pymysql.connect(
    host='47.108.169.120', #服务器名字
    user='remote', #用户
    password='123456',  # 替换为你的真实密码
    database='trx', #数据库名字
    charset='utf8mb4'
)
cursor = db.cursor()

org = "trx"
url = "http://47.108.169.120:8086"
token = 'YkXOflEN22TCy2cZSndeY6KIOZeatb99QwecnptwJDZ_ehVqiYGXR8ihOW9oOKFQCBtgGfhY70ww0QhNe3I8uw=='
bucket = "log"

def log_data(url, token, org, bucket, user_id, log_message):
    with InfluxDBClient(url=url, token=token, org=org) as client:
        log_message = json.dumps(log_message, ensure_ascii=False)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = (
            Point("measurement1")
            .tag("user_id", user_id)
            .field("log", log_message)
        )
        write_api.write(bucket=bucket, org=org, record=point)
        



# RabbitMQ
#用户的名字和密码
user_info = pika.PlainCredentials('admin', '123456')
#本地部署，调用AMQR专用端口5672，同时如果要进入管理页面就访问localhost的15672端口即可
connection = pika.BlockingConnection(pika.ConnectionParameters('47.108.169.120', 5672, '/', user_info))
#信道建立
channel = connection.channel()
#建立名字叫durable_queue的队列
channel.queue_declare(queue='durable_queue', durable=True)

def validate_file_data(file_data):
    """验证文件数据是否包含必要字段"""
    required_fields = ['file_name', 'md5', 'count']
    for field in required_fields:
        if field not in file_data:
            raise ValueError(f"缺少必要字段: {field}")
    return True

def callback(ch, method, properties, body):
    try:
        print(f" [debug] 原始消息: {body.decode('utf-8')}")
        data = json.loads(body.decode('utf-8'))

        flag = int(data.get("flag", -1))
        user_id = data.get("user_id")
        
        if not user_id:
            raise ValueError("user_id is required")
        print("start log")
        log_data(url, token, org, bucket, user_id, log_message=data)
        print("end log")
        if flag == 0:
            # 删除该用户所有 files 和关联的 matches
            cursor.execute("DELETE FROM matches WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM files WHERE user_id = %s", (user_id,))
            print(f" [i] 已删除 user_id = {user_id} 所有文件和匹配记录")

        elif flag == 1:
        # 批量更新文件（与 flag=2 逻辑一致，但先清空旧记录）
            if "files" in data:
                for file_data in data["files"]:
                    try:
                        validate_file_data(file_data)
                        # 注入公共字段：user_id 和顶级的 discovery_time
                        file_data.update({
                            "user_id": user_id,
                            "discovery_time": data["discovery_time"]
                        })
                        update_file_and_matches(file_data)  # 调用更新逻辑
                    except Exception as e:
                        print(f" [×] 处理文件数据失败: {e}")
            else:
                raise ValueError("flag=1 需要传递 files 数组")

        elif flag == 2:
        # 批量插入或更新
            if "files" in data:
                for file_data in data["files"]:
                    try:
                        validate_file_data(file_data)
                        file_data.update({
                            "user_id": user_id,
                            "discovery_time": data["discovery_time"]
                        })
                        insert_or_update_file_and_matches(file_data)
                    except Exception as e:
                        print(f" [×] 处理文件数据失败: {e}")
            else:
                try:
                    validate_file_data(data)
                    data.update({
                        "user_id": user_id,
                        "discovery_time": data["discovery_time"]
                    })
                    insert_or_update_file_and_matches(data)
                except Exception as e:
                    print(f" [×] 处理文件数据失败: {e}")

        elif flag == 3:
            # 删除指定的 user_id + file_name 及其匹配记录
            if "files" in data:
                for file_data in data["files"]:
                    file_id = file_data.get("file_name")
                    if not file_id:
                        print(" [×] file_id (file_name) is required for each file in flag=3")
                        continue
                    cursor.execute("DELETE FROM matches WHERE user_id = %s AND file_id = %s", (user_id, file_id))
                    cursor.execute("DELETE FROM files WHERE user_id = %s AND file_id = %s", (user_id, file_id))
                    print(f" [i] 已删除 file_id = {file_id}, user_id = {user_id} 及其匹配记录")
            else:
                file_id = data.get("file_name")
                if not file_id:
                    raise ValueError("file_id is required for flag=3")
                cursor.execute("DELETE FROM matches WHERE user_id = %s AND file_id = %s", (user_id, file_id))
                cursor.execute("DELETE FROM files WHERE user_id = %s AND file_id = %s", (user_id, file_id))
                print(f" [i] 已删除 file_id = {file_id}, user_id = {user_id} 及其匹配记录")

        else:
            print(f" [!] 未知操作 flag: {flag}")

        db.commit()
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f" [×] 错误类型: {type(e).__name__}, 错误详情: {str(e)}")
        db.rollback()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def insert_file_and_matches(data):
    """插入文件记录和关联的匹配记录"""
    
    data["file_id"] = data["file_name"]
    
    sql = """
        INSERT INTO files (file_id, user_id, file_name, md5, discovery_time, count)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            file_name = VALUES(file_name),
            md5 = VALUES(md5),
            discovery_time = VALUES(discovery_time),
            count = VALUES(count)
    """
    cursor.execute(sql, (
        data["file_id"],
        data["user_id"],
        data["file_name"],
        data["md5"],
        data["discovery_time"],
        data["count"]
    ))
    
    # 插入匹配记录
    if "rule_id" in data:
        rule_ids = data["rule_id"] if isinstance(data["rule_id"], list) else [data["rule_id"]]
        for rule_id in rule_ids:
            insert_match_record({
                "file_id": data["file_id"],
                "user_id": data["user_id"],
                "rule_id": rule_id
            })

def update_file_and_matches(data):
    """更新文件记录和关联的匹配记录"""
    if "file_name" not in data:
        raise ValueError("data 必须包含 file_name 字段")
    data["file_id"] = data["file_name"]
    # 先删除旧匹配记录
    cursor.execute(
        "DELETE FROM matches WHERE user_id = %s AND file_id = %s",
        (data["user_id"], data["file_id"])
    )
    # 插入更新后的文件记录
    insert_file_and_matches(data)  # 复用插入逻辑

def insert_or_update_file_and_matches(data):
    
    data["file_id"] = data["file_name"]
    cursor.execute("SELECT 1 FROM files WHERE user_id = %s AND file_id = %s",
                  (data["user_id"], data["file_id"]))
    if cursor.fetchone():
        update_file_and_matches(data)
    else:
        insert_file_and_matches(data)

def insert_match_record(data):
    """插入单个匹配记录"""
    sql = """
        INSERT INTO matches (file_id, user_id, rule_id, match_time)
        VALUES (%s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
            rule_id = VALUES(rule_id)
    """
    cursor.execute(sql, (
        data["file_id"],
        data["user_id"],
        data["rule_id"]
    ))

# 消费逻辑
channel.basic_consume(
    queue='durable_queue',
    auto_ack=False,
    on_message_callback=callback
)

print("等待消息中...（按 Ctrl+C 退出）")
channel.start_consuming()