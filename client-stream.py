#生产者
import asyncio
from rstream import Producer

STREAM_NAME = "hello-python-stream"
STREAM_RETENTION = 5000000000  # 5GB

async def send():
    producer = Producer(
        host="localhost",
        port=5552,  # 明确指定端口
        username="root",
        password="root",
    )
    await producer.start()  # 显式启动

    # 确保流存在
    await producer.create_stream(
        STREAM_NAME,
        exists_ok=True,
        arguments={"max-length-bytes": STREAM_RETENTION}
    )

    # 发送消息并等待确认
    await producer.send_wait(stream=STREAM_NAME, message=b"Hello, World!")
    print(" [x] Message sent and confirmed")

    input("Press Enter to exit...")  # 保持连接以便调试
    await producer.close()

if __name__ == "__main__":
    asyncio.run(send())