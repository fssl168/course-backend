from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DB_CONFIG

# 创建数据库连接URL
DATABASE_URL = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:3306/training_system"

# 创建引擎
engine = create_engine(DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 用户模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, index=True)
    username = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    organization = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    is_admin = Column(Integer, default=0)
    wechat_unionid = Column(String(255), unique=True, nullable=True)
    wechat_openid = Column(String(255), unique=True, nullable=True)
    is_wechat_user = Column(Integer, default=0)

# 课程模型
class Course(Base):
    __tablename__ = "courses"
    
    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    date = Column(String(10), nullable=False)
    time = Column(String(20), nullable=False)
    location = Column(String(255), nullable=False)
    capacity = Column(Integer, nullable=False)
    registered = Column(Integer, default=0)
    registration_start = Column(String(19), nullable=False)
    registration_end = Column(String(19), nullable=False)
    image = Column(String(255), nullable=True)

# 报名记录模型
class Registration(Base):
    __tablename__ = "registrations"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    course_id = Column(String(36), nullable=False, index=True)
    registration_date = Column(String(30), nullable=False)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 导出
__all__ = ["Base", "User", "Course", "Registration", "get_db", "engine"]
