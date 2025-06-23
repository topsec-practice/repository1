import pymysql
 


def upload(db, cursor, user_id, files):
    try:
        for file in files:
            # 插入文件信息到数据库
            md5 = file["md5"]
            file_name = file["name"]
            discovery_time = file["discovery_time"]
            file_id = file["file_id"]
            count = file["count"]
            # trx.sql: files(file_id, user_id, md5, file_name, discovery_time, count)
            sql = "INSERT INTO files (file_id, user_id, md5, file_name, discovery_time, count) VALUES (%s, %s, %s, %s, %s, %s)"
            value = (file_id, user_id, md5, file_name, discovery_time, count)
            cursor.execute(sql, value)

            # 更新matches表
            policy_id = file["policy_id"]
            rule_id = file["rule_id"]
            # rule_id 是个列表
            for rule in rule_id:
                # trx.sql: matches(file_id, policy_id, rule_id, user_id)
                sql = "INSERT INTO matches (file_id, policy_id, rule_id, user_id) VALUES (%s, %s, %s, %s)"
                value = (file_id, policy_id, rule, user_id)
                cursor.execute(sql, value)

            db.commit()
        print("Files uploaded successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()

def update_user_status(db, cursor, user_id, status, LastEchoTime):
    try:
        # trx.sql: user(user_id, status, LastEchoTime, ...)
        sql = "UPDATE user SET status = %s, LastEchoTime = %s WHERE user_id = %s"
        cursor.execute(sql, (status, LastEchoTime, user_id))
        db.commit()
        print("update user status success")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()

def delete_file(db, cursor, file_id, user_id, policy_id):
    try:
        # 删除文件信息
        sql = "DELETE FROM files WHERE file_id = %s AND user_id = %s"
        cursor.execute(sql, (file_id, user_id))
        # 删除匹配记录
        sql = "DELETE FROM matches WHERE file_id = %s AND user_id = %s AND policy_id = %s"
        cursor.execute(sql, (file_id, user_id, policy_id))
        db.commit()
        print("File deleted successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()

def update_file(db, cursor, file_id, user_id, new_md5, new_file_name, count, discovery_time, policy_id, rule_id):
    try:
        # 更新文件信息
        sql = "UPDATE files SET md5 = %s, file_name = %s, discovery_time = %s, count = %s WHERE file_id = %s AND user_id = %s"
        cursor.execute(sql, (new_md5, new_file_name, discovery_time, count, file_id, user_id))
        # 先删除旧的matches
        sql = "DELETE FROM matches WHERE file_id = %s AND user_id = %s"
        cursor.execute(sql, (file_id, user_id))
        # 重新插入matches
        for rule in rule_id:
            sql = "INSERT INTO matches (file_id, policy_id, rule_id, user_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (file_id, policy_id, rule, user_id))
        db.commit()
        print("File updated successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()

def get_file_policy_rule_info(db, cursor, user_id):
    try:
        sql = """
        SELECT 
            f.file_id,
            f.file_name,
            f.md5,
            f.discovery_time,
            f.count,
            m.policy_id,
            p.policy_description,
            m.rule_id,
            r.rule_description
        FROM files f
        JOIN matches m ON f.file_id = m.file_id AND f.user_id = m.user_id
        LEFT JOIN policy p ON m.policy_id = p.policy_id
        LEFT JOIN rules r ON m.rule_id = r.rule_id
        WHERE f.user_id = %s
        """
        cursor.execute(sql, (user_id,))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error: {e}")
        return []

def insert_policy(db, cursor, policy_id, policy_description):
    try:
        sql = "INSERT INTO policy (policy_id, policy_description) VALUES (%s, %s)"
        cursor.execute(sql, (policy_id, policy_description))
        db.commit()
        print("Policy inserted successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()

def insert_rule(db, cursor, rule_id, policy_id, rule_description):
    try:
        sql = "INSERT INTO rules (rule_id, policy_id, rule_description) VALUES (%s, %s, %s)"
        cursor.execute(sql, (rule_id, policy_id, rule_description))
        db.commit()
        print("Rule inserted successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()

def get_max_policyid(cursor):
    try:
        sql = "SELECT max(CAST(policy_id AS UNSIGNED)) FROM policy"
        cursor.execute(sql)
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_all_policies(cursor):
    try:
        sql = "SELECT * FROM policy"
        cursor.execute(sql)
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_all_rules(cursor, policy_id):
    try:
        sql = """
        SELECT r.rule_id, r.rule_description
        FROM policy_rules pr
        JOIN rules r ON pr.rule_id = r.rule_id
        WHERE pr.policy_id = %s
        ORDER BY CAST(r.rule_id AS UNSIGNED) ASC
        """
        cursor.execute(sql, (policy_id,))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error: {e}")
        return []
    
def get_policy_path(cursor, policy_id):
    try:
        sql = "SELECT policy_path FROM policy WHERE policy_id = %s"
        cursor.execute(sql, (policy_id,))
        result = cursor.fetchone()
        return result[0]
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_all_users(cursor, admin_id):
    try:
        sql = "SELECT * FROM user WHERE admin_id = %s"
        cursor.execute(sql, (admin_id,))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error: {e}")
        return []

def update_user_policy(db, cursor, user_id, policy_id):
    try:
        sql = "UPDATE user SET policy_id = %s WHERE user_id = %s"
        cursor.execute(sql, (policy_id, user_id))
        db.commit()
        print("update user policy success")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()



if __name__ == "__main__":
    db = pymysql.connect(
    host="localhost", 
    user="root", 
    password="123456",
    database="trx" 
)

    cursor = db.cursor()
    # 测试代码
    user_id = "test_user"
    files = [
        {
            "md5": "1234567890abcdef",
            "name": "test_file",
            "discovery_time": "2023-10-01 12:00:00",
            "file_id": "file_001",
            "count": 1,
            "policy_id": "policy_001",
            "rule_id": ["rule_001", "rule_002"]
        }
    ]

    # upload(db, cursor, user_id, files)
    # print(get_file_policy_rule_info(db, cursor, user_id))
    # delete_file(db, cursor, "file_001", user_id, "policy_001")
    # update_file(db, cursor, "file_001", user_id, "new_md5", "new_file_name.txt", 2, "2023-10-02 12:00:00", "policy_002", ["rule_003"])
    print(get_all_policies(cursor))
    print(get_all_rules(cursor, "policy_001"))
    print(get_all_users(cursor, "1"))
    
    cursor.close()
    db.close()