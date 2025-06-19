# coding=utf-8
import pika
import pymysql
import json
from datetime import datetime

# 连接数据库
db = pymysql.connect(
    host='47.108.169.120', #服务器名字
    user='remote', #用户
    password='123456',  # 替换为你的真实密码
    database='trx', #数据库名字
    charset='utf8mb4'
)
cursor = db.cursor()

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
        data = json.loads(body.decode('utf-8'))
        flag = int(data.get("flag", -1))
        user_id = data.get("user_id")
        
        if not user_id:
            raise ValueError("user_id is required")

        if flag == 0:
            # 删除该用户所有 files 和关联的 matches
            cursor.execute("DELETE FROM matches WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM files WHERE user_id = %s", (user_id,))
            print(f" [i] 已删除 user_id = {user_id} 所有文件和匹配记录")

        elif flag == 1:
            # 更新指定文件及其匹配记录
            update_file_and_matches(data)
            print(f" [i] 已更新文件和匹配记录: {data.get('file_name', '未知文件')} (user_id: {user_id})")

        elif flag == 2:
            # 处理批量插入或更新
            if "files" in data:
                for file_data in data["files"]:
                    try:
                        validate_file_data(file_data)
                        file_data.update({
                            "user_id": user_id,
                            "discovery_time": data.get("discovery_time", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        })
                        insert_or_update_file_and_matches(file_data)
                        print(f" [i] 已处理文件数据: {file_data.get('file_name', '未知文件')} (user_id: {user_id})")
                    except Exception as e:
                        print(f" [×] 处理文件数据失败: {e}")
                        continue
            else:
                try:
                    validate_file_data(data)
                    data["discovery_time"] = data.get("discovery_time", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    insert_or_update_file_and_matches(data)
                    print(f" [i] 已处理文件数据: {data.get('file_name', '未知文件')} (user_id: {user_id})")
                except Exception as e:
                    print(f" [×] 处理文件数据失败: {e}")
                    raise

        elif flag == 3:
            # 删除指定的 user_id + md5 及其匹配记录
            file_id = data.get("file_id")
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
        print(f" [×] 错误处理消息: {e}")
        db.rollback()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def insert_file_and_matches(data):
    """插入文件记录和关联的匹配记录"""
    
    data["file_id"] = data["md5"]
    
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
    
    data["file_id"] = data["md5"]
    cursor.execute("DELETE FROM matches WHERE user_id = %s AND file_id = %s",
                  (data["user_id"], data["file_id"]))
    insert_file_and_matches(data)

def insert_or_update_file_and_matches(data):
    
    data["file_id"] = data["md5"]
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