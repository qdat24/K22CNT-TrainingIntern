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

# ==================== Site Settings Functions ====================

def get_all_settings():
    """Lấy tất cả cài đặt website"""
    query = "SELECT * FROM site_settings ORDER BY setting_key"
    return execute_query(query, fetch=True)

def get_setting(setting_key, default=None):
    """Lấy giá trị của một cài đặt theo key"""
    query = "SELECT setting_value FROM site_settings WHERE setting_key = %s"
    result = execute_query(query, (setting_key,), fetch=True, fetch_one=True)
    return result['setting_value'] if result else default

def get_settings_dict():
    """Lấy tất cả cài đặt dưới dạng dictionary"""
    settings = get_all_settings()
    return {s['setting_key']: s['setting_value'] for s in settings} if settings else {}

def update_setting(setting_key, setting_value):
    """Cập nhật giá trị của một cài đặt"""
    query = """
        UPDATE site_settings 
        SET setting_value = %s, updated_at = NOW()
        WHERE setting_key = %s
    """
    return execute_query(query, (setting_value, setting_key))

def update_multiple_settings(settings_dict):
    """Cập nhật nhiều cài đặt cùng lúc"""
    success = True
    for key, value in settings_dict.items():
        if not update_setting(key, value):
            success = False
    return success

def create_setting(setting_key, setting_value, description=''):
    """Tạo một cài đặt mới"""
    query = """
        INSERT INTO site_settings (setting_key, setting_value, description)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            setting_value = VALUES(setting_value),
            description = VALUES(description),
            updated_at = NOW()
    """
    return execute_query(query, (setting_key, setting_value, description))

# ==================== Contact Functions ====================

def create_contact(contact_data):
    """Tạo tin nhắn liên hệ mới"""
    query = """
        INSERT INTO contacts (name, email, phone, subject, message, status)
        VALUES (%s, %s, %s, %s, %s, 'new')
    """
    params = (
        contact_data['name'],
        contact_data['email'],
        contact_data.get('phone', ''),
        contact_data['subject'],
        contact_data['message']
    )
    return execute_query(query, params)

def get_all_contacts(status=None, limit=None):
    """Lấy danh sách liên hệ"""
    query = "SELECT * FROM contacts"
    params = []
    
    if status:
        query += " WHERE status = %s"
        params.append(status)
    
    query += " ORDER BY created_at DESC"
    
    if limit:
        query += " LIMIT %s"
        params.append(limit)
    
    return execute_query(query, tuple(params) if params else None, fetch=True)

def get_contact_by_id(contact_id):
    """Lấy chi tiết một liên hệ"""
    query = "SELECT * FROM contacts WHERE id = %s"
    return execute_query(query, (contact_id,), fetch=True, fetch_one=True)

def update_contact_status(contact_id, status, replied=False):
    """Cập nhật trạng thái liên hệ"""
    query = """
        UPDATE contacts 
        SET status = %s, replied = %s
        WHERE id = %s
    """
    return execute_query(query, (status, replied, contact_id))

def count_contacts(status=None):
    """Đếm số lượng liên hệ"""
    query = "SELECT COUNT(*) as total FROM contacts"
    params = None
    
    if status:
        query += " WHERE status = %s"
        params = (status,)
    
    result = execute_query(query, params, fetch=True, fetch_one=True)
    return result['total'] if result else 0

# ============================================
# HÀM QUẢN LÝ KHÁCH HÀNG CHO ADMIN
# ============================================

def get_all_customers(search=None, status_filter=None, limit=None, offset=0):
    """
    Lấy danh sách tất cả khách hàng với tìm kiếm và lọc
    
    Args:
        search: Từ khóa tìm kiếm (tên, email, số điện thoại)
        status_filter: Lọc theo trạng thái (active, inactive)
        limit: Số lượng kết quả tối đa
        offset: Vị trí bắt đầu lấy dữ liệu
    
    Returns:
        List các khách hàng
    """
    query = "SELECT * FROM customers WHERE 1=1"
    params = []
    
    # Tìm kiếm
    if search:
        query += " AND (full_name LIKE %s OR email LIKE %s OR phone LIKE %s)"
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern])
    
    # Lọc theo trạng thái
    if status_filter == 'active':
        query += " AND is_active = TRUE"
    elif status_filter == 'inactive':
        query += " AND is_active = FALSE"
    
    # Sắp xếp
    query += " ORDER BY created_at DESC"
    
    # Giới hạn và phân trang
    if limit:
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
    
    return execute_query(query, tuple(params) if params else None, fetch=True) or []

def count_customers(search=None, status_filter=None):
    """
    Đếm số lượng khách hàng với điều kiện tìm kiếm và lọc
    
    Args:
        search: Từ khóa tìm kiếm
        status_filter: Lọc theo trạng thái
    
    Returns:
        Số lượng khách hàng
    """
    query = "SELECT COUNT(*) as total FROM customers WHERE 1=1"
    params = []
    
    if search:
        query += " AND (full_name LIKE %s OR email LIKE %s OR phone LIKE %s)"
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern])
    
    if status_filter == 'active':
        query += " AND is_active = TRUE"
    elif status_filter == 'inactive':
        query += " AND is_active = FALSE"
    
    result = execute_query(query, tuple(params) if params else None, fetch=True, fetch_one=True)
    return result['total'] if result else 0

def toggle_customer_status(customer_id):
    """
    Chuyển đổi trạng thái khách hàng (kích hoạt/vô hiệu hóa)
    
    Args:
        customer_id: ID của khách hàng
    
    Returns:
        True nếu thành công, False nếu thất bại
    """
    query = "UPDATE customers SET is_active = NOT is_active WHERE id = %s"
    return execute_query(query, (customer_id,))

def delete_customer(customer_id):
    """
    Xóa khách hàng
    
    Args:
        customer_id: ID của khách hàng
    
    Returns:
        True nếu thành công, False nếu thất bại
    """
    # Trước khi xóa, set customer_id = NULL cho các đơn hàng liên quan
    update_orders_query = "UPDATE orders SET customer_id = NULL WHERE customer_id = %s"
    execute_query(update_orders_query, (customer_id,))
    
    # Xóa khách hàng
    query = "DELETE FROM customers WHERE id = %s"
    return execute_query(query, (customer_id,))

def get_customer_stats():
    """
    Lấy thống kê về khách hàng
    
    Returns:
        Dict chứa các thống kê
    """
    stats = {}
    
    # Tổng số khách hàng
    total_query = "SELECT COUNT(*) as total FROM customers"
    total_result = execute_query(total_query, fetch=True, fetch_one=True)
    stats['total'] = total_result['total'] if total_result else 0
    
    # Khách hàng đang hoạt động
    active_query = "SELECT COUNT(*) as total FROM customers WHERE is_active = TRUE"
    active_result = execute_query(active_query, fetch=True, fetch_one=True)
    stats['active'] = active_result['total'] if active_result else 0
    
    # Khách hàng bị khóa
    stats['inactive'] = stats['total'] - stats['active']
    
    # Khách hàng mới trong tháng này
    new_query = """
        SELECT COUNT(*) as total FROM customers 
        WHERE MONTH(created_at) = MONTH(CURRENT_DATE()) 
        AND YEAR(created_at) = YEAR(CURRENT_DATE())
    """
    new_result = execute_query(new_query, fetch=True, fetch_one=True)
    stats['new_this_month'] = new_result['total'] if new_result else 0
    
    return stats

def update_customer_by_admin(customer_id, data):
    """
    Admin cập nhật thông tin khách hàng (bao gồm cả trạng thái)
    
    Args:
        customer_id: ID khách hàng
        data: Dict chứa thông tin cần cập nhật
    
    Returns:
        True nếu thành công, False nếu thất bại
    """
    query = """
        UPDATE customers 
        SET full_name = %s, phone = %s, address = %s, is_active = %s
        WHERE id = %s
    """
    params = (
        data.get('full_name'),
        data.get('phone'),
        data.get('address'),
        data.get('is_active', True),
        customer_id
    )
    
    return execute_query(query, params)