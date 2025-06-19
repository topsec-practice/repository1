import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import json

org = "trx"
url = "http://47.108.169.120:8086"
token = 'YkXOflEN22TCy2cZSndeY6KIOZeatb99QwecnptwJDZ_ehVqiYGXR8ihOW9oOKFQCBtgGfhY70ww0QhNe3I8uw=='

def log_data(url, token, org, bucket, user_id, log_message):
    with InfluxDBClient(url=url, token=token, org=org) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = (
            Point("measurement1")
            .tag("user_id", user_id)
            .field("log", log_message)
        )
        write_api.write(bucket=bucket, org=org, record=point)


def query_logs(url, token, org, bucket, start_time, user_id):
    with InfluxDBClient(url=url, token=token, org=org) as client:
        query_api = client.query_api()
        query = f"""from(bucket: "{bucket}")
        |> range(start: {start_time})
        |> filter(fn: (r) => r._measurement == "measurement1" and r.user_id == {user_id})"""
        tables = query_api.query(query, org=org)
        logs = []
        for table in tables:
            for record in table.records:
                logs.append(
                    {
                        "time": record.get_time(),
                        "value": record.get_value(), # value 是操作
                        "user_id": record.values.get("user_id")
                    }
                )

        return logs
    
def get_upload_logs(url, token, org, bucket, start_time="0"):
    with InfluxDBClient(url=url, token=token, org=org) as client:
        query_api = client.query_api()
        query = f'''from(bucket: "{bucket}")
        |> range(start: {start_time})
        |> filter(fn: (r) => r._measurement == "measurement1")
        '''
        tables = query_api.query(query, org=org)
        logs = []
        for table in tables:
            for record in table.records:
                try:
                    log_value = record.get_value()
                    log_json = json.loads(log_value)
                    # 拆分每个文件
                    if isinstance(log_json, dict) and "files" in log_json:
                        for file in log_json["files"]:
                            entry = {
                                "time": record.get_time(),
                                "user_id": record.values.get("user_id"),
                                "flag": log_json.get("flag"),
                                "policy_id": log_json.get("policy_id"),
                                "discovery_time": log_json.get("discovery_time"),
                                **file
                            }
                            logs.append(entry)
                    else:
                        # 单文件情况
                        entry = {
                            "time": record.get_time(),
                            "user_id": record.values.get("user_id"),
                            **log_json
                        }
                        logs.append(entry)
                except Exception as e:
                    continue
        return logs

if __name__ == "__main__":
    org = "trx"
    url = "http://47.108.169.120:8086"
    token = 'YkXOflEN22TCy2cZSndeY6KIOZeatb99QwecnptwJDZ_ehVqiYGXR8ihOW9oOKFQCBtgGfhY70ww0QhNe3I8uw=='
    bucket = "log"

