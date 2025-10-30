import bcrypt
import mysql.connector

# Kết nối database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',  # Thay bằng password MySQL của bạn nếu có
    database='furniture_store'
)

cursor = conn.cursor()

# Xóa admin cũ
cursor.execute("DELETE FROM admin_users WHERE username = 'admin'")

# Tạo password mới
password = 'admin123'
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Insert admin mới
query = """
    INSERT INTO admin_users (username, password, full_name, email)
    VALUES (%s, %s, %s, %s)
"""
cursor.execute(query, ('admin', hashed.decode('utf-8'), 'Administrator', 'admin@furniture.com'))

conn.commit()
print("✅ Đã tạo lại admin thành công!")
print("Username: admin")
print("Password: admin123")

cursor.close()
conn.close()