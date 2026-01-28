from flask import Blueprint, request, jsonify, render_template, redirect, make_response
import bcrypt
import jwt
import datetime
from db_init import get_db_connection
from config import FLASK_CONFIG

# 创建蓝图
login_bp = Blueprint('login', __name__)

# 用户登录
@login_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # 查找用户
        c.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = c.fetchone()

        if not user:
            return jsonify({'message': '用户不存在'}), 401

        # 验证密码
        if not bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8') if isinstance(user[3], str) else user[3]):
            return jsonify({'message': '密码错误'}), 401

        # 生成JWT令牌
        token = jwt.encode(
            {'user_id': user[0], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
            FLASK_CONFIG['SECRET_KEY'],
            algorithm='HS256'
        )

        return jsonify({'token': token, 'user': {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'phone': user[4],
            'organization': user[5],
            'is_admin': user[6] if len(user) > 6 else 0
        }}), 200
    except Exception as e:
        return jsonify({'message': f'登录失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

# 管理员登录页面
@login_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login_page():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        # 处理登录逻辑
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = None
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # 查找用户
            c.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = c.fetchone()
            
            if not user:
                return render_template('login.html', error='用户不存在')
            
            # 验证密码
            if not bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8') if isinstance(user[3], str) else user[3]):
                return render_template('login.html', error='密码错误')
            
            # 生成JWT令牌
            token = jwt.encode(
                {'user_id': user[0], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
                FLASK_CONFIG['SECRET_KEY'],
                algorithm='HS256'
            )
            
            # 创建响应对象
            resp = make_response(redirect('/admin'))
            
            # 将token存储到cookie中
            resp.set_cookie('token', token, max_age=3600*24, httponly=False, secure=False, path='/')
            
            # 返回响应
            return resp
        except Exception as e:
            return render_template('login.html', error=f'登录失败: {str(e)}')
        finally:
            if conn:
                conn.close()

# 管理员退出登录
@login_bp.route('/admin/logout')
def admin_logout():
    # 创建响应对象
    resp = make_response(redirect('/login'))
    
    # 清除cookie中的token
    resp.set_cookie('token', '', max_age=0, httponly=False, secure=False, path='/')
    
    # 返回响应
    return resp

# 提供一个函数来注册蓝图
def register_routes(app):
    app.register_blueprint(login_bp)