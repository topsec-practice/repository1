import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
org = "trx"
url = "http://localhost:8086"
token = 'PGrDLJWSk18Cq1C8h7pKKn8J5EbMR2slKjdE7UN9cmz6scmaj2IX3L1Eq-dlFQ26s6pC_JUoEAMGu-Gl8cVEgQ=='

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
    
if __name__ == "__main__":
    org = "trx"
    url = "http://localhost:8086"
    token = 'PGrDLJWSk18Cq1C8h7pKKn8J5EbMR2slKjdE7UN9cmz6scmaj2IX3L1Eq-dlFQ26s6pC_JUoEAMGu-Gl8cVEgQ=='
    bucket = "test"
    user_id = "user_1"
    log_message = "This is a log message."
    
   