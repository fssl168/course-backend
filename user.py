from flask import Blueprint, request, jsonify
import uuid
import bcrypt
import jwt
import datetime
from functools import wraps
from db_init import get_db_connection
from auth import admin_required
from config import FLASK_CONFIG
from models import User

# 创建蓝图
user_bp = Blueprint('user', __name__)

@user_bp.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': '缺少请求数据'}), 400
        
        # 输入验证
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone')
        organization = data.get('organization')
        address = data.get('address', '')
        
        # 验证必填字段
        if not username or len(username) > 50:
            return jsonify({'message': '用户名长度必须在1-50之间'}), 400
        if not email or '@' not in email or len(email) > 100:
            return jsonify({'message': '邮箱格式不正确'}), 400
        if not password or len(password) < 6:
            return jsonify({'message': '密码长度至少为6位'}), 400
        if not phone or len(phone) not in [11, 12]:
            return jsonify({'message': '电话号码格式不正确'}), 400
        if not organization or len(organization) > 100:
            return jsonify({'message': '单位名称长度不能超过100'}), 400
        if address and len(address) > 200:
            return jsonify({'message': '地址长度不能超过200'}), 400

        # 使用ORM查询
        from models import SessionLocal
        db = SessionLocal()

        # 检查用户是否已存在
        existing_user = db.query(User).filter_by(email=email).first()
        if existing_user:
            db.close()
            return jsonify({'message': '用户已存在'}), 400

        # 哈希密码
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # 创建用户
        user_id = str(uuid.uuid4())
        new_user = User(
            id=user_id,
            username=username,
            email=email,
            password=hashed_password,
            phone=phone,
            organization=organization,
            address=address,
            is_admin=0,
            is_wechat_user=0
        )
        db.add(new_user)
        db.commit()
        db.close()
        return jsonify({'message': '注册成功'}), 201
    except Exception as e:
        if 'db' in locals() and db:
            db.rollback()
            db.close()
        return jsonify({'message': f'注册失败: {str(e)}'}), 500

@user_bp.route('/api/admin/users', methods=['GET'])
@admin_required
def get_users():
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # 获取查询参数
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page

        # 构建SQL查询
        query = 'SELECT id, username, email, phone, organization, is_admin, wechat_unionid FROM users'
        count_query = 'SELECT COUNT(*) FROM users'
        conditions = []
        params = []

        # 添加搜索条件
        if search:
            conditions.append('(username LIKE %s OR email LIKE %s OR phone LIKE %s OR organization LIKE %s)')
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'])

        # 组合查询条件
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
            count_query += ' WHERE ' + ' AND '.join(conditions)

        # 添加排序
        query += ' ORDER BY username ASC'

        # 添加分页
        query += ' LIMIT %s OFFSET %s'
        params.extend([per_page, offset])

        # 执行查询
        c.execute(query, params)
        users = c.fetchall()

        # 获取总记录数
        c.execute(count_query, params[:-2])
        total = c.fetchone()[0]

        # 转换为字典格式
        user_list = []
        for user in users:
            if isinstance(user, tuple) and len(user) >= 6:
                user_dict = {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'phone': user[3],
                    'organization': user[4],
                    'is_admin': user[5] if len(user) > 5 else 0,
                    'is_wechat_user': 1 if (len(user) > 6 and user[6]) else 0
                }
                user_list.append(user_dict)

        # 返回带分页信息的响应
        return jsonify({
            'users': user_list,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'has_more': (page * per_page) < total
            }
        }), 200
    except Exception as e:
        print(f"获取用户列表失败: {str(e)}")
        return jsonify({'message': f'获取用户列表失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@user_bp.route('/api/user-info', methods=['GET'])
def get_user_info():
    # 从查询参数获取user_id
    user_id = request.args.get('user_id')
    
    # 从Authorization头中获取token
    token = request.headers.get('Authorization') or request.headers.get('authorization')
    if not token:
        return jsonify({'message': '缺少认证令牌'}), 401

    # 移除Bearer前缀
    if token.startswith('Bearer '):
        token = token[7:]

    try:
        # 解码token
        jwt.decode(token, FLASK_CONFIG['SECRET_KEY'], algorithms=['HS256'])
        
        # 如果没有提供user_id，返回错误
        if not user_id:
            return jsonify({'message': '缺少用户ID参数'}), 400

        # 查找用户
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = c.fetchone()
        conn.close()

        if not user:
            return jsonify({'message': '用户不存在'}), 404

        # 转换为字典格式
        user_dict = {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'phone': user[4],
            'organization': user[5],
            'address': user[6] if len(user) > 6 else '',
            'is_admin': user[7] if len(user) > 7 else 0
        }

        return jsonify(user_dict), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': '认证令牌已过期'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': '无效的认证令牌'}), 401
    except Exception as e:
        return jsonify({'message': f'获取用户信息失败: {str(e)}'}), 500

@user_bp.route('/api/user-profile', methods=['GET'])
def get_user_profile():
    # 从Authorization头中获取token
    token = request.headers.get('Authorization') or request.headers.get('authorization')
    if not token:
        return jsonify({'message': '缺少认证令牌'}), 401

    # 移除Bearer前缀
    if token.startswith('Bearer '):
        token = token[7:]

    try:
        # 解码token
        data = jwt.decode(token, FLASK_CONFIG['SECRET_KEY'], algorithms=['HS256'])
        user_id = data['user_id']

        # 查找用户
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = c.fetchone()
        conn.close()

        if not user:
            return jsonify({'message': '用户不存在'}), 404

        # 转换为字典格式
        user_dict = {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'phone': user[4],
            'organization': user[5],
            'address': user[6] if len(user) > 6 else '',
            'is_admin': user[7] if len(user) > 7 else 0,
            'is_wechat_user': user[10] if len(user) > 10 else 0
        }

        return jsonify(user_dict), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': '认证令牌已过期'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': '无效的认证令牌'}), 401
    except Exception as e:
        return jsonify({'message': f'获取个人信息失败: {str(e)}'}), 500

@user_bp.route('/api/user-profile', methods=['PUT'])
def update_user_profile():
    # 从Authorization头中获取token
    token = request.headers.get('Authorization') or request.headers.get('authorization')
    if not token:
        return jsonify({'message': '缺少认证令牌'}), 401

    # 移除Bearer前缀
    if token.startswith('Bearer '):
        token = token[7:]

    try:
        # 解码token
        data = jwt.decode(token, FLASK_CONFIG['SECRET_KEY'], algorithms=['HS256'])
        user_id = data['user_id']

        # 获取更新数据
        update_data = request.get_json()
        username = update_data.get('username')
        email = update_data.get('email')
        phone = update_data.get('phone')
        organization = update_data.get('organization')
        address = update_data.get('address')

        # 查找用户
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE id = %s', (user_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({'message': '用户不存在'}), 404

        # 更新用户信息
        c.execute('''UPDATE users SET username = %s, email = %s, phone = %s, organization = %s, address = %s
                     WHERE id = %s''',
                  (username, email, phone, organization, address, user_id))
        conn.commit()
        conn.close()

        return jsonify({'message': '个人信息更新成功'}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': '认证令牌已过期'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': '无效的认证令牌'}), 401
    except Exception as e:
        return jsonify({'message': f'更新个人信息失败: {str(e)}'}), 500

@user_bp.route('/api/change-password', methods=['POST'])
def change_password():
    # 从Authorization头中获取token
    token = request.headers.get('Authorization') or request.headers.get('authorization')
    if not token:
        return jsonify({'message': '缺少认证令牌'}), 401

    # 移除Bearer前缀
    if token.startswith('Bearer '):
        token = token[7:]

    try:
        # 解码token
        data = jwt.decode(token, FLASK_CONFIG['SECRET_KEY'], algorithms=['HS256'])
        user_id = data['user_id']

        # 获取请求数据
        password_data = request.get_json()
        current_password = password_data['current_password']
        new_password = password_data['new_password']

        # 校验当前密码
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT password FROM users WHERE id = %s', (user_id,))
        result = c.fetchone()
        if not result:
            conn.close()
            return jsonify({'message': '用户不存在'}), 404
        stored_password = result[0]
        if not bcrypt.checkpw(current_password.encode('utf-8'), stored_password.encode('utf-8')):
            conn.close()
            return jsonify({'message': '当前密码错误'}), 400

        # 更新密码
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        c.execute('UPDATE users SET password = %s WHERE id = %s', (hashed_password, user_id))
        conn.commit()
        conn.close()

        return jsonify({'message': '密码修改成功'}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': '认证令牌已过期'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': '无效的认证令牌'}), 401
    except Exception as e:
        return jsonify({'message': f'修改密码失败: {str(e)}'}), 500

# 重置用户密码
@user_bp.route('/api/admin/users/<user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # 检查用户是否存在
        c.execute('SELECT id FROM users WHERE id = %s', (user_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({'message': '用户不存在'}), 404

        # 生成默认密码的哈希值
        default_password = '123456'
        hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # 更新用户密码
        c.execute('UPDATE users SET password = %s WHERE id = %s', (hashed_password, user_id))
        conn.commit()
        conn.close()

        return jsonify({'message': '密码重置成功，新密码为 "123456"'}), 200

    except Exception as e:
        return jsonify({'message': f'重置密码失败: {str(e)}'}), 500

# 编辑用户信息
@user_bp.route('/api/admin/users/<user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # 检查用户是否存在
        c.execute('SELECT id FROM users WHERE id = %s', (user_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({'message': '用户不存在'}), 404

        # 获取更新数据
        update_data = request.get_json()
        username = update_data.get('username')
        email = update_data.get('email')
        phone = update_data.get('phone')
        organization = update_data.get('organization')
        address = update_data.get('address')
        is_admin = update_data.get('is_admin', 0)

        # 更新用户信息
        c.execute('''UPDATE users SET username = %s, email = %s, phone = %s, organization = %s, address = %s, is_admin = %s
                     WHERE id = %s''',
                  (username, email, phone, organization, address, is_admin, user_id))
        conn.commit()
        conn.close()

        return jsonify({'message': '用户信息更新成功'}), 200

    except Exception as e:
        return jsonify({'message': f'更新用户信息失败: {str(e)}'}), 500

# 提供一个函数来注册蓝图
def register_routes(app):
    app.register_blueprint(user_bp)