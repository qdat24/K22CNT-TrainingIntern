from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime
import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

# Import database helper
from db_helper import *

# Import Web3 Payment
from web3_payment import init_web3_payment

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Initialize Web3 Payment System
init_web3_payment(app)

# Context processor để cung cấp cart_count và site_settings cho tất cả templates
@app.context_processor
def inject_globals():
    cart_count = 0
    if 'cart' in session:
        cart_count = sum(item['quantity'] for item in session['cart'])
    
    # Lấy site settings
    site_settings = get_settings_dict()
    
    return {
        'cart_count': cart_count,
        'site_settings': site_settings
    }

# Custom filter để format currency
@app.template_filter('format_currency')
def format_currency(value):
    """Format number as Vietnamese currency"""
    try:
        return "{:,.0f}".format(float(value))
    except (ValueError, TypeError):
        return value

# Thông tin ngân hàng
BANK_INFO = {
    'bank_code': 'MB',
    'bank_name': 'MBBANK',
    'account_number': '988888865',
    'account_name': 'DINH QUOC DAT'
}

# Email configuration (cấu hình nếu cần gửi email)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'quocdat3007888@gmail.com',
    'sender_password': 'vdrb yfkp qrav lrlt',
    'enabled': True  # Đặt True khi muốn bật gửi email
}

# Decorator để kiểm tra đăng nhập admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Vui lòng đăng nhập để truy cập trang này', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator để kiểm tra đăng nhập khách hàng
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'customer_logged_in' not in session:
            flash('Vui lòng đăng nhập để tiếp tục', 'error')
            return redirect(url_for('customer_login'))
        return f(*args, **kwargs)
    return decorated_function

def send_order_confirmation_email(order):
    """Gửi email xác nhận đơn hàng"""
    if not EMAIL_CONFIG['enabled']:
        return
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = order.get('email', '')
        msg['Subject'] = f"✅ Xác nhận đơn hàng #{order['order_id']} - Nội Thất ABC"
        
        # Tạo bảng sản phẩm HTML
        items_html = ""
        for item in order.get('items', []):
            items_html += f"""
            <tr>
                <td style="padding: 15px; border-bottom: 1px solid #eee;">
                    <strong>{item['name']}</strong>
                </td>
                <td style="padding: 15px; border-bottom: 1px solid #eee; text-align: center;">
                    {item['quantity']}
                </td>
                <td style="padding: 15px; border-bottom: 1px solid #eee; text-align: right;">
                    {item['price']:,.0f}₫
                </td>
                <td style="padding: 15px; border-bottom: 1px solid #eee; text-align: right;">
                    <strong>{item['subtotal']:,.0f}₫</strong>
                </td>
            </tr>
            """
        
        # Tạo HTML email đẹp
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 650px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #27ae60 0%, #229954 100%); 
                          color: white; padding: 40px 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .header .order-id {{ background: rgba(255,255,255,0.2); padding: 10px 20px; 
                                    border-radius: 20px; display: inline-block; margin-top: 15px; 
                                    font-size: 18px; font-weight: bold; }}
                .content {{ background: white; padding: 30px; border: 1px solid #ddd; }}
                .status-box {{ background: #d5f4e6; border-left: 4px solid #27ae60; 
                              padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .info-section {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .info-row {{ margin: 10px 0; }}
                .label {{ color: #666; font-weight: 600; display: inline-block; width: 140px; }}
                .value {{ color: #333; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #f1f3f5; padding: 15px; text-align: left; font-weight: 600; 
                     color: #495057; border-bottom: 2px solid #dee2e6; }}
                .total-section {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .total-row {{ display: flex; justify-content: space-between; padding: 10px 0; }}
                .total-row.grand {{ border-top: 2px solid #27ae60; margin-top: 10px; 
                                   padding-top: 15px; font-size: 18px; font-weight: bold; color: #27ae60; }}
                .payment-method {{ display: inline-block; background: #e3f2fd; color: #1976d2; 
                                  padding: 8px 16px; border-radius: 20px; font-weight: 600; 
                                  margin: 10px 0; }}
                .contact-box {{ background: #fff3cd; padding: 20px; border-radius: 8px; 
                               margin: 20px 0; border-left: 4px solid #ffc107; }}
                .footer {{ background: #2c3e50; color: white; padding: 30px; text-align: center; 
                          border-radius: 0 0 10px 10px; }}
                .footer a {{ color: #3498db; text-decoration: none; }}
                .button {{ display: inline-block; background: #27ae60; color: white; 
                          padding: 12px 30px; text-decoration: none; border-radius: 5px; 
                          margin: 15px 5px; font-weight: bold; }}
                .button-secondary {{ background: #3498db; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ ĐẶT HÀNG THÀNH CÔNG</h1>
                    <div class="order-id">Mã đơn: #{order['order_id']}</div>
                </div>
                
                <div class="content">
                    <div class="status-box">
                        <p style="margin: 0; font-size: 16px;">
                            <strong>🎉 Cảm ơn bạn đã đặt hàng tại Nội Thất ABC!</strong>
                        </p>
                        <p style="margin: 10px 0 0 0;">
                            Chúng tôi đã nhận được đơn hàng của bạn và đang xử lý. 
                            Nhân viên sẽ liên hệ với bạn sớm nhất để xác nhận.
                        </p>
                    </div>

                    <h3 style="color: #2c3e50; border-bottom: 2px solid #27ae60; padding-bottom: 10px;">
                        📦 Chi Tiết Đơn Hàng
                    </h3>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>Sản phẩm</th>
                                <th style="text-align: center; width: 80px;">Số lượng</th>
                                <th style="text-align: right; width: 120px;">Đơn giá</th>
                                <th style="text-align: right; width: 120px;">Thành tiền</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>

                    <div class="total-section">
                        <div class="total-row">
                            <span>Tạm tính:</span>
                            <span>{order['subtotal']:,.0f}₫</span>
                        </div>
                        <div class="total-row">
                            <span>Phí vận chuyển:</span>
                            <span>{order['shipping_fee']:,.0f}₫</span>
                        </div>
                        <div class="total-row grand">
                            <span>Tổng cộng:</span>
                            <span>{order['total']:,.0f}₫</span>
                        </div>
                    </div>

                    <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                        📋 Thông Tin Giao Hàng
                    </h3>
                    
                    <div class="info-section">
                        <div class="info-row">
                            <span class="label">👤 Người nhận:</span>
                            <span class="value">{order['customer_name']}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">📱 Số điện thoại:</span>
                            <span class="value">{order['phone']}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">📧 Email:</span>
                            <span class="value">{order.get('email', 'Không có')}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">🏠 Địa chỉ:</span>
                            <span class="value">{order['address']}</span>
                        </div>
                        {f'<div class="info-row"><span class="label">📝 Ghi chú:</span><span class="value">{order["note"]}</span></div>' if order.get('note') else ''}
                    </div>

                    <div class="info-row" style="margin: 20px 0;">
                        <span class="label">💳 Thanh toán:</span>
                        <span class="payment-method">
                            {'💵 Thanh toán khi nhận hàng (COD)' if order['payment_method'] == 'cod' 
                             else '🏦 Chuyển khoản ngân hàng' if order['payment_method'] == 'bank_transfer'
                             else '💳 USDT Crypto' if order['payment_method'] == 'usdt'
                             else '💳 Thẻ tín dụng/ghi nợ'}
                        </span>
                    </div>

                    <div class="contact-box">
                        <p style="margin: 0 0 10px 0; font-weight: bold;">
                            ⚠️ Cần hỗ trợ hoặc thay đổi đơn hàng?
                        </p>
                        <p style="margin: 0;">
                            Vui lòng liên hệ: <strong>0357100129</strong> hoặc 
                            email <strong>quocdat30075@gmail.com</strong>
                        </p>
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:5000/account" class="button">
                            Xem Chi Tiết Đơn Hàng
                        </a>
                        <a href="http://localhost:5000/products" class="button button-secondary">
                            Tiếp Tục Mua Sắm
                        </a>
                    </div>
                </div>

                <div class="footer">
                    <h3 style="margin: 0 0 15px 0;">🛋️ Nội Thất ABC</h3>
                    <p style="margin: 5px 0;">Thiết Kế Không Gian Sống Của Bạn</p>
                    <p style="margin: 15px 0 5px 0;">
                        📞 Hotline: <strong>0357100129</strong> | 
                        📧 Email: <strong>quocdat30075@gmail.com</strong>
                    </p>
                    <p style="margin: 5px 0;">🏠 Địa chỉ: Hà Đông, Hà Nội</p>
                    <p style="margin: 20px 0 0 0; font-size: 12px; opacity: 0.8;">
                        Email này được gửi tự động, vui lòng không trả lời trực tiếp email này.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Đã gửi email xác nhận đơn hàng đến {order.get('email', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Lỗi gửi email xác nhận đơn hàng: {e}")

# ==================== CONTACT EMAIL FUNCTIONS ====================

def send_contact_email(contact_data):
    """Gửi email thông báo có liên hệ mới đến admin"""
    if not EMAIL_CONFIG['enabled']:
        return False
    
    try:
        # Email gửi đến admin
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['sender_email']  # Gửi đến chính mình
        msg['Subject'] = f"🔔 Liên hệ mới: {contact_data['subject']}"
        
        # HTML email đẹp cho admin
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
                .info-row {{ margin: 15px 0; padding: 15px; background: white; border-radius: 5px; }}
                .label {{ font-weight: bold; color: #667eea; display: inline-block; width: 120px; }}
                .value {{ color: #333; }}
                .message-box {{ background: white; padding: 20px; border-left: 4px solid #667eea; 
                               margin: 20px 0; border-radius: 5px; }}
                .footer {{ text-align: center; padding: 20px; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📬 Liên Hệ Mới Từ Website</h1>
                </div>
                <div class="content">
                    <div class="info-row">
                        <span class="label">👤 Họ tên:</span>
                        <span class="value">{contact_data['name']}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">📧 Email:</span>
                        <span class="value">{contact_data['email']}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">📱 Điện thoại:</span>
                        <span class="value">{contact_data.get('phone', 'Không có')}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">📌 Chủ đề:</span>
                        <span class="value">{contact_data['subject']}</span>
                    </div>
                    <div class="message-box">
                        <p style="margin: 0 0 10px 0; font-weight: bold; color: #667eea;">💬 Nội dung tin nhắn:</p>
                        <p style="margin: 0; white-space: pre-wrap;">{contact_data['message']}</p>
                    </div>
                    <p style="text-align: center; margin-top: 30px;">
                        <a href="http://localhost:5000/admin/contacts" 
                           style="background: #667eea; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Xem trong Admin Panel
                        </a>
                    </p>
                </div>
                <div class="footer">
                    <p>Email tự động từ hệ thống Nội Thất ABC</p>
                    <p>Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Gửi email
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Lỗi gửi email thông báo: {e}")
        return False

def send_contact_reply_email(contact_data):
    """Gửi email tự động trả lời khách hàng"""
    if not EMAIL_CONFIG['enabled']:
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = contact_data['email']
        msg['Subject'] = f"Cảm ơn bạn đã liên hệ - {contact_data['subject']}"
        
        # HTML email đẹp cho khách hàng
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); 
                          color: white; padding: 40px; text-align: center; border-radius: 10px 10px 0 0; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .content {{ background: white; padding: 40px; border: 1px solid #ddd; }}
                .highlight {{ background: #f0f8ff; padding: 20px; border-radius: 5px; 
                             border-left: 4px solid #3498db; margin: 20px 0; }}
                .button {{ display: inline-block; background: #3498db; color: white; 
                          padding: 15px 40px; text-decoration: none; border-radius: 5px; 
                          margin: 20px 0; font-weight: bold; }}
                .footer {{ background: #f9f9f9; padding: 30px; text-align: center; 
                          border-top: 3px solid #3498db; }}
                .contact-info {{ margin: 20px 0; padding: 20px; background: #f9f9f9; 
                                border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛋️ Nội Thất ABC</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">Cảm ơn bạn đã liên hệ với chúng tôi!</p>
                </div>
                <div class="content">
                    <p>Xin chào <strong>{contact_data['name']}</strong>,</p>
                    
                    <p>Chúng tôi đã nhận được tin nhắn của bạn với nội dung:</p>
                    
                    <div class="highlight">
                        <p style="margin: 0 0 10px 0;"><strong>📌 Chủ đề:</strong> {contact_data['subject']}</p>
                        <p style="margin: 0;"><strong>💬 Nội dung:</strong></p>
                        <p style="margin: 10px 0 0 0; white-space: pre-wrap;">{contact_data['message']}</p>
                    </div>
                    
                    <p>Đội ngũ chúng tôi sẽ xem xét và phản hồi bạn trong vòng <strong>24 giờ làm việc</strong>.</p>
                    
                    <p style="text-align: center;">
                        <a href="http://localhost:5000" class="button">Ghé Thăm Website</a>
                    </p>
                    
                    <div class="contact-info">
                        <p style="margin: 0 0 10px 0; font-weight: bold; color: #2c3e50;">
                            📞 Thông Tin Liên Hệ
                        </p>
                        <p style="margin: 5px 0;">📱 Hotline: 0357100129</p>
                        <p style="margin: 5px 0;">📧 Email: quocdat30075@gmail.com</p>
                        <p style="margin: 5px 0;">🏠 Địa chỉ: Hà Đông Hà Nội</p>
                    </div>
                    
                    <p>Nếu bạn cần hỗ trợ gấp, vui lòng gọi trực tiếp hotline của chúng tôi.</p>
                    
                    <p style="margin-top: 30px;">Trân trọng,<br>
                    <strong>Đội ngũ Nội Thất ABC</strong></p>
                </div>
                <div class="footer">
                    <p style="margin: 0 0 10px 0; color: #666;">
                        🛋️ Nội Thất ABC - Thiết Kế Không Gian Sống Của Bạn
                    </p>
                    <p style="margin: 5px 0; font-size: 12px; color: #999;">
                        Email này được gửi tự động, vui lòng không trả lời email này.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Gửi email
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Lỗi gửi email trả lời: {e}")
        return False

# ==================== PUBLIC ROUTES ====================

@app.route('/')
def index():
    """Trang chủ"""
    products = get_all_products()
    categories = get_category_names()
    
    # Lấy sản phẩm featured (8 sản phẩm đầu)
    featured_products = products[:8] if products else []
    
    return render_template('index.html', 
                         featured_products=featured_products,
                         categories=categories)

@app.route('/products')
def products():
    """Trang danh sách sản phẩm"""
    category = request.args.get('category')
    products_list = get_all_products(category=category)
    categories = get_category_names()
    
    return render_template('products.html',
                         products=products_list,
                         categories=categories,
                         selected_category=category)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Trang chi tiết sản phẩm"""
    product = get_product_by_id(product_id)
    
    if not product:
        return "Không tìm thấy sản phẩm", 404
    
    # Lấy sản phẩm liên quan (cùng category)
    related_products = get_all_products(category=product['category'])
    # Loại bỏ sản phẩm hiện tại và lấy 4 sản phẩm
    related_products = [p for p in related_products if p['id'] != product_id][:4]
    
    return render_template('product_detail.html',
                         product=product,
                         related_products=related_products)

@app.route('/api/add-to-cart', methods=['POST'])
def add_to_cart():
    """Thêm sản phẩm vào giỏ hàng"""
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    # Kiểm tra sản phẩm tồn tại
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Sản phẩm không tồn tại'})
    
    # Khởi tạo giỏ hàng nếu chưa có
    if 'cart' not in session:
        session['cart'] = []
    
    cart = session['cart']
    
    # Kiểm tra sản phẩm đã có trong giỏ chưa
    found = False
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            found = True
            break
    
    if not found:
        cart.append({
            'product_id': product_id,
            'quantity': quantity
        })
    
    session['cart'] = cart
    session.modified = True
    
    return jsonify({
        'success': True, 
        'message': 'Đã thêm vào giỏ hàng',
        'cart_count': sum(item['quantity'] for item in cart)
    })

@app.route('/api/update-cart', methods=['POST'])
def update_cart():
    """Cập nhật số lượng sản phẩm trong giỏ"""
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if 'cart' not in session:
        return jsonify({'success': False})
    
    cart = session['cart']
    
    for item in cart:
        if item['product_id'] == product_id:
            if quantity <= 0:
                cart.remove(item)
            else:
                item['quantity'] = quantity
            break
    
    session['cart'] = cart
    session.modified = True
    
    return jsonify({'success': True})

@app.route('/api/remove-from-cart', methods=['POST'])
def remove_from_cart():
    """Xóa sản phẩm khỏi giỏ hàng"""
    data = request.json
    product_id = data.get('product_id')
    
    if 'cart' not in session:
        return jsonify({'success': False})
    
    cart = session['cart']
    cart = [item for item in cart if item['product_id'] != product_id]
    
    session['cart'] = cart
    session.modified = True
    
    return jsonify({'success': True})

@app.route('/cart')
def cart():
    """Trang giỏ hàng"""
    # DEBUG
    print("\n" + "="*60)
    print("🛒 DEBUG TRANG GIỎ HÀNG")
    print("="*60)
    
    cart_items = []
    total = 0
    
    # Kiểm tra session cart
    print(f"📦 Session có 'cart': {'cart' in session}")
    
    if 'cart' in session:
        print(f"📦 Số items trong session['cart']: {len(session['cart'])}")
        print(f"📦 Nội dung session['cart']: {session['cart']}")
        
        for idx, item in enumerate(session['cart']):
            print(f"\n   Item {idx + 1}:")
            print(f"   - product_id: {item.get('product_id')}")
            print(f"   - quantity: {item.get('quantity')}")
            
            product = get_product_by_id(item['product_id'])
            
            if product:
                print(f"   - product found: {product['name']}")
                subtotal = product['price'] * item['quantity']
                cart_items.append({
                    'product': product,
                    'quantity': item['quantity'],
                    'subtotal': subtotal
                })
                total += subtotal
            else:
                print(f"   - ❌ Sản phẩm ID {item['product_id']} KHÔNG TÌM THẤY!")
    else:
        print("❌ Session KHÔNG có 'cart'")
    
    print(f"\n📊 Tổng số cart_items để render: {len(cart_items)}")
    print(f"💰 Tổng tiền: {total}")
    print("="*60 + "\n")
    
    shipping_fee = 0 if total >= 5000000 else 200000
    
    return render_template('cart.html',
                         cart_items=cart_items,
                         subtotal=total,
                         shipping_fee=shipping_fee,
                         total=total + shipping_fee)

@app.route('/checkout')
def checkout():
    """Trang thanh toán"""
    # Kiểm tra giỏ hàng có sản phẩm không
    if 'cart' not in session or not session['cart']:
        flash('Giỏ hàng của bạn đang trống', 'warning')
        return redirect(url_for('cart'))
    
    # Tính toán giỏ hàng
    cart_items = []
    total = 0
    
    for item in session['cart']:
        product = get_product_by_id(item['product_id'])
        if product:
            subtotal = product['price'] * item['quantity']
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'subtotal': subtotal
            })
            total += subtotal
    
    # Kiểm tra lại nếu không có sản phẩm hợp lệ
    if not cart_items:
        flash('Giỏ hàng của bạn đang trống', 'warning')
        return redirect(url_for('cart'))
    
    shipping_fee = 0 if total >= 5000000 else 200000
    
    # Lấy thông tin khách hàng nếu đã đăng nhập
    customer = None
    if 'customer_logged_in' in session:
        customer = get_customer_by_id(session['customer_id'])
    
    # Lưu tổng tiền vào session cho Web3 payment
    session['cart_total'] = total + shipping_fee
    session['pending_order_id'] = None  # Sẽ set sau khi tạo order
    
    return render_template('checkout.html',
                         cart_items=cart_items,
                         subtotal=total,
                         shipping_fee=shipping_fee,
                         total=total + shipping_fee,
                         customer=customer)

@app.route('/api/place-order', methods=['POST'])
def place_order():
    """Đặt hàng"""
    data = request.json
    
    if 'cart' not in session or not session['cart']:
        return jsonify({'success': False, 'message': 'Giỏ hàng trống'})
    
    # Tính tổng tiền và chuẩn bị order items
    order_items = []
    total = 0
    
    for item in session['cart']:
        product = get_product_by_id(item['product_id'])
        if product:
            subtotal = product['price'] * item['quantity']
            total += subtotal
            order_items.append({
                'product_id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'quantity': item['quantity'],
                'subtotal': subtotal
            })
    
    # Thêm phí vận chuyển
    shipping_fee = 0 if total >= 5000000 else 200000
    subtotal = total
    total += shipping_fee
    
    # Tạo mã đơn hàng
    order_id = 'ORD' + ''.join(random.choices(string.digits, k=8))
    
    # Chuẩn bị dữ liệu đơn hàng
    order_data = {
        'order_id': order_id,
        'customer_id': session.get('customer_id'),  # Thêm customer_id nếu đã đăng nhập
        'customer_name': data.get('fullname'),
        'phone': data.get('phone'),
        'email': data.get('email'),
        'address': f"{data.get('address')}, {data.get('ward')}, {data.get('district')}, {data.get('city')}",
        'note': data.get('note', ''),
        'payment_method': data.get('payment_method'),
        'items': order_items,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'total': total,
        'status': 'pending',
        'payment_status': 'pending'
    }
    
    # Lưu vào database
    result = create_order(order_data)
    
    if not result:
        return jsonify({'success': False, 'message': 'Không thể tạo đơn hàng'})
    
    # Lưu order_id vào session cho Web3 payment
    session['pending_order_id'] = order_id
    
    # Xóa giỏ hàng
    session['cart'] = []
    
    # Chuyển hướng dựa trên phương thức thanh toán
    payment_method = data.get('payment_method')
    
    if payment_method == 'usdt':
        # USDT Web3 Payment
        return jsonify({
            'success': True, 
            'order_id': order_id,
            'redirect': 'usdt_payment'
        })
    elif payment_method == 'bank_transfer':
        return jsonify({
            'success': True, 
            'order_id': order_id,
            'redirect': 'bank_transfer'
        })
    elif payment_method == 'credit_card':
        return jsonify({
            'success': True, 
            'order_id': order_id,
            'redirect': 'credit_card'
        })
    else:
        # COD
        try:
            send_order_confirmation_email(order_data)
        except Exception as e:
            print(f"Không thể gửi email: {str(e)}")
        
        return jsonify({
            'success': True, 
            'order_id': order_id,
            'redirect': 'order_success'
        })

@app.route('/order-success')
def order_success():
    """Trang thành công"""
    order_id = request.args.get('order_id')
    
    if not order_id:
        return redirect('/')
    
    order = get_order_by_id(order_id)
    
    if not order:
        return "Không tìm thấy đơn hàng", 404
    
    return render_template('order_success.html', order_id=order_id, order=order)

@app.route('/bank-transfer/<order_id>')
def bank_transfer(order_id):
    """Trang chuyển khoản"""
    order = get_order_by_id(order_id)
    
    if not order:
        return "Không tìm thấy đơn hàng", 404
    
    return render_template('bank_transfer.html', 
                         order_id=order_id,
                         order=order,
                         total=order['total'],
                         bank_code=BANK_INFO['bank_code'],
                         bank_name=BANK_INFO['bank_name'],
                         account_number=BANK_INFO['account_number'],
                         account_name=BANK_INFO['account_name'])

@app.route('/credit-card/<order_id>')
def credit_card(order_id):
    """Trang thanh toán thẻ"""
    order = get_order_by_id(order_id)
    
    if not order:
        return "Không tìm thấy đơn hàng", 404
    
    return render_template('credit_card.html',
                         order_id=order_id,
                         order=order,
                         total=order['total'])

@app.route('/api/process-card-payment', methods=['POST'])
def process_card_payment():
    """Xử lý thanh toán thẻ"""
    data = request.json
    order_id = data.get('order_id')
    
    order = get_order_by_id(order_id)
    
    if not order:
        return jsonify({
            'success': False,
            'message': 'Không tìm thấy đơn hàng'
        })
    
    # Cập nhật trạng thái
    update_order_status(order_id, 'confirmed', 'paid')
    
    # Gửi email
    try:
        send_order_confirmation_email(order)
    except Exception as e:
        print(f"Không thể gửi email: {str(e)}")
    
    return jsonify({
        'success': True,
        'message': 'Thanh toán thành công',
        'transaction_id': 'TXN' + ''.join(random.choices(string.digits, k=12))
    })

# Các trang thông tin
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/policy')
def policy():
    return render_template('policy.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Trang liên hệ"""
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        contact_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone', ''),
            'subject': request.form.get('subject'),
            'message': request.form.get('message')
        }
        
        # Validate
        if not all([contact_data['name'], contact_data['email'], 
                   contact_data['subject'], contact_data['message']]):
            flash('Vui lòng điền đầy đủ thông tin bắt buộc', 'error')
            return render_template('contact.html')
        
        # Lưu vào database
        if create_contact(contact_data):
            # Gửi email thông báo cho admin
            send_contact_email(contact_data)
            
            # Gửi email trả lời tự động cho khách hàng
            send_contact_reply_email(contact_data)
            
            flash('Cảm ơn bạn đã liên hệ! Chúng tôi sẽ phản hồi trong 24h.', 'success')
            return redirect(url_for('contact'))
        else:
            flash('Có lỗi xảy ra, vui lòng thử lại sau', 'error')
    
    return render_template('contact.html')

@app.route('/guide')
def guide():
    return render_template('guide.html')

@app.route('/return-policy')
def return_policy():
    return render_template('return_policy.html')

@app.route('/warranty')
def warranty():
    return render_template('warranty.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

# ==================== CUSTOMER AUTH ROUTES ====================

@app.route('/register', methods=['GET', 'POST'])
def customer_register():
    """Đăng ký tài khoản khách hàng"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # Validate
        if not all([email, password, full_name]):
            flash('Vui lòng điền đầy đủ thông tin bắt buộc', 'error')
            return render_template('customer/register.html')
        
        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp', 'error')
            return render_template('customer/register.html')
        
        if len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự', 'error')
            return render_template('customer/register.html')
        
        # Kiểm tra email đã tồn tại
        if get_customer_by_email(email):
            flash('Email này đã được đăng ký', 'error')
            return render_template('customer/register.html')
        
        # Tạo tài khoản
        result = create_customer(email, password, full_name, phone, address)
        
        if result:
            flash('Đăng ký thành công! Vui lòng đăng nhập', 'success')
            return redirect(url_for('customer_login'))
        else:
            flash('Đã có lỗi xảy ra, vui lòng thử lại', 'error')
    
    return render_template('customer/register.html')

@app.route('/login', methods=['GET', 'POST'])
def customer_login():
    """Đăng nhập khách hàng"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        customer = verify_customer(email, password)
        
        if customer:
            session['customer_logged_in'] = True
            session['customer_id'] = customer['id']
            session['customer_email'] = customer['email']
            session['customer_name'] = customer['full_name']
            flash('Đăng nhập thành công!', 'success')
            
            # Redirect về trang trước đó hoặc trang chủ
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Email hoặc mật khẩu không đúng', 'error')
    
    return render_template('customer/login.html')

@app.route('/logout')
def customer_logout():
    """Đăng xuất khách hàng"""
    session.pop('customer_logged_in', None)
    session.pop('customer_id', None)
    session.pop('customer_email', None)
    session.pop('customer_name', None)
    flash('Đã đăng xuất', 'info')
    return redirect(url_for('index'))

@app.route('/account')
@login_required
def customer_account():
    """Trang tài khoản khách hàng"""
    customer = get_customer_by_id(session['customer_id'])
    
    # Lấy đơn hàng của khách hàng
    query = "SELECT * FROM orders WHERE customer_id = %s ORDER BY created_at DESC"
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (session['customer_id'],))
        orders = cursor.fetchall()
        cursor.close()
        connection.close()
    else:
        orders = []
    
    return render_template('customer/account.html', customer=customer, orders=orders)

@app.route('/account/update', methods=['POST'])
@login_required
def update_customer_info():
    """Cập nhật thông tin khách hàng"""
    data = {
        'full_name': request.form.get('full_name'),
        'phone': request.form.get('phone'),
        'address': request.form.get('address')
    }
    
    result = update_customer(session['customer_id'], data)
    
    if result:
        session['customer_name'] = data['full_name']
        flash('Cập nhật thông tin thành công!', 'success')
    else:
        flash('Đã có lỗi xảy ra', 'error')
    
    return redirect(url_for('customer_account'))

@app.route('/account/change-password', methods=['POST'])
@login_required
def change_customer_password():
    """Đổi mật khẩu khách hàng"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validate
    customer = get_customer_by_id(session['customer_id'])
    
    if not verify_customer(customer['email'], current_password):
        flash('Mật khẩu hiện tại không đúng', 'error')
        return redirect(url_for('customer_account'))
    
    if new_password != confirm_password:
        flash('Mật khẩu mới không khớp', 'error')
        return redirect(url_for('customer_account'))
    
    if len(new_password) < 6:
        flash('Mật khẩu phải có ít nhất 6 ký tự', 'error')
        return redirect(url_for('customer_account'))
    
    result = update_customer_password(session['customer_id'], new_password)
    
    if result:
        flash('Đổi mật khẩu thành công!', 'success')
    else:
        flash('Đã có lỗi xảy ra', 'error')
    
    return redirect(url_for('customer_account'))

@app.route('/order/<order_id>')
@login_required
def customer_order_detail(order_id):
    """Trang chi tiết đơn hàng của khách hàng"""
    order = get_order_by_id(order_id)
    
    if not order:
        flash('Không tìm thấy đơn hàng', 'error')
        return redirect(url_for('customer_account'))
    
    # Kiểm tra quyền xem đơn hàng (chỉ chủ đơn hàng mới xem được)
    if order.get('customer_id') != session.get('customer_id'):
        flash('Bạn không có quyền xem đơn hàng này', 'error')
        return redirect(url_for('customer_account'))
    
    return render_template('customer/order_detail.html', order=order)

@app.route('/order/<order_id>/cancel', methods=['POST'])
@login_required
def customer_cancel_order(order_id):
    """Hủy đơn hàng"""
    order = get_order_by_id(order_id)
    
    if not order:
        flash('Không tìm thấy đơn hàng', 'error')
        return redirect(url_for('customer_account'))
    
    # Kiểm tra quyền (chỉ chủ đơn hàng mới hủy được)
    if order.get('customer_id') != session.get('customer_id'):
        flash('Bạn không có quyền hủy đơn hàng này', 'error')
        return redirect(url_for('customer_account'))
    
    # Chỉ cho phép hủy đơn hàng ở trạng thái pending
    if order['status'] != 'pending':
        flash('Chỉ có thể hủy đơn hàng đang chờ xử lý', 'error')
        return redirect(url_for('customer_order_detail', order_id=order_id))
    
    # Cập nhật trạng thái
    result = update_order_status(order_id, 'cancelled', order['payment_status'])
    
    if result:
        flash('Đã hủy đơn hàng thành công', 'success')
    else:
        flash('Có lỗi xảy ra khi hủy đơn hàng', 'error')
    
    return redirect(url_for('customer_account'))

# ==================== ADMIN ROUTES ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Trang đăng nhập admin"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = verify_admin(username, password)
        
        if admin:
            session['admin_logged_in'] = True
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            session['admin_name'] = admin['full_name']
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Đăng xuất admin"""
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    session.pop('admin_name', None)
    flash('Đã đăng xuất', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Trang dashboard admin"""
    stats = {
        'total_products': count_products(),
        'total_orders': count_orders(),
        'revenue': get_revenue_stats()
    }
    
    recent_orders = get_all_orders(limit=10)
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_orders=recent_orders)

@app.route('/admin/products')
@admin_required
def admin_products():
    """Danh sách sản phẩm admin"""
    products_list = get_all_products(active_only=False)
    categories = get_category_names()
    
    return render_template('admin/products.html',
                         products=products_list,
                         categories=categories)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    """Thêm sản phẩm mới"""
    if request.method == 'POST':
        # Lấy features từ form (mỗi feature trên 1 dòng)
        features_text = request.form.get('features', '')
        features = [f.strip() for f in features_text.split('\n') if f.strip()]
        
        product_data = {
            'name': request.form.get('name'),
            'category': request.form.get('category'),
            'price': float(request.form.get('price')),
            'original_price': float(request.form.get('original_price')),
            'image': request.form.get('image'),
            'description': request.form.get('description'),
            'features': features,
            'rating': float(request.form.get('rating', 5.0)),
            'reviews': int(request.form.get('reviews', 0)),
            'stock': int(request.form.get('stock', 100))
        }
        
        result = create_product(product_data)
        
        if result:
            flash('Thêm sản phẩm thành công!', 'success')
            return redirect(url_for('admin_products'))
        else:
            flash('Lỗi khi thêm sản phẩm', 'error')
    
    categories = get_category_names()
    return render_template('admin/product_form.html', 
                         product=None,
                         categories=categories,
                         action='add')

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    """Sửa sản phẩm"""
    product = get_product_by_id(product_id)
    
    if not product:
        flash('Không tìm thấy sản phẩm', 'error')
        return redirect(url_for('admin_products'))
    
    if request.method == 'POST':
        # Lấy features từ form
        features_text = request.form.get('features', '')
        features = [f.strip() for f in features_text.split('\n') if f.strip()]
        
        product_data = {
            'name': request.form.get('name'),
            'category': request.form.get('category'),
            'price': float(request.form.get('price')),
            'original_price': float(request.form.get('original_price')),
            'image': request.form.get('image'),
            'description': request.form.get('description'),
            'features': features,
            'rating': float(request.form.get('rating', 5.0)),
            'reviews': int(request.form.get('reviews', 0)),
            'stock': int(request.form.get('stock', 100)),
            'is_active': request.form.get('is_active') == 'on'
        }
        
        result = update_product(product_id, product_data)
        
        if result:
            flash('Cập nhật sản phẩm thành công!', 'success')
            return redirect(url_for('admin_products'))
        else:
            flash('Lỗi khi cập nhật sản phẩm', 'error')
    
    categories = get_category_names()
    return render_template('admin/product_form.html',
                         product=product,
                         categories=categories,
                         action='edit')

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    """Xóa sản phẩm (soft delete)"""
    result = delete_product(product_id)
    
    if result:
        flash('Xóa sản phẩm thành công!', 'success')
    else:
        flash('Lỗi khi xóa sản phẩm', 'error')
    
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    """Danh sách đơn hàng"""
    orders = get_all_orders()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/<order_id>')
@admin_required
def admin_order_detail(order_id):
    """Chi tiết đơn hàng"""
    order = get_order_by_id(order_id)
    
    if not order:
        flash('Không tìm thấy đơn hàng', 'error')
        return redirect(url_for('admin_orders'))
    
    return render_template('admin/order_detail.html', order=order)

@app.route('/admin/orders/<order_id>/update-status', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    """Cập nhật trạng thái đơn hàng"""
    status = request.form.get('status')
    payment_status = request.form.get('payment_status')
    
    result = update_order_status(order_id, status, payment_status)
    
    if result:
        flash('Cập nhật trạng thái thành công!', 'success')
    else:
        flash('Lỗi khi cập nhật trạng thái', 'error')
    
    return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    """Quản lý cài đặt website (logo, banner, thông tin liên hệ)"""
    if request.method == 'POST':
        # Lấy tất cả các cài đặt từ form
        settings_to_update = {}
        
        # Các setting keys cần cập nhật
        setting_keys = [
            'site_logo', 'site_name',
            'hero_banner_image', 'hero_banner_title', 'hero_banner_subtitle',
            'hero_banner_button_text', 'hero_banner_button_link',
            'contact_phone', 'contact_email', 'contact_address'
        ]
        
        for key in setting_keys:
            value = request.form.get(key, '')
            if value:  # Chỉ cập nhật nếu có giá trị
                settings_to_update[key] = value
        
        # Cập nhật tất cả settings
        if update_multiple_settings(settings_to_update):
            flash('Cập nhật cài đặt thành công!', 'success')
        else:
            flash('Có lỗi xảy ra khi cập nhật cài đặt', 'error')
        
        return redirect(url_for('admin_settings'))
    
    # GET request - hiển thị form
    settings = get_all_settings()
    settings_dict = {s['setting_key']: s for s in settings} if settings else {}
    
    return render_template('admin/settings.html', settings=settings_dict)

# ============================================
# ROUTES QUẢN LÝ KHÁCH HÀNG (CUSTOMERS)
# ============================================

@app.route('/admin/customers')
@admin_required
def admin_customers():
    """Danh sách khách hàng"""
    # Lấy tham số từ URL
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    # Phân trang
    per_page = 20
    offset = (page - 1) * per_page
    
    # Lấy danh sách khách hàng
    customers = get_all_customers(
        search=search if search else None,
        status_filter=status_filter if status_filter else None,
        limit=per_page,
        offset=offset
    )
    
    # Đếm tổng số khách hàng
    total_customers = count_customers(
        search=search if search else None,
        status_filter=status_filter if status_filter else None
    )
    
    # Tính tổng số trang
    total_pages = (total_customers + per_page - 1) // per_page
    
    # Lấy thống kê
    stats = get_customer_stats()
    
    return render_template('admin/customers.html',
                         customers=customers,
                         stats=stats,
                         page=page,
                         total_pages=total_pages,
                         total_customers=total_customers,
                         search=search,
                         status_filter=status_filter)

@app.route('/admin/customers/<int:customer_id>')
@admin_required
def admin_customer_detail(customer_id):
    """Chi tiết khách hàng"""
    customer = get_customer_by_id(customer_id)
    
    if not customer:
        flash('Không tìm thấy khách hàng', 'error')
        return redirect(url_for('admin_customers'))
    
    # Lấy đơn hàng của khách hàng
    orders_query = "SELECT * FROM orders WHERE customer_id = %s ORDER BY created_at DESC"
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(orders_query, (customer_id,))
            customer_orders = cursor.fetchall()
        except:
            customer_orders = []
        finally:
            cursor.close()
            connection.close()
    else:
        customer_orders = []
    
    return render_template('admin/customer_detail.html',
                         customer=customer,
                         orders=customer_orders)

@app.route('/admin/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_customer(customer_id):
    """Chỉnh sửa thông tin khách hàng"""
    customer = get_customer_by_id(customer_id)
    
    if not customer:
        flash('Không tìm thấy khách hàng', 'error')
        return redirect(url_for('admin_customers'))
    
    if request.method == 'POST':
        data = {
            'full_name': request.form.get('full_name'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address'),
            'is_active': request.form.get('is_active') == 'true'
        }
        
        result = update_customer_by_admin(customer_id, data)
        
        if result:
            flash('Cập nhật thông tin khách hàng thành công!', 'success')
            return redirect(url_for('admin_customer_detail', customer_id=customer_id))
        else:
            flash('Lỗi khi cập nhật thông tin khách hàng', 'error')
    
    return render_template('admin/customer_edit.html', customer=customer)

@app.route('/admin/customers/<int:customer_id>/toggle-status', methods=['POST'])
@admin_required
def admin_toggle_customer_status(customer_id):
    """Kích hoạt/Vô hiệu hóa khách hàng"""
    result = toggle_customer_status(customer_id)
    
    if result:
        flash('Đã cập nhật trạng thái khách hàng', 'success')
    else:
        flash('Lỗi khi cập nhật trạng thái', 'error')
    
    return redirect(url_for('admin_customers'))

@app.route('/admin/customers/<int:customer_id>/delete', methods=['POST'])
@admin_required
def admin_delete_customer(customer_id):
    """Xóa khách hàng"""
    customer = get_customer_by_id(customer_id)
    
    if not customer:
        flash('Không tìm thấy khách hàng', 'error')
        return redirect(url_for('admin_customers'))
    
    result = delete_customer(customer_id)
    
    if result:
        flash(f'Đã xóa khách hàng {customer["full_name"]}', 'success')
    else:
        flash('Lỗi khi xóa khách hàng', 'error')
    
    return redirect(url_for('admin_customers'))

@app.route('/usdt-payment')
@app.route('/usdt-payment')
def usdt_payment():
    temp_id = request.args.get('temp_id', '')
    amount = request.args.get('amount', 0)
    name = request.args.get('name', '')
    email = request.args.get('email', '')
    phone = request.args.get('phone', '')
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        amount = 0
    
    usdt_rate = 25000
    usdt_amount = round(amount / usdt_rate, 2)
    
    recipient_address = '0x3fd86c3728b38cb6b09fa7d4914888dcfef1518c'  # ⚠️ ĐỔI ĐỊA CHỈ VÍ
    
    print(f"\n💰 USDT Payment Page Loaded:")
    print(f"   Order: {temp_id}")
    print(f"   Amount: {amount:,.0f} VND")
    print(f"   USDT: {usdt_amount}\n")
    
    return render_template('customer/usdt-payment.html',
                         temp_id=temp_id,
                         amount=amount,
                         usdt_amount=usdt_amount,
                         usdt_rate=usdt_rate,
                         recipient_address=recipient_address,
                         name=name,
                         email=email,
                         phone=phone)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)