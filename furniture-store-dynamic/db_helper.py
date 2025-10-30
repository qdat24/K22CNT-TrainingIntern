import mysql.connector
from mysql.connector import Error
import bcrypt

# Cấu hình database
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345678',  # Thay đổi password của bạn
    'database': 'furniture_store',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def get_db_connection():
    """Tạo kết nối đến database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Lỗi kết nối database: {e}")
        return None

def execute_query(query, params=None, fetch=False, fetch_one=False):
    """
    Thực thi câu lệnh SQL
    
    Args:
        query: Câu lệnh SQL
        params: Tham số cho prepared statement
        fetch: True nếu cần lấy kết quả (SELECT)
        fetch_one: True nếu chỉ lấy 1 kết quả
    
    Returns:
        Kết quả query hoặc None
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchone() if fetch_one else cursor.fetchall()
            return result
        else:
            connection.commit()
            return cursor.lastrowid if cursor.lastrowid else True
            
    except Error as e:
        print(f"Lỗi thực thi query: {e}")
        if not fetch:
            connection.rollback()
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Hàm helper cho sản phẩm
def get_all_products(category=None, active_only=True):
    """Lấy tất cả sản phẩm"""
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    
    if active_only:
        query += " AND is_active = TRUE"
    
    if category:
        query += " AND category = %s"
        params.append(category)
    
    query += " ORDER BY created_at DESC"
    
    products = execute_query(query, tuple(params) if params else None, fetch=True)
    
    # Chuyển đổi features từ string sang list
    if products:
        for product in products:
            if product['features']:
                product['features'] = product['features'].split('|')
            else:
                product['features'] = []
    
    return products

def get_product_by_id(product_id):
    """Lấy sản phẩm theo ID"""
    query = "SELECT * FROM products WHERE id = %s"
    product = execute_query(query, (product_id,), fetch=True, fetch_one=True)
    
    # DEBUG
    print(f"🔍 get_product_by_id({product_id}): {product is not None}")
    
    if product and product.get('features'):
        product['features'] = product['features'].split('|')
    
    return product

def create_product(data):
    """Tạo sản phẩm mới"""
    features_str = '|'.join(data['features']) if isinstance(data['features'], list) else data['features']
    
    query = """
        INSERT INTO products (name, category, price, original_price, image, description, features, rating, reviews, stock)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        data['name'],
        data['category'],
        data['price'],
        data.get('original_price', data['price']),
        data.get('image', ''),
        data.get('description', ''),
        features_str,
        data.get('rating', 5.0),
        data.get('reviews', 0),
        data.get('stock', 100)
    )
    
    return execute_query(query, params)

def update_product(product_id, data):
    """Cập nhật sản phẩm"""
    features_str = '|'.join(data['features']) if isinstance(data['features'], list) else data['features']
    
    query = """
        UPDATE products 
        SET name = %s, category = %s, price = %s, original_price = %s, 
            image = %s, description = %s, features = %s, rating = %s, 
            reviews = %s, stock = %s, is_active = %s
        WHERE id = %s
    """
    params = (
        data['name'],
        data['category'],
        data['price'],
        data.get('original_price', data['price']),
        data.get('image', ''),
        data.get('description', ''),
        features_str,
        data.get('rating', 5.0),
        data.get('reviews', 0),
        data.get('stock', 100),
        data.get('is_active', True),
        product_id
    )
    
    return execute_query(query, params)

def delete_product(product_id):
    """Xóa sản phẩm (soft delete)"""
    query = "UPDATE products SET is_active = FALSE WHERE id = %s"
    return execute_query(query, (product_id,))

def hard_delete_product(product_id):
    """Xóa vĩnh viễn sản phẩm"""
    query = "DELETE FROM products WHERE id = %s"
    return execute_query(query, (product_id,))

# Hàm helper cho categories
def get_all_categories():
    """Lấy tất cả danh mục"""
    query = "SELECT * FROM categories ORDER BY name"
    return execute_query(query, fetch=True)

def get_category_names():
    """Lấy danh sách tên categories"""
    categories = get_all_categories()
    return [cat['name'] for cat in categories] if categories else []

# Hàm helper cho admin
def verify_admin(username, password):
    """Xác thực admin"""
    query = "SELECT * FROM admin_users WHERE username = %s AND is_active = TRUE"
    admin = execute_query(query, (username,), fetch=True, fetch_one=True)
    
    # DEBUG
    print(f"DEBUG: Looking for admin: {username}")
    print(f"DEBUG: Admin found: {admin is not None}")
    
    if admin:
        print(f"DEBUG: Stored hash starts with: {admin['password'][:10]}")
        print(f"DEBUG: Password to check: {password}")
        
        try:
            result = bcrypt.checkpw(password.encode('utf-8'), admin['password'].encode('utf-8'))
            print(f"DEBUG: Bcrypt result: {result}")
            
            if result:
                # Cập nhật last_login
                update_query = "UPDATE admin_users SET last_login = NOW() WHERE id = %s"
                execute_query(update_query, (admin['id'],))
                return admin
        except Exception as e:
            print(f"DEBUG: Bcrypt error: {e}")
    
    return None

def create_admin(username, password, full_name, email):
    """Tạo admin mới"""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    query = """
        INSERT INTO admin_users (username, password, full_name, email)
        VALUES (%s, %s, %s, %s)
    """
    params = (username, hashed.decode('utf-8'), full_name, email)
    
    return execute_query(query, params)

# Hàm helper cho khách hàng
def create_customer(email, password, full_name, phone=None, address=None):
    """Tạo khách hàng mới"""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    query = """
        INSERT INTO customers (email, password, full_name, phone, address)
        VALUES (%s, %s, %s, %s, %s)
    """
    params = (email, hashed.decode('utf-8'), full_name, phone, address)
    
    return execute_query(query, params)

def verify_customer(email, password):
    """Xác thực khách hàng"""
    query = "SELECT * FROM customers WHERE email = %s AND is_active = TRUE"
    customer = execute_query(query, (email,), fetch=True, fetch_one=True)
    
    if customer and bcrypt.checkpw(password.encode('utf-8'), customer['password'].encode('utf-8')):
        # Cập nhật last_login
        update_query = "UPDATE customers SET last_login = NOW() WHERE id = %s"
        execute_query(update_query, (customer['id'],))
        return customer
    
    return None

def get_customer_by_id(customer_id):
    """Lấy thông tin khách hàng theo ID"""
    query = "SELECT * FROM customers WHERE id = %s"
    return execute_query(query, (customer_id,), fetch=True, fetch_one=True)

def get_customer_by_email(email):
    """Lấy thông tin khách hàng theo email"""
    query = "SELECT * FROM customers WHERE email = %s"
    return execute_query(query, (email,), fetch=True, fetch_one=True)

def update_customer(customer_id, data):
    """Cập nhật thông tin khách hàng"""
    query = """
        UPDATE customers 
        SET full_name = %s, phone = %s, address = %s
        WHERE id = %s
    """
    params = (
        data.get('full_name'),
        data.get('phone'),
        data.get('address'),
        customer_id
    )
    
    return execute_query(query, params)

def update_customer_password(customer_id, new_password):
    """Cập nhật mật khẩu khách hàng"""
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    query = "UPDATE customers SET password = %s WHERE id = %s"
    return execute_query(query, (hashed.decode('utf-8'), customer_id))

# Hàm helper cho đơn hàng
def create_order(order_data):
    """Tạo đơn hàng mới"""
    query = """
        INSERT INTO orders (order_id, customer_id, customer_name, phone, email, address, note, 
                          payment_method, subtotal, shipping_fee, total, status, payment_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        order_data['order_id'],
        order_data.get('customer_id'),
        order_data['customer_name'],
        order_data['phone'],
        order_data.get('email', ''),
        order_data['address'],
        order_data.get('note', ''),
        order_data['payment_method'],
        order_data['subtotal'],
        order_data['shipping_fee'],
        order_data['total'],
        order_data.get('status', 'pending'),
        order_data.get('payment_status', 'pending')
    )
    
    order_id = execute_query(query, params)
    
    # Thêm order items
    if order_id and 'items' in order_data:
        for item in order_data['items']:
            create_order_item(order_data['order_id'], item)
    
    return order_id

def create_order_item(order_id, item_data):
    """Tạo chi tiết đơn hàng"""
    query = """
        INSERT INTO order_items (order_id, product_id, product_name, price, quantity, subtotal)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        order_id,
        item_data['product_id'],
        item_data['name'],
        item_data['price'],
        item_data['quantity'],
        item_data['subtotal']
    )
    
    return execute_query(query, params)

def get_order_by_id(order_id):
    """Lấy đơn hàng theo order_id"""
    query = "SELECT * FROM orders WHERE order_id = %s"
    order = execute_query(query, (order_id,), fetch=True, fetch_one=True)
    
    if order:
        # Lấy order items
        items_query = "SELECT * FROM order_items WHERE order_id = %s"
        order['items'] = execute_query(items_query, (order_id,), fetch=True)
    
    return order

def get_all_orders(limit=None):
    """Lấy tất cả đơn hàng"""
    query = "SELECT * FROM orders ORDER BY created_at DESC"
    if limit:
        query += f" LIMIT {limit}"
    
    return execute_query(query, fetch=True)

def update_order_status(order_id, status, payment_status=None):
    """Cập nhật trạng thái đơn hàng"""
    if payment_status:
        query = "UPDATE orders SET status = %s, payment_status = %s WHERE order_id = %s"
        params = (status, payment_status, order_id)
    else:
        query = "UPDATE orders SET status = %s WHERE order_id = %s"
        params = (status, order_id)
    
    return execute_query(query, params)

# Helper để đếm
def count_products(active_only=True):
    """Đếm số lượng sản phẩm"""
    query = "SELECT COUNT(*) as total FROM products"
    if active_only:
        query += " WHERE is_active = TRUE"
    
    result = execute_query(query, fetch=True, fetch_one=True)
    return result['total'] if result else 0

def count_orders():
    """Đếm số lượng đơn hàng"""
    query = "SELECT COUNT(*) as total FROM orders"
    result = execute_query(query, fetch=True, fetch_one=True)
    return result['total'] if result else 0

def get_revenue_stats():
    """Lấy thống kê doanh thu"""
    query = """
        SELECT 
            SUM(total) as total_revenue,
            COUNT(*) as total_orders,
            AVG(total) as avg_order_value
        FROM orders 
        WHERE payment_status = 'paid'
    """
    return execute_query(query, fetch=True, fetch_one=True)
