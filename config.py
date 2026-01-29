# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'training_system'
}

# 微信公众号配置
WECHAT_CONFIG = {
    'app_id': 'your-wechat-app-id',
    'app_secret': 'your-wechat-app-secret'
}

# Flask应用配置
FLASK_CONFIG = {
    'SECRET_KEY': 'your-secret-key'
}

# 环境配置
ENVIRONMENT = {
    'development': {
        'debug': True,
        'host': 'localhost',
        'port': 5000
    },
    'production': {
        'debug': False,
        'host': '0.0.0.0',
        'port': 5000
    }
}
