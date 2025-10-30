-- Tạo database
CREATE DATABASE IF NOT EXISTS furniture_store CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE furniture_store;

-- Bảng danh mục sản phẩm
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng sản phẩm
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    original_price DECIMAL(12, 2),
    image VARCHAR(500),
    description TEXT,
    features TEXT,
    rating DECIMAL(2, 1) DEFAULT 5.0,
    reviews INT DEFAULT 0,
    stock INT DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng admin users
CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng khách hàng
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng đơn hàng
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL UNIQUE,
    customer_id INT NULL,
    customer_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    address TEXT NOT NULL,
    note TEXT,
    payment_method VARCHAR(50) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    shipping_fee DECIMAL(12, 2) DEFAULT 0,
    total DECIMAL(12, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    payment_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    INDEX idx_customer_id (customer_id),
    INDEX idx_order_id (order_id),
    INDEX idx_status (status),
    INDEX idx_payment_status (payment_status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng chi tiết đơn hàng
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    product_id INT NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    quantity INT NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Thêm dữ liệu mẫu cho danh mục
INSERT INTO categories (name, description) VALUES
('Phòng Khách', 'Nội thất phòng khách sang trọng, hiện đại'),
('Phòng Ngủ', 'Nội thất phòng ngủ ấm cúng, tiện nghi'),
('Phòng Ăn', 'Nội thất phòng ăn đẹp mắt, tiện dụng'),
('Văn Phòng', 'Nội thất văn phòng chuyên nghiệp'),
('Nhà Bếp', 'Nội thất nhà bếp hiện đại, tiện lợi');

-- Thêm admin mặc định (username: admin, password: admin123)
-- Mật khẩu được mã hóa bằng bcrypt
INSERT INTO admin_users (username, password, full_name, email) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYNq.4OdFG6', 'Administrator', 'admin@furniture.com');

-- Thêm dữ liệu sản phẩm mẫu
INSERT INTO products (name, category, price, original_price, image, description, features, rating, reviews) VALUES
('Ghế Sofa Hiện Đại', 'Phòng Khách', 15000000, 18000000, 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800', 
 'Ghế sofa cao cấp với chất liệu vải nhung mềm mại, thiết kế hiện đại phù hợp mọi không gian.',
 'Chất liệu vải nhung cao cấp|Khung gỗ chắc chắn|Đệm mút êm ái|Bảo hành 2 năm', 4.8, 124),

('Bàn Làm Việc Gỗ Sồi', 'Văn Phòng', 8500000, 10000000, 'https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=800',
 'Bàn làm việc gỗ sồi tự nhiên, thiết kế tối giản, sang trọng với nhiều ngăn kéo tiện dụng.',
 'Gỗ sồi tự nhiên 100%|Thiết kế tối giản|3 ngăn kéo rộng rãi|Chống trầy xước', 4.9, 89),

('Giường Ngủ Bọc Da', 'Phòng Ngủ', 22000000, 25000000, 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800',
 'Giường ngủ bọc da cao cấp với đầu giường êm ái, mang lại sự thoải mái tối đa.',
 'Da PU cao cấp|Đầu giường có đệm|Kích thước 1.8m x 2m|Bền bỉ theo thời gian', 4.7, 156),

('Tủ Bếp Hiện Đại', 'Nhà Bếp', 35000000, 40000000, 'https://images.unsplash.com/photo-1556912172-45b7abe8b7e1?w=800',
 'Tủ bếp thiết kế hiện đại với chất liệu gỗ công nghiệp cao cấp chống ẩm.',
 'Gỗ công nghiệp chống ẩm|Phụ kiện cao cấp|Thiết kế tối ưu|Lắp đặt miễn phí', 4.9, 78),

('Kệ Sách Gỗ Trang Trí', 'Phòng Khách', 6500000, 8000000, 'https://images.unsplash.com/photo-1594620302200-9a762244a156?w=800',
 'Kệ sách đa năng với thiết kế độc đáo, vừa để sách vừa trang trí không gian.',
 'Gỗ công nghiệp MDF|5 tầng rộng rãi|Thiết kế hiện đại|Dễ lắp đặt', 4.6, 92),

('Ghế Ăn Bọc Vải', 'Phòng Ăn', 2500000, 3000000, 'https://images.unsplash.com/photo-1503602642458-232111445657?w=800',
 'Ghế ăn êm ái với chân gỗ chắc chắn, phù hợp mọi phong cách nội thất.',
 'Vải bọc cao cấp|Chân gỗ bền chắc|Thiết kế ergonomic|Bộ 4 ghế', 4.7, 145),

('Tủ Quần Áo Cửa Lùa', 'Phòng Ngủ', 18000000, 21000000, 'https://images.unsplash.com/photo-1595428774223-ef52624120d2?w=800',
 'Tủ quần áo hiện đại với cửa lùa tiết kiệm không gian, nhiều ngăn chia khoa học.',
 'Cửa lùa êm ái|Gương soi toàn thân|Nhiều ngăn chia|Chống ẩm mốc', 4.8, 67),

('Bàn Ăn 6 Chỗ', 'Phòng Ăn', 12000000, 14000000, 'https://images.unsplash.com/photo-1617806118233-18e1de247200?w=800',
 'Bàn ăn mặt đá sang trọng, chắc chắn dành cho gia đình 6 người.',
 'Mặt đá nhân tạo|Chân inox cao cấp|Kích thước 1.6m x 0.9m|Dễ vệ sinh', 4.9, 103),

('Ghế Sofa Góc L', 'Phòng Khách', 28000000, 32000000, 'https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?w=800',
 'Sofa góc L rộng rãi, sang trọng, phù hợp phòng khách lớn.',
 'Thiết kế góc L|Chất liệu da cao cấp|Chỗ ngồi rộng|Khung gỗ chắc chắn', 4.9, 87),

('Bàn Trà Mặt Kính', 'Phòng Khách', 4500000, 5500000, 'https://images.unsplash.com/photo-1554995207-c18c203602cb?w=800',
 'Bàn trà hiện đại với mặt kính cường lực, chân inox sang trọng.',
 'Kính cường lực 10mm|Chân inox mạ chrome|Dễ vệ sinh|Thiết kế tối giản', 4.6, 95),

('Tủ Giày Thông Minh', 'Phòng Khách', 3200000, 4000000, 'https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=800',
 'Tủ giày đa năng với nhiều ngăn, thiết kế thông minh tiết kiệm không gian.',
 '8-10 đôi giày|Có ghế ngồi|Chống ẩm mốc|Dễ lắp đặt', 4.5, 112),

('Ghế Gaming Pro', 'Văn Phòng', 5800000, 7000000, 'https://images.unsplash.com/photo-1598550476439-6847785fcea6?w=800',
 'Ghế gaming cao cấp với tựa lưng điều chỉnh, gác chân tiện lợi.',
 'Tựa lưng 180 độ|Gác chân co giãn|Đệm memory foam|Trục D5 chịu lực 200kg', 4.8, 143),

('Bàn Học Cho Bé', 'Phòng Ngủ', 3500000, 4200000, 'https://images.unsplash.com/photo-1611269154421-4e27233ac5c7?w=800',
 'Bàn học ergonomic cho trẻ em, điều chỉnh độ cao, bảo vệ cột sống.',
 'Điều chỉnh độ cao|Mặt bàn nghiêng|Chống gù lưng|Màu sắc tươi sáng', 4.7, 128),

('Giường Tầng Gỗ Thông', 'Phòng Ngủ', 12000000, 14500000, 'https://images.unsplash.com/photo-1595428773665-69b0566f97bb?w=800',
 'Giường tầng chắc chắn cho 2 bé, gỗ thông tự nhiên an toàn.',
 'Gỗ thông tự nhiên|Thanh chắn an toàn|Thang leo vững chắc|Sơn water-based', 4.8, 76),

('Tủ Đầu Giường Hiện Đại', 'Phòng Ngủ', 2800000, 3500000, 'https://images.unsplash.com/photo-1540574163026-643ea20ade25?w=800',
 'Tủ đầu giường nhỏ gọn với 2 ngăn kéo, thiết kế sang trọng.',
 '2 ngăn kéo rộng|Ray trượt êm ái|Mặt gỗ veneer|Chống trầy xước', 4.6, 134),

('Ghế Xoay Văn Phòng', 'Văn Phòng', 2200000, 2800000, 'https://images.unsplash.com/photo-1580480055273-228ff5388ef8?w=800',
 'Ghế xoay lưng lưới thoáng mát, phù hợp làm việc lâu dài.',
 'Lưng lưới thoáng|Tay vịn điều chỉnh|Bánh xe êm|Nâng hạ khí nén', 4.5, 167),

('Kệ Tivi Gỗ Tự Nhiên', 'Phòng Khách', 8900000, 10500000, 'https://images.unsplash.com/photo-1591290619762-539b1838ad70?w=800',
 'Kệ tivi gỗ sồi tự nhiên với nhiều ngăn chứa đồ tiện lợi.',
 'Gỗ sồi tự nhiên|Nhiều ngăn chứa|Dài 1.8m|Chịu lực tốt', 4.8, 91),

('Bàn Ăn Thông Minh', 'Phòng Ăn', 15000000, 18000000, 'https://images.unsplash.com/photo-1615066390971-03e4e1c36ddf?w=800',
 'Bàn ăn mở rộng thông minh, từ 4 chỗ thành 8 chỗ.',
 'Mở rộng linh hoạt|Cơ chế trơn tru|Mặt gỗ veneer|Tiết kiệm không gian', 4.9, 121),

('Tủ Rượu Gỗ Tự Nhiên', 'Phòng Khách', 12500000, 15000000, 'https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?w=800',
 'Tủ rượu cao cấp với cửa kính, lưu trữ và trưng bày đẹp mắt.',
 'Gỗ tự nhiên cao cấp|Cửa kính chắc chắn|Nhiều ngăn|Thiết kế sang trọng', 4.7, 54),

('Ghế Thư Giãn Bọc Da', 'Phòng Khách', 9800000, 12000000, 'https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=800',
 'Ghế thư giãn ergonomic, điều chỉnh được góc ngả thoải mái.',
 'Da PU cao cấp|Điều chỉnh góc ngả|Gác chân tích hợp|Khung thép chắc chắn', 4.8, 98);
