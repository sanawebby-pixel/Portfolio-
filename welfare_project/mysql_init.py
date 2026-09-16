import pymysql


def ensure_database():
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='',
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS welfare_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.close()
    print('Database ready: welfare_db')


if __name__ == '__main__':
    ensure_database()
