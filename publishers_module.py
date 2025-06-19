# coding=utf-8
import pika
import json
import datetime

# RabbitMQ连接部分保持不变
user_info = pika.PlainCredentials('root', 'root')  
connection = pika.BlockingConnection(pika.ConnectionParameters('10.175.28.39', 5672, '/', user_info)) 
channel = connection.channel()
channel.queue_declare(queue='durable_queue', durable=True)

# 新格式的消息（不再需要指定file_id）
message = {
    "flag": 2,  # 使用flag=2进行新文件批量插入,flag=0删除该userid下的所有文件,flag=1更新指定文件的信息,flag=3删除指定文件
    "files": [
        {
            "file_name": "filasdawdasds",
            "md5": "masfqwasff",
            "count": 8,
            "rule_id": ["1", "3"],  # 规则列表
        },
        {
            "file_name": "fasfawwadasfd",
            "md5": "masfwqasdra",
            "count": 5,
            "rule_id": ["1"],  # 规则列表
        }
    ],
    "discovery_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "user_id": "1",
    "policy_id": "1"
}

channel.basic_publish(
    exchange='',
    routing_key='durable_queue',
    body=json.dumps(message).encode('utf-8'),
    properties=pika.BasicProperties(delivery_mode=2)
)
print(f" [x] Sent batch message for user {message['user_id']}")

connection.close()