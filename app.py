from flask import Flask, redirect, url_for, render_template, request
from flask_cors import CORS
from config import DB_CONFIG, WECHAT_CONFIG, FLASK_CONFIG
from db_init import init_db

# 创建Flask应用
app = Flask(__name__, template_folder='src/views')
CORS(app)
app.config['SECRET_KEY'] = FLASK_CONFIG['SECRET_KEY']
app.config['TEMPLATES_AUTO_RELOAD'] = True

# 添加uploads目录的静态文件访问
import os
uploads_dir = os.path.join(app.root_path, 'uploads')
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
# 保持默认的静态文件夹设置，同时添加uploads目录的访问
from flask import send_from_directory

@app.route('/uploads/<path:filename>')
def uploads(filename):
    return send_from_directory(uploads_dir, filename)

# 初始化数据库
init_db()

# 导入并注册蓝图
from user import register_routes as user_routes
from course import register_routes as course_routes
from login import register_routes as login_routes
from wx_login import register_routes as wx_login_routes
from admin import register_routes as admin_routes

# 注册所有路由
user_routes(app)
course_routes(app)
login_routes(app)
wx_login_routes(app)
admin_routes(app)

# 页面路由配置
@app.route('/')
def index():
    # 重定向到管理后台
    return redirect(url_for('admin.admin_dashboard'))

@app.route('/login')
def login_page():
    return render_template('login.html')

# 管理后台

if __name__ == '__main__':
    app.run(debug=True, port=5000)