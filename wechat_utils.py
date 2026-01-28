import requests
import json
import base64
from Crypto.Cipher import AES
from config import WECHAT_CONFIG

# WXBizDataCrypt类，用于解密微信数据
class WXBizDataCrypt:
    def __init__(self, app_id, session_key):
        self.app_id = app_id
        self.session_key = session_key

    def decryptData(self, encrypted_data, iv):
        # 解码数据
        session_key = base64.b64decode(self.session_key)
        encrypted_data = base64.b64decode(encrypted_data)
        iv = base64.b64decode(iv)

        # 解密
        cipher = AES.new(session_key, AES.MODE_CBC, iv)
        decrypted = self._unpad(cipher.decrypt(encrypted_data))

        # 转换为JSON
        decrypted_data = json.loads(decrypted)

        # 验证app_id
        if decrypted_data['watermark']['appid'] != self.app_id:
            raise Exception('Invalid app_id')

        return decrypted_data

    def _unpad(self, s):
        return s[:-ord(s[len(s)-1:])]

# 获取微信access_token
def get_wechat_access_token(code):
    app_id = WECHAT_CONFIG['app_id']
    app_secret = WECHAT_CONFIG['app_secret']
    
    access_token_url = f'https://api.weixin.qq.com/sns/oauth2/access_token?appid={app_id}&secret={app_secret}&code={code}&grant_type=authorization_code'
    access_token_response = requests.get(access_token_url)
    access_token_data = access_token_response.json()
    
    return access_token_data

# 获取微信用户信息
def get_wechat_user_info(access_token, openid):
    user_info_url = f'https://api.weixin.qq.com/sns/userinfo?access_token={access_token}&openid={openid}&lang=zh_CN'
    user_info_response = requests.get(user_info_url)
    user_info = user_info_response.json()
    
    return user_info

# 获取微信session_key
def get_wechat_session_key(code):
    app_id = WECHAT_CONFIG['app_id']
    app_secret = WECHAT_CONFIG['app_secret']
    
    session_url = f'https://api.weixin.qq.com/sns/jscode2session?appid={app_id}&secret={app_secret}&js_code={code}&grant_type=authorization_code'
    session_response = requests.get(session_url)
    session_data = session_response.json()
    
    return session_data

# 解密微信手机号
def decrypt_wechat_phone(app_id, session_key, encrypted_data, iv):
    pc = WXBizDataCrypt(app_id, session_key)
    decrypted_data = pc.decryptData(encrypted_data, iv)
    
    return decrypted_data

# 导出函数
__all__ = [
    'WXBizDataCrypt',
    'get_wechat_access_token',
    'get_wechat_user_info',
    'get_wechat_session_key',
    'decrypt_wechat_phone'
]
