# coding=utf-8
import pika
import json
import datetime

#这里是rabbitMQ的链接部分
#用户的名字和密码
user_info = pika.PlainCredentials('root', 'root')  
#本地部署，调用AMQR专用端口5672，同时如果要进入管理页面就访问localhost的15672端口即可
connection = pika.BlockingConnection(pika.ConnectionParameters('47.108.169.120', 5672, '/', user_info))
#信道建立
channel = connection.channel()
#建立名字叫durable_queue的队列
channel.queue_declare(queue='durable_queue', durable=True)


#这里的message内容化成你们数据库的内容即可（或者你们时存到某个缓存中，反正调用它的内容，注意rule_id和policy_id我个人认为是固定的已知的）
#也就是说如果要做到全覆盖需要在第一个数据包调用flag=0，后续数据包调用2即可，比如设置message1中flag=0，后续添加一个循环message2中flag=2
#for i in range(1, 6):
message = {
        "flag": 0,  # 0删除该用户所有 files 和关联的 matches；1更新指定文件及其匹配记录（file_id+user_id确定）；2插入一条文件记录及其匹配记录；3删除删除指定的 user_id + file_id 及其匹配记录
        "file_id": f"file_id2",
        "file_name": f"file_name2",
        "md5": f"md53",
        "discovery_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "user_id": "user_2",
        "count": 8,
        "rule_id": "rule1",
        "policy_id": "policy1"
}

    #信道传输的基本信息，比如虚拟机、路由密钥、数据本体（utf-8封装）
channel.basic_publish( #这里是传输到rabbitmq的关键函数，你也可以循环调用，反正用一次这个函数就传一次message
        exchange='',  #虚拟机
        routing_key='durable_queue', #路由密钥
        body=json.dumps(message).encode('utf-8'), #数据本体（utf-8封装），用一个叫body的来存储
        properties=pika.BasicProperties(delivery_mode=2) #调用rabbitMQ来转化为二进制传输
    )
print(f" [x] Sent flag={message['flag']} file_id={message['file_id']}")#为了校验是否传入

connection.close() #完成传输