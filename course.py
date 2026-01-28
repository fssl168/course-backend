from flask import Blueprint, request, jsonify, current_app
import uuid
import datetime
import os
from db_init import get_db_connection
from auth import admin_required
from config import FLASK_CONFIG
import jwt

# 创建蓝图
course_bp = Blueprint('course', __name__)


# 管理员发布课程
@course_bp.route('/api/admin/courses', methods=['POST'])
@admin_required
def create_course():
    try:
        # 获取表单数据
        title = request.form.get('title')
        description = request.form.get('description')
        date = request.form.get('date')
        time = request.form.get('time')
        location = request.form.get('location')
        capacity = int(request.form.get('capacity'))
        registration_start = request.form.get('registration_start')
        registration_end = request.form.get('registration_end')

        # 处理文件上传
        image = ''
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                # 确保上传目录存在
                upload_folder = os.path.join(current_app.root_path, 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                # 生成唯一的文件名
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                
                # 存储相对路径
                image = '/uploads/' + filename

        print(f"获取到的表单数据: title={title}, description={description}, date={date}")

        conn = None
        try:
            conn = get_db_connection()
            c = conn.cursor()

            # 创建课程
            course_id = str(uuid.uuid4())
            print(f"准备插入课程，course_id={course_id}")
            c.execute('''INSERT INTO courses (id, title, description, date, time, location, capacity, registered, registration_start, registration_end, image)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                      (course_id, title, description, date, time, location, capacity, 0, registration_start,
                       registration_end, image))

            conn.commit()
            print(f"课程创建成功，course_id={course_id}")
            return jsonify({'message': '课程创建成功', 'course_id': course_id}), 201
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"数据库操作失败: {str(e)}")
            return jsonify({'message': f'课程创建失败: {str(e)}'}), 500
        finally:
            if conn:
                conn.close()
    except Exception as e:
        print(f"处理请求失败: {str(e)}")
        return jsonify({'message': f'课程创建失败: {str(e)}'}), 500


# 管理员编辑课程
@course_bp.route('/api/admin/courses/<course_id>', methods=['PUT'])
@admin_required
def update_course(course_id):
    # 获取表单数据
    title = request.form.get('title')
    description = request.form.get('description')
    date = request.form.get('date')
    time = request.form.get('time')
    location = request.form.get('location')
    capacity = int(request.form.get('capacity'))
    registration_start = request.form.get('registration_start')
    registration_end = request.form.get('registration_end')

    # 处理文件上传
    image = None
    if 'image' in request.files:
        file = request.files['image']
        if file.filename:
            # 确保上传目录存在
            upload_folder = os.path.join(current_app.root_path, 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            # 生成唯一的文件名
            filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            
            # 存储相对路径
            image = '/uploads/' + filename

    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # 检查课程是否存在
        c.execute('SELECT id, date FROM courses WHERE id = %s', (course_id,))
        course = c.fetchone()
        if not course:
            return jsonify({'message': '课程不存在'}), 404

        # 检查课程是否已结束
        today = datetime.datetime.now()
        c.execute('SELECT registration_end FROM courses WHERE id = %s', (course_id,))
        db_registration_end = c.fetchone()
        if db_registration_end:
            class_end_date = datetime.datetime.strptime(db_registration_end[0], '%Y-%m-%d %H:%M:%S')
            end_date = class_end_date + datetime.timedelta(days=1)
            if today > end_date:
                return jsonify({'message': '已结束课程不可编辑'}), 400

        # 更新课程
        if image:
            c.execute('''UPDATE courses SET title = %s, description = %s, date = %s, time = %s, location = %s, capacity = %s, registration_start = %s, registration_end = %s, image = %s
                         WHERE id = %s''',
                      (title, description, date, time, location, capacity, registration_start, registration_end, image, course_id))
        else:
            c.execute('''UPDATE courses SET title = %s, description = %s, date = %s, time = %s, location = %s, capacity = %s, registration_start = %s, registration_end = %s
                         WHERE id = %s''',
                      (title, description, date, time, location, capacity, registration_start, registration_end, course_id))

        conn.commit()
        return jsonify({'message': '课程更新成功'}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'message': f'课程更新失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


# 管理员删除课程
@course_bp.route('/api/admin/courses/<course_id>', methods=['DELETE'])
@admin_required
def delete_course(course_id):
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # 检查课程是否存在
        c.execute('SELECT id, date FROM courses WHERE id = %s', (course_id,))
        course = c.fetchone()
        if not course:
            return jsonify({'message': '课程不存在'}), 404

        # 检查课程是否已结束
        today = datetime.date.today().strftime('%Y-%m-%d')
        if course[1] < today:
            return jsonify({'message': '已结束课程不可删除'}), 400

        # 删除相关的报名记录
        c.execute('DELETE FROM registrations WHERE course_id = %s', (course_id,))

        # 删除课程
        c.execute('DELETE FROM courses WHERE id = %s', (course_id,))

        conn.commit()
        return jsonify({'message': '课程删除成功'}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'message': f'课程删除失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


# 获取课程列表
@course_bp.route('/api/courses', methods=['GET'])
def get_courses():
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # 获取查询参数
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page

        # 构建SQL查询
        query = 'SELECT * FROM courses'
        count_query = 'SELECT COUNT(*) FROM courses'
        conditions = []
        params = []

        # 添加搜索条件
        if search:
            conditions.append('(title LIKE %s OR description LIKE %s)')
            params.extend([f'%{search}%', f'%{search}%'])

        # 添加状态筛选条件
        if status:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if status == 'upcoming':
                conditions.append('registration_start > %s')
                params.append(now)
            elif status == 'ongoing':
                conditions.append('registration_start <= %s AND registration_end >= %s')
                params.extend([now, now])
            elif status == 'ended':
                conditions.append('registration_end < %s')
                params.append(now)

        # 组合查询条件
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
            count_query += ' WHERE ' + ' AND '.join(conditions)

        # 添加排序
        query += ' ORDER BY date DESC'

        # 添加分页
        query += ' LIMIT %s OFFSET %s'
        params.extend([per_page, offset])

        # 执行查询
        c.execute(query, params)
        courses = c.fetchall()

        # 获取总记录数
        c.execute(count_query, params[:-2])
        total = c.fetchone()[0]

        # 转换为字典格式
        course_list = []
        for course in courses:
            if isinstance(course, tuple) and len(course) >= 10:
                course_dict = {
                    'id': course[0],
                    'title': course[1],
                    'description': course[2],
                    'date': course[3],
                    'time': course[4],
                    'location': course[5],
                    'capacity': course[6],
                    'registered': course[7],
                    'registration_start': course[8],
                    'registration_end': course[9],
                    'image': course[10] if len(course) > 10 else '',
                    'class_start': course[8]  # 使用registration_start作为class_start
                }
                course_list.append(course_dict)

        # 返回带分页信息的响应
        return jsonify({
            'courses': course_list,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'has_more': (page * per_page) < total
            }
        }), 200
    except Exception as e:
        print(f"获取课程列表失败: {str(e)}")
        return jsonify({'message': f'获取课程列表失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


# 获取单个课程信息
@course_bp.route('/api/courses/<course_id>', methods=['GET'])
def get_course(course_id):
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # 查询课程信息
        c.execute('SELECT * FROM courses WHERE id = %s', (course_id,))
        course = c.fetchone()

        if not course:
            return jsonify({'message': '课程不存在'}), 404

        # 查询报名人数
        c.execute('SELECT COUNT(*) FROM registrations WHERE course_id = %s', (course_id,))
        registered_count = c.fetchone()[0]

        # 构造课程信息
        course_dict = {
            'id': course[0],
            'title': course[1],
            'description': course[2],
            'date': course[3],
            'time': course[4],
            'location': course[5],
            'capacity': course[6],
            'registered': registered_count,  # 使用实际报名人数
            'registration_start': course[8],
            'registration_end': course[9],
            'image': course[10] if len(course) > 10 else ''
        }

        return jsonify(course_dict), 200
    except Exception as e:
        print(f"获取课程信息失败: {str(e)}")
        return jsonify({'message': f'获取课程信息失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


# 学生报名课程
@course_bp.route('/api/courses/<course_id>/register', methods=['POST'])
def register_course(course_id):
    try:
        # 从Authorization头中获取token
        token = request.headers.get('Authorization') or request.headers.get('authorization')
        print(f"获取到的Authorization头: {token}")
        if not token:
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
        except jwt.ExpiredSignatureError:
            return jsonify({'message': '认证令牌已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': '无效的认证令牌'}), 401
        except Exception as e:
            print(f"认证失败: {str(e)}")
            return jsonify({'message': f'认证失败: {str(e)}'}), 500

        conn = None
        try:
            conn = get_db_connection()
            c = conn.cursor()

            # 检查课程是否存在
            print(f"检查课程是否存在，课程ID: {course_id}")
            c.execute('SELECT capacity, registered, registration_start, registration_end FROM courses WHERE id = %s',
                      (course_id,))
            course = c.fetchone()
            print(f"查询到的课程信息: {course}")
            if not course:
                return jsonify({'message': '课程不存在'}), 404

            # 检查是否在报名时间内
            now = datetime.datetime.now()
            print(f"当前时间: {now}")
            print(f"报名开始时间: {course[2]}")
            print(f"报名结束时间: {course[3]}")
            registration_start = datetime.datetime.strptime(course[2], '%Y-%m-%d %H:%M:%S')
            registration_end = datetime.datetime.strptime(course[3], '%Y-%m-%d %H:%M:%S')

            if now < registration_start:
                return jsonify({'message': '报名尚未开始'}), 400
            if now > registration_end:
                return jsonify({'message': '报名已经结束'}), 400

            # 检查课程是否已满
            print(f"课程容量: {course[0]}, 已报名人数: {course[1]}")
            if course[1] >= course[0]:  # registered >= capacity
                return jsonify({'message': '课程已满'}), 400

            # 检查用户是否已报名
            print(f"检查用户是否已报名，用户ID: {user_id}, 课程ID: {course_id}")
            c.execute('SELECT id FROM registrations WHERE course_id = %s AND user_id = %s', (course_id, user_id))
            if c.fetchone():
                return jsonify({'message': '您已报名此课程'}), 400

            # 报名课程
            print(f"开始报名课程，用户ID: {user_id}, 课程ID: {course_id}")
            registration_id = str(uuid.uuid4())
            registration_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"生成报名记录ID: {registration_id}, 报名时间: {registration_date}")
            c.execute('INSERT INTO registrations (id, course_id, user_id, registration_date) VALUES (%s, %s, %s, %s)',
                      (registration_id, course_id, user_id, registration_date))
            c.execute('UPDATE courses SET registered = registered + 1 WHERE id = %s', (course_id,))

            conn.commit()
            print("报名成功")
            return jsonify({'message': '报名成功'}), 200
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"报名课程失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'message': f'报名课程失败: {str(e)}'}), 500
        finally:
            if conn:
                conn.close()
    except Exception as e:
        print(f"处理报名请求失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'处理报名请求失败: {str(e)}'}), 500


# 学生取消报名
@course_bp.route('/api/courses/<course_id>/unregister', methods=['DELETE'])
def unregister_course(course_id):
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
    except jwt.ExpiredSignatureError:
        return jsonify({'message': '认证令牌已过期'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': '无效的认证令牌'}), 401
    except Exception as e:
        return jsonify({'message': f'认证失败: {str(e)}'}), 500

    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # 检查用户是否已报名
        c.execute('SELECT id FROM registrations WHERE course_id = %s AND user_id = %s', (course_id, user_id))
        registration = c.fetchone()
        if not registration:
            return jsonify({'message': '您尚未报名此课程'}), 400

        # 取消报名
        c.execute('DELETE FROM registrations WHERE id = %s', (registration[0],))
        c.execute('UPDATE courses SET registered = registered - 1 WHERE id = %s', (course_id,))

        conn.commit()
        return jsonify({'message': '取消报名成功'}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"取消报名失败: {str(e)}")
        return jsonify({'message': f'取消报名失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


# 获取学生报名的课程列表
@course_bp.route('/api/my-courses', methods=['GET'])
def get_my_courses():
    try:
        # 从Authorization头中获取token
        token = request.headers.get('Authorization') or request.headers.get('authorization')
        print(f"获取到的Authorization头: {token}")
        if not token:
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
        except jwt.ExpiredSignatureError:
            return jsonify({'message': '认证令牌已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': '无效的认证令牌'}), 401
        except Exception as e:
            print(f"认证失败: {str(e)}")
            return jsonify({'message': f'认证失败: {str(e)}'}), 500

        conn = None
        try:
            conn = get_db_connection()
            c = conn.cursor()

            # 查询学生报名的课程
            print(f"执行SQL查询获取用户报名记录，用户ID: {user_id}")
            c.execute('''SELECT c.*, r.registration_date
                         FROM courses c
                         JOIN registrations r ON c.id = r.course_id
                         WHERE r.user_id = %s
                         ORDER BY c.date DESC''', (user_id,))
            courses = c.fetchall()
            print(f"查询结果数量: {len(courses)}")

            # 转换为字典格式
            course_list = []
            for course in courses:
                print(f"处理课程记录: {course}")
                if isinstance(course, tuple) and len(course) >= 10:
                    course_dict = {
                        'id': course[0],
                        'title': course[1],
                        'description': course[2],
                        'date': course[3],
                        'time': course[4],
                        'location': course[5],
                        'capacity': course[6],
                        'registered': course[7],
                        'registration_start': course[8],
                        'registration_end': course[9],
                        'registered_at': course[10] if len(course) > 10 else None
                    }
                    course_list.append(course_dict)

            print(f"返回课程列表数量: {len(course_list)}")
            return jsonify(course_list), 200
        except Exception as e:
            print(f"获取我的课程失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'message': f'获取我的课程失败: {str(e)}'}), 500
        finally:
            if conn:
                conn.close()
    except Exception as e:
        print(f"处理请求失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'处理请求失败: {str(e)}'}), 500


# 提供一个函数来注册蓝图
def register_routes(app):
    app.register_blueprint(course_bp)
