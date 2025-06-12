# coding=utf-8
import pika
import pymysql
import json
import time
from datetime import datetime

# 连接数据库
db = pymysql.connect(
    host='localhost', #服务器名字
    user='root', #用户
    password='yjydmm520',  # 替换为你的真实密码
    database='test', #数据库名字
    charset='utf8mb4'
)
cursor = db.cursor()

# RabbitMQ
#用户的名字和密码
user_info = pika.PlainCredentials('root', 'root')
#本地部署，调用AMQR专用端口5672，同时如果要进入管理页面就访问localhost的15672端口即可
connection = pika.BlockingConnection(pika.ConnectionParameters('10.175.28.39', 5672, '/', user_info))
#信道建立
channel = connection.channel()
#建立名字叫durable_queue的队列
channel.queue_declare(queue='durable_queue', durable=True)

# 数据库连接保持不变...

def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode('utf-8'))
        flag = int(data.get("flag", -1))
        user_id = data.get("user_id")
        file_id = data.get("file_id")
        
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

        elif flag == 2:
            # 插入或更新一条文件记录及其匹配记录
            insert_or_update_file_and_matches(data)

        elif flag == 3:
            # 删除指定的 user_id + file_id 及其匹配记录
            cursor.execute("DELETE FROM matches WHERE user_id = %s AND file_id = %s", (user_id, file_id))
            cursor.execute("DELETE FROM files WHERE user_id = %s AND file_id = %s", (user_id, file_id))
            print(f" [i] 已删除 file_id = {file_id}, user_id = {user_id} 及其匹配记录")

        else:
            print(" [!] 未知操作 flag")

        db.commit()
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f" [×] 错误: {e}")
        db.rollback()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def insert_file_and_matches(data):
    """插入文件记录和关联的匹配记录"""
    # 插入文件记录
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
    
    # 插入匹配记录（如果有提供 policy_id 和 rule_id）
    if "policy_id" in data and "rule_id" in data:
        insert_match_record(data)
    
    print(f" [√] 插入/更新文件记录: {data['file_id']}")

def update_file_and_matches(data):
    """更新文件记录和关联的匹配记录"""
    # 先删除旧的匹配记录
    cursor.execute("DELETE FROM matches WHERE user_id = %s AND file_id = %s", 
                  (data["user_id"], data["file_id"]))
    
    # 更新文件记录
    insert_file_and_matches(data)

def insert_or_update_file_and_matches(data):
    """插入或更新文件记录和匹配记录"""
    # 检查文件是否存在
    cursor.execute("SELECT 1 FROM files WHERE user_id = %s AND file_id = %s", 
                  (data["user_id"], data["file_id"]))
    
    if cursor.fetchone():
        # 文件存在，执行更新
        update_file_and_matches(data)
    else:
        # 文件不存在，执行插入
        insert_file_and_matches(data)

def insert_match_record(data):
    """插入单个匹配记录"""
    sql = """
        INSERT INTO matches (policy_id, file_id, user_id, rule_id)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            rule_id = VALUES(rule_id)
    """
    cursor.execute(sql, (
        data["policy_id"],
        data["file_id"],
        data["user_id"],
        data["rule_id"]
    ))
    print(f" [√] 插入/更新匹配记录: policy_id={data['policy_id']}, rule_id={data['rule_id']}")

# 消费逻辑保持不变...

#消费的逻辑
channel.basic_consume(
    queue='durable_queue',#队列名字
    auto_ack=False,#是否自动ack
    on_message_callback=callback#调用callback类的方法
)

print("等待消息中...（按 Ctrl+C 退出）")
channel.start_consuming()