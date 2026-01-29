from flask import Blueprint, request, jsonify, render_template, redirect, make_response, send_file
import bcrypt
import jwt
import datetime
from db_init import get_db_connection
from config import FLASK_CONFIG
from models import User
from captcha import generate_captcha, verify_captcha

# 创建蓝图
login_bp = Blueprint('login', __name__)

# 用户登录
@login_bp.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': '缺少请求数据'}), 400
        
        # 输入验证
        email = data.get('email')
        password = data.get('password')
        
        if not email or '@' not in email or len(email) > 100:
            return jsonify({'message': '邮箱格式不正确'}), 400
        if not password or len(password) < 6:
            return jsonify({'message': '密码长度至少为6位'}), 400

        # 使用ORM查询
        from models import SessionLocal
        db = SessionLocal()
        
        # 查找用户
        user = db.query(User).filter_by(email=email).first()

        if not user:
            db.close()
            return jsonify({'message': '用户不存在'}), 401

        # 验证密码
        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            db.close()
            return jsonify({'message': '密码错误'}), 401

        # 生成JWT令牌
        token = jwt.encode(
            {'user_id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
            FLASK_CONFIG['SECRET_KEY'],
            algorithm='HS256'
        )

        db.close()
        return jsonify({'token': token, 'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'organization': user.organization,
            'address': user.address,
            'is_admin': user.is_admin,
            'is_wechat_user': user.is_wechat_user
        }}), 200
    except Exception as e:
        if 'db' in locals() and db:
            db.close()
        return jsonify({'message': f'登录失败: {str(e)}'}), 500

# 管理员登录页面
@login_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login_page():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        # 处理登录逻辑
        email = request.form.get('email')
        password = request.form.get('password')
        captcha = request.form.get('captcha')
        
        # 验证验证码
        if not captcha:
            return render_template('login.html', error='请输入验证码')
        
        if not verify_captcha(captcha):
            return render_template('login.html', error='验证码错误')
        
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

# 验证码图片生成
@login_bp.route('/api/captcha', methods=['GET'])
def get_captcha():
    captcha_image = generate_captcha()
    return send_file(captcha_image, mimetype='image/png')

# 提供一个函数来注册蓝图
def register_routes(app):
    app.register_blueprint(login_bp)