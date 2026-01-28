from flask import Blueprint, render_template, request
import jwt
from db_init import get_db_connection
from config import FLASK_CONFIG

# 创建蓝图
admin_bp = Blueprint('admin', __name__)

# 管理后台
@admin_bp.route('/admin')
def admin_dashboard():
    # 获取课程数据
    courses = []
    user = None
    # 从请求头或cookie中获取token
    token = request.headers.get('Authorization') or request.headers.get('authorization') or request.cookies.get('token')
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 尝试解码token获取当前用户信息
        if token:
            # 移除Bearer前缀（如果有）
            if token.startswith('Bearer '):
                token = token[7:]
            try:
                # 解码token
                data = jwt.decode(token, FLASK_CONFIG['SECRET_KEY'], algorithms=['HS256'])
                user_id = data['user_id']
                
                # 获取当前用户信息
                c.execute('SELECT id, username, email, phone, organization, is_admin FROM users WHERE id = %s', (user_id,))
                user_data = c.fetchone()
                if user_data:
                    user = {
                        'id': user_data[0],
                        'username': user_data[1],
                        'email': user_data[2],
                        'phone': user_data[3],
                        'organization': user_data[4],
                        'is_admin': user_data[5] if len(user_data) > 5 else 0
                    }
            except Exception as e:
                pass
        
        # 获取所有课程及其报名人数
        c.execute('''
            SELECT c.*, COUNT(r.id) as registered 
            FROM courses c
            LEFT JOIN registrations r ON c.id = r.course_id
            GROUP BY c.id
            ORDER BY c.date DESC
        ''')
        courses_data = c.fetchall()
        
        for course in courses_data:
            courses.append({
                'id': course[0],
                'title': course[1],
                'description': course[2],
                'date': course[3],
                'time': course[4],
                'location': course[5],
                'capacity': course[6],
                'registered': course[11],  # 使用COUNT(r.id)的结果
                'registration_start': course[8],  # 正确的registration_start字段
                'registration_end': course[9],  # 正确的registration_end字段
                'class_start': course[8],  # 使用registration_start作为class_start
                'image': course[10] if len(course) > 10 else ''  # 正确的image字段
            })
        
        conn.close()
    except Exception as e:
        pass
    
    return render_template('admin.html', courses=courses, user=user)

@admin_bp.route('/admin/users')
def admin_users():
    # 从请求头或cookie中获取JWT令牌
    token = request.headers.get('Authorization') or request.headers.get('authorization') or request.cookies.get('token')
    user = None
    users = []
    
    try:
        # 从数据库中获取用户信息
        conn = get_db_connection()
        c = conn.cursor()
        
        # 尝试解码token获取当前用户信息
        if token:
            # 移除Bearer前缀（如果有）
            if token.startswith('Bearer '):
                token = token[7:]
            try:
                # 解码token
                data = jwt.decode(token, FLASK_CONFIG['SECRET_KEY'], algorithms=['HS256'])
                user_id = data['user_id']
                
                # 获取当前用户信息
                c.execute('SELECT id, username, email, phone, organization, is_admin FROM users WHERE id = %s', (user_id,))
                user_data = c.fetchone()
                if user_data:
                    user = {
                        'id': user_data[0],
                        'username': user_data[1],
                        'email': user_data[2],
                        'phone': user_data[3],
                        'organization': user_data[4],
                        'is_admin': user_data[5] if len(user_data) > 5 else 0
                    }
            except Exception as e:
                pass
        
        # 总是获取所有用户列表
        c.execute('SELECT id, username, email, phone, organization, is_admin, wechat_unionid, wechat_openid, is_wechat_user FROM users')
        users_data = c.fetchall()
        for u in users_data:
            users.append({
                'id': u[0],
                'username': u[1],
                'email': u[2],
                'phone': u[3],
                'organization': u[4],
                'is_admin': u[5] if len(u) > 5 else 0,
                'is_wechat_user': u[8] if len(u) > 8 else 0
            })
        
        conn.close()
    except Exception as e:
        pass
    
    return render_template('user_management.html', user=user, users=users, token=token)

# 提供一个函数来注册蓝图
def register_routes(app):
    app.register_blueprint(admin_bp)
