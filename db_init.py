import mysql.connector
import uuid
import bcrypt
from config import DB_CONFIG

# 连接MySQL数据库
def get_db_connection():
    # 先连接到MySQL服务器，不指定数据库
    config = DB_CONFIG.copy()
    del config['database']
    conn = mysql.connector.connect(**config)
    
    # 创建数据库（如果不存在）
    c = conn.cursor()
    c.execute('CREATE DATABASE IF NOT EXISTS training_system')
    conn.database = 'training_system'
    
    return conn

# 初始化数据库
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # 创建用户表
    c.execute('CREATE TABLE IF NOT EXISTS users (id VARCHAR(36) PRIMARY KEY, username VARCHAR(255) NOT NULL, email VARCHAR(255) UNIQUE NOT NULL, password VARCHAR(255) NOT NULL, phone VARCHAR(20) NOT NULL, organization VARCHAR(255) NOT NULL, address VARCHAR(255) NOT NULL, is_admin INT DEFAULT 0, wechat_unionid VARCHAR(255) UNIQUE, wechat_openid VARCHAR(255) UNIQUE, is_wechat_user INT DEFAULT 0)')
    
    # 创建课程表
    c.execute('CREATE TABLE IF NOT EXISTS courses (id VARCHAR(36) PRIMARY KEY, title VARCHAR(255) NOT NULL, description TEXT NOT NULL, date VARCHAR(10) NOT NULL, time VARCHAR(20) NOT NULL, location VARCHAR(255) NOT NULL, capacity INT NOT NULL, registered INT DEFAULT 0, registration_start VARCHAR(19) NOT NULL, registration_end VARCHAR(19) NOT NULL, image VARCHAR(255))')
    
    # 为现有表添加image列（如果不存在）
    try:
        c.execute('ALTER TABLE courses ADD COLUMN image VARCHAR(255)')
    except Exception as e:
        # 如果列已经存在，忽略错误
        pass
    
    # 创建报名记录表
    c.execute('CREATE TABLE IF NOT EXISTS registrations (id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36) NOT NULL, course_id VARCHAR(36) NOT NULL, registration_date VARCHAR(30) NOT NULL, FOREIGN KEY (user_id) REFERENCES users (id), FOREIGN KEY (course_id) REFERENCES courses (id), UNIQUE (user_id, course_id))')
    
    # 添加管理员用户（如果不存在）
    admin_id = str(uuid.uuid4())
    admin_email = 'admin@example.com'
    name = 'admin'
    phone = '13800138000'
    organization = '系统管理员'
    c.execute('SELECT id FROM users WHERE email = %s', (admin_email,))
    if not c.fetchone():
        # 哈希管理员密码
        hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        c.execute('''INSERT INTO users (id, username, email, password, phone, organization, is_admin, wechat_unionid, wechat_openid, is_wechat_user, address) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                     (admin_id, name, admin_email, hashed_password, phone, organization, 1, '', '', 0, ''))
    
    # 检查是否已有课程数据
    c.execute('SELECT COUNT(*) FROM courses')
    course_count = c.fetchone()[0]
    
    # 只有当课程表为空时才初始化课程数据
    if course_count == 0:
        # 初始化课程数据
        courses = [
            {
                'title': '急救基础培训',
                'description': '掌握基本急救技能，包括心肺复苏、止血、包扎等',
                'date': '2026-02-15',
                'time': '09:00-17:00',
                'location': '市急救中心',
                'capacity': 50,
                'registered': 0,
                'registration_start': '2026-01-28 00:00:00',
                'registration_end': '2026-02-14 23:59:59'
            },
            {
                'title': '创伤急救进阶',
                'description': '针对各种创伤的急救处理，包括骨折、烧伤、头部创伤等',
                'date': '2026-02-22',
                'time': '09:00-17:00',
                'location': '市急救中心',
                'capacity': 30,
                'registered': 0,
                'registration_start': '2026-01-28 00:00:00',
                'registration_end': '2026-02-21 23:59:59'
            },
            {
                'title': '心脑血管急症处理',
                'description': '掌握心脑血管急症的识别和处理方法',
                'date': '2026-02-29',
                'time': '09:00-17:00',
                'location': '市急救中心',
                'capacity': 40,
                'registered': 0,
                'registration_start': '2026-01-28 00:00:00',
                'registration_end': '2026-02-28 23:59:59'
            }
        ]
        
        # 插入课程数据
        for course in courses:
            # 生成UUID作为课程ID
            course_id = str(uuid.uuid4())
            # 插入课程数据
            c.execute('INSERT INTO courses (id, title, description, date, time, location, capacity, registered, registration_start, registration_end, image) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                      (course_id, course['title'], course['description'], course['date'],
                       course['time'], course['location'], course['capacity'], course['registered'],
                       course['registration_start'], course['registration_end'], course.get('image', '')))
    
    conn.commit()
    conn.close()

# 导出函数
__all__ = ['get_db_connection', 'init_db']
