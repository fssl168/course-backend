from flask import request, jsonify
import jwt
import datetime
from functools import wraps
from db_init import get_db_connection
from config import FLASK_CONFIG


# 管理员权限验证装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查JWT认证
        token = request.headers.get('Authorization') or request.headers.get('authorization')
        print(f"获取到的Authorization头: {token}")

        if not token:
            print("未获取到认证令牌")
            return jsonify({'message': '缺少认证令牌'}), 401

        # 移除Bearer前缀
        if token.startswith('Bearer '):
            token = token[7:]
            print(f"移除Bearer前缀后的token: {token[:20]}...")

        try:
            # 解码token
            data = jwt.decode(token, FLASK_CONFIG['SECRET_KEY'], algorithms=['HS256'])
            user_id = data['user_id']
            print(f"解码token成功，用户ID: {user_id}")

            # 查找用户
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT is_admin FROM users WHERE id = %s', (user_id,))
            user = c.fetchone()
            print(f"查询到的用户信息: {user}")
            conn.close()

            # 检查用户是否存在且是管理员
            if not user:
                print("用户不存在")
                return jsonify({'message': '权限不足'}), 403
            if user[0] != 1:
                print(f"用户不是管理员，is_admin值: {user[0]}")
                return jsonify({'message': '权限不足'}), 403

            print("JWT认证成功")
        except jwt.ExpiredSignatureError:
            print("认证令牌已过期")
            return jsonify({'message': '认证令牌已过期'}), 401
        except jwt.InvalidTokenError as e:
            print(f"无效的认证令牌: {str(e)}")
            return jsonify({'message': '无效的认证令牌'}), 401
        except Exception as e:
            print(f"服务器错误: {str(e)}")
            return jsonify({'message': '服务器错误'}), 500

        return f(*args, **kwargs)

    return decorated_function