# coding=utf-8
import pika
import pymysql
import json
import time
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

# 数据库连接保持不变...

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
                        update_file_and_matches(data,cursor)

                    elif flag == 2:
                    # 批量处理文件
                        if "files" not in data:
                            raise ValueError("Missing 'files' array in message")
                
                        # 获取下一个可用的file_id
                        next_file_id = get_next_file_id(user_id)
                        discovery_time = data.get("discovery_time", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        count = data.get("count", 0)
                        policy_id = data.get("policy_id")
                        rule_ids = data.get("rule_id", [])
                        
                        for file_data in data["files"]:
                            current_file_id = str(next_file_id)
                            next_file_id += 1
                    
                            # 合并公共数据到每个文件记录
                            file_data.update({
                                "file_id": current_file_id,
                                "user_id": user_id,
                                "discovery_time": discovery_time,
                                "count": count,
                                "policy_id": policy_id
                            })
                    
                            # 插入或更新文件记录
                            insert_file_and_matches(file_data, cursor)
                    
                            # 为每个规则创建匹配记录
                            if policy_id and rule_ids:
                                for rule_id in rule_ids:
                                    match_data = {
                                        "policy_id": policy_id,
                                        "file_id": current_file_id,
                                        "user_id": user_id,
                                        "rule_id": rule_id
                                    }
                                    insert_match_record(match_data,cursor)

                    elif flag == 3:
                        file_id = data.get("file_id")
                        if not file_id:
                            raise ValueError("file_id is required for flag=3")
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

            # 开始消费消息
            channel.basic_consume(
                queue='durable_queue',
                on_message_callback=callback,
                auto_ack=False  # 手动确认消息
            )

            print("Waiting for messages... (Press Ctrl+C to exit)")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            print(f"RabbitMQ connection error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("Shutting down gracefully...")
            try:
                if 'connection' in locals() and connection.is_open:
                    connection.close()
            except:
                pass
            try:
                if 'db' in locals() and db.open:
                    db.close()
            except:
                pass
            break
        except Exception as e:
            print(f"Unexpected error: {e}. Restarting in 5 seconds...")
            time.sleep(5)
        finally:
            try:
                if 'connection' in locals() and connection.is_open:
                    connection.close()
            except:
                pass
            try:
                if 'db' in locals() and db.open:
                    db.close()
            except:
                pass

def insert_file_and_matches(data, cursor):
    """插入文件记录和关联的匹配记录"""
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
        count
    ))
    # 插入匹配记录（如果有提供 policy_id 和 rule_id）
    if "policy_id" in data and "rule_id" in data:
        # rule_id 可能为列表
        if isinstance(data["rule_id"], list):
            for rule in data["rule_id"]:
                insert_match_record({
                    "policy_id": data["policy_id"],
                    "file_id": data["file_id"],
                    "user_id": data["user_id"],
                    "rule_id": rule
                })
        else:
            insert_match_record(data)
    print(f" [√] 插入/更新文件记录: {data['file_id']}")

def update_file_and_matches(data):
    """更新文件记录和关联的匹配记录"""
    cursor.execute("DELETE FROM matches WHERE user_id = %s AND file_id = %s",
                  (data["user_id"], data["file_id"]))
    insert_file_and_matches(data)

def insert_or_update_file_and_matches(data):
    cursor.execute("SELECT 1 FROM files WHERE user_id = %s AND file_id = %s",
                  (data["user_id"], data["file_id"]))
    if cursor.fetchone():
        update_file_and_matches(data)
    else:
        insert_file_and_matches(data)

def insert_match_record(data, cursor):
    """Insert a single match record"""
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
    print(f" [√] Inserted/updated match record: policy_id={data['policy_id']}, rule_id={data['rule_id']}")

if __name__ == "__main__":
    main()