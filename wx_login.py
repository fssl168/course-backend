from flask import Blueprint, request, jsonify, redirect
import uuid
import bcrypt
import jwt
import datetime
import requests
from db_init import get_db_connection
from wechat_utils import get_wechat_access_token, get_wechat_user_info, get_wechat_session_key, decrypt_wechat_phone
from config import WECHAT_CONFIG, FLASK_CONFIG

# 创建蓝图
wx_login_bp = Blueprint('wx_login', __name__)


# 微信授权页面
@wx_login_bp.route('/api/wechat/auth', methods=['GET'])
def wechat_auth():
    # 重定向到微信授权页面
    import urllib.parse
    redirect_uri = urllib.parse.quote('http://localhost:5000/api/wechat/login')
    wechat_auth_url = f'https://open.weixin.qq.com/connect/qrconnect?appid={WECHAT_CONFIG["app_id"]}&redirect_uri={redirect_uri}&response_type=code&scope=snsapi_login#wechat_redirect'
    return redirect(wechat_auth_url)

# 微信手机号授权页面
@wx_login_bp.route('/api/wechat/phone-auth', methods=['GET'])
def wechat_phone_auth():
    # 重定向到微信授权页面，用于获取手机号
    import urllib.parse
    redirect_uri = urllib.parse.quote('http://localhost:5000/api/wechat/login')
    wechat_auth_url = f'https://open.weixin.qq.com/connect/qrconnect?appid={WECHAT_CONFIG["app_id"]}&redirect_uri={redirect_uri}&response_type=code&scope=snsapi_login#wechat_redirect'
    return redirect(wechat_auth_url)

# 微信登录回调
@wx_login_bp.route('/api/wechat/login', methods=['GET'])
def wx_login():
    code = request.args.get('code')
    if not code:
        return jsonify({'error': '缺少授权码'}), 400

    try:
        # 获取微信session key
        session_data = get_wechat_session_key(code)
        if 'errcode' in session_data:
            return jsonify({'error': session_data.get('errmsg', '微信登录失败')}), 400

        openid = session_data['openid']
        session_key = session_data.get('session_key', '')

        # 获取微信用户信息
        encrypted_data = request.args.get('encryptedData')
        iv = request.args.get('iv')

        if encrypted_data and iv:
            # 解密用户敏感信息
            decrypted_data = decrypt_wechat_phone(WECHAT_CONFIG['app_id'], session_key, encrypted_data, iv)
            # 构造用户信息
            user_info = {
                'nickName': '微信用户',
                'gender': 0,
                'city': '',
                'province': '',
                'country': '',
                'avatarUrl': '',
                'phoneNumber': decrypted_data.get('phoneNumber', '')
            }
        else:
            # 如果没有加密数据，只获取基本信息
            # 由于我们已经有了openid，直接构造用户信息
            user_info = {
                'nickName': '微信用户',
                'gender': 0,
                'city': '',
                'province': '',
                'country': '',
                'avatarUrl': ''
            }

        nickname = user_info.get('nickName', '微信用户')
        gender = user_info.get('gender', 0)
        city = user_info.get('city', '')
        province = user_info.get('province', '')
        country = user_info.get('country', '')
        avatar_url = user_info.get('avatarUrl', '')
        phone = user_info.get('phoneNumber', '')

        conn = None
        try:
            conn = get_db_connection()
            c = conn.cursor()

            # 检查微信用户是否已存在
            c.execute('SELECT id FROM users WHERE wechat_openid = %s', (openid,))
            existing_user = c.fetchone()

            if not existing_user:
                # 创建新的微信用户
                user_id = str(uuid.uuid4())  # 生成UUID作为用户ID
                email = f'{openid}@wechat.com'
                hashed_password = bcrypt.hashpw('wechat'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                c.execute('''INSERT INTO users (id, username, email, password, phone, organization, is_admin, wechat_unionid, wechat_openid, is_wechat_user, address) 
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                          (user_id, nickname, email,
                           hashed_password,
                           phone, nickname, 0, user_info.get('unionId', ''), openid, 1, ''))
                conn.commit()
            else:
                user_id = existing_user[0]
                # 更新用户信息
                c.execute('''UPDATE users SET username = %s, organization = %s, phone = %s 
                             WHERE id = %s''',
                          (nickname, nickname, phone, user_id))
                conn.commit()

            # 生成JWT令牌
            token = jwt.encode(
                {'user_id': user_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
                FLASK_CONFIG['SECRET_KEY'],
                algorithm='HS256'
            )

            # 查询完整的用户信息
            c.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            user = c.fetchone()
            conn.close()

            return jsonify({
                'token': token,
                'user': {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'phone': user[4],
                    'organization': user[5],
                    'is_admin': user[7] if len(user) > 7 else 0,
                    'is_wechat_user': user[10] if len(user) > 10 else 0
                }
            }), 200
        except Exception as e:
            if conn:
                conn.rollback()
            return jsonify({'error': f'数据库操作失败: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'微信登录失败: {str(e)}'}), 500


# 提供一个函数来注册蓝图
def register_routes(app):
    app.register_blueprint(wx_login_bp)