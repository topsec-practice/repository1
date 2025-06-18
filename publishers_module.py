# coding=utf-8
import pika
import json
import datetime

#这里是rabbitMQ的链接部分
#用户的名字和密码
user_info = pika.PlainCredentials('admin', '123456')  
#本地部署，调用AMQR专用端口5672，同时如果要进入管理页面就访问localhost的15672端口即可
connection = pika.BlockingConnection(pika.ConnectionParameters('47.108.169.120', 5672, '/', user_info))
#信道建立
channel = connection.channel()
channel.queue_declare(queue='durable_queue', durable=True)

# 新格式的消息（不再需要指定file_id）
message = {
    "flag": 2,  # 使用flag=2进行批量插入
    "files": [
        {
            "file_name": "file_name1",
            "md5": "md51",
            "count": 8
        },
        {
            "file_name": "file_name2",
            "md5": "md52",
            "count": 5
        },
        {
            "file_name": "file_name3",
            "md5": "md53",
            "count": 10
        }
    ],
    "discovery_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "user_id": "user_2",
    "rule_id": ["1", "3"],  # 规则列表
    "policy_id": "3"
}

channel.basic_publish(
    exchange='',
    routing_key='durable_queue',
    body=json.dumps(message).encode('utf-8'),
    properties=pika.BasicProperties(delivery_mode=2)
)
print(f" [x] Sent batch message for user {message['user_id']}")

connection.close()