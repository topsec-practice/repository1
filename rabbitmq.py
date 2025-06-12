# coding=utf-8
import pika
import pymysql
import json
import time

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

#操作类
def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode('utf-8'))#从队列里提取消息（找body）
        flag = int(data.get("flag", -1))  # 默认为 -1

        user_id = data.get("user_id")
        file_id = data.get("file_id")

        if not user_id:#确保一定传入了user_id
            raise ValueError("user_id is required")

        if flag == 0:
            # 删除该用户所有 files，再插入当前记录，也就是全覆盖
            cursor.execute("DELETE FROM files WHERE user_id = %s", (user_id,))#删除
            print(f" [i] 已删除 user_id = {user_id} 所有文件")
            insert_file(data)#插入

        elif flag == 1:
            # 更新指定文件
            cursor.execute("DELETE FROM files WHERE user_id = %s AND file_id = %s", (user_id, file_id))
            insert_file(data)

        elif flag == 2:
            # 仅插入一条记录（如存在，可选择更新或忽略）
            insert_file(data)

        elif flag == 3:
            # 删除指定的 user_id + file_id
            cursor.execute("DELETE FROM files WHERE user_id = %s AND file_id = %s", (user_id, file_id))
            print(f" [i] 已删除 file_id = {file_id}, user_id = {user_id}")

        else:
            #flag不规范
            print(" [!] 未知操作 flag")

        db.commit()
        ch.basic_ack(delivery_tag=method.delivery_tag)

    #如果出现错误，就回滚数据库，恢复原样
    except Exception as e:
        print(f" [×] 错误: {e}")
        db.rollback()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


#该插入语法用于在插入数据时，如果目标表中存在与新插入行冲突的唯一索引或主键值，则更新原有行；
#如果不存在冲突，则插入新行。该语法基于表中已建立的主键约束来判断是否存在重复记录
def insert_file(data):
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
    print(f" [√] 插入/更新文件记录: {data['file_id']}")

#消费的逻辑
channel.basic_consume(
    queue='durable_queue',#队列名字
    auto_ack=False,#是否自动ack
    on_message_callback=callback#调用callback类的方法
)

print("等待消息中...（按 Ctrl+C 退出）")
channel.start_consuming()