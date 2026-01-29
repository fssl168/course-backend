# 院前培训报名系统

## 项目简介

这是一个基于Flask框架开发的院前培训报名系统，用于管理培训课程、用户报名等功能。系统支持普通登录和微信登录，管理员可以发布、编辑和管理课程，用户可以查看和报名课程。

## 技术栈

- **后端**：Flask、MySQL、JWT认证
- **前端**：HTML、JavaScript、CSS
- **数据库**：MySQL
- **认证**：JWT令牌认证、微信扫码登录

## 项目结构

```
FlaskProject/
├── src/
│   ├── views/           # HTML模板文件
│   │   ├── admin.html          # 管理后台首页
│   │   ├── login.html           # 登录页面
│   │   ├── my_courses.html      # 我的课程页面
│   │   └── user_management.html # 用户管理页面
│   └── router/
│       └── index.js     # 前端路由配置
├── uploads/             # 上传文件目录
├── admin.py             # 管理后台相关路由
├── app.py               # 主应用入口
├── auth.py              # 认证相关功能
├── config.py            # 配置文件
├── course.py            # 课程相关API
├── db_init.py           # 数据库初始化
├── login.py             # 登录相关路由
├── user.py              # 用户相关API
├── wechat_utils.py      # 微信相关工具函数
└── wx_login.py          # 微信登录相关路由
```

## 功能特性

### 管理员功能
- 发布、编辑、删除课程
- 管理用户信息
- 查看课程报名情况
- 支持课程图片上传

### 用户功能
- 查看课程列表
- 报名/取消报名课程
- 查看我的课程
- 支持微信登录

## 安装说明

### 1. 环境要求

- Python 3.7+
- MySQL 5.7+
- pip 包管理器

### 2. 安装步骤

1. **克隆项目**

   ```bash
   git clone <项目地址>
   cd FlaskProject
   ```

2. **创建虚拟环境**

   ```bash
   python -m venv venv
   ```

3. **激活虚拟环境**

   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **安装依赖**

   ```bash
   pip install flask flask-cors pymysql pyjwt bcrypt cryptography requests
   ```

5. **配置数据库**

   修改 `config.py` 文件，配置数据库连接信息：

   ```python
   DB_CONFIG = {
       'user': 'your_username',
       'password': 'your_password',
       'host': 'localhost',
       'database': 'training_system'
   }
   ```

6. **初始化数据库**

   运行应用时会自动初始化数据库：

   ```bash
   python app.py
   ```

   系统会自动创建数据库表结构并插入默认管理员账户。

7. **启动应用**

   ```bash
   python app.py
   ```

   应用将在 `http://127.0.0.1:5000` 上运行。

## 默认账户

- **管理员账户**：
  - 邮箱：admin@example.com
  - 密码：admin123

## API 接口

### 认证相关
- `POST /api/login` - 用户登录
- `GET /api/wx-login` - 微信登录
- `GET /admin/login` - 管理员登录页面
- `GET /admin/logout` - 管理员退出登录

### 课程相关
- `GET /api/courses` - 获取课程列表
- `GET /api/courses/<course_id>` - 获取单个课程详情
- `POST /api/admin/courses` - 管理员创建课程
- `PUT /api/admin/courses/<course_id>` - 管理员编辑课程
- `DELETE /api/admin/courses/<course_id>` - 管理员删除课程
- `POST /api/courses/<course_id>/register` - 用户报名课程
- `DELETE /api/courses/<course_id>/unregister` - 用户取消报名

### 用户相关
- `GET /api/admin/users` - 管理员获取用户列表
- `GET /api/my-courses` - 获取当前用户的课程

## 微信登录配置

要使用微信登录功能，需要在 `config.py` 文件中配置微信公众号的 `app_id` 和 `app_secret`：

```python
WECHAT_CONFIG = {
    'app_id': 'your_wechat_app_id',
    'app_secret': 'your_wechat_app_secret'
}
```

## 注意事项

1. 本项目为开发环境配置，生产环境部署时需要进行安全配置
2. 上传文件存储在 `uploads` 目录，请确保该目录有写入权限
3. 数据库连接信息需要根据实际环境进行配置
4. 微信登录功能需要在微信公众平台进行相应配置

## 许可证

MIT License

## 联系方式

如有问题，请联系系统管理员。