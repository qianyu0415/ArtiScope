import os
from flask import Flask, request, jsonify, session
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import oss2 # 导入阿里云 OSS SDK
from PIL import Image as PILImage # 导入 Pillow 用于图像处理
import io # 用于处理内存中的字节流
from img2img import convert_image_to_ascii_art, DEFAULT_ASCII_OPTIONS
from api import generate_image,check_task_status
import requests
import time

app = Flask(__name__)

# --- 数据库配置 ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:123456@localhost/ArtiScope')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-very-secure-and-long-secret-key-here')

db = SQLAlchemy(app)
load_dotenv()

# --- 阿里云 OSS 配置 ---
OSS_ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID')
OSS_ACCESS_KEY_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET')
OSS_BUCKET_NAME = os.environ.get('OSS_BUCKET_NAME')
OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT')

if OSS_ACCESS_KEY_ID and OSS_ACCESS_KEY_SECRET and OSS_BUCKET_NAME and OSS_ENDPOINT:
    auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
else:
    auth = None
    bucket = None
    app.logger.warning("OSS 配置不完整，图片上传和处理功能可能受限。")

# --- 辅助函数：登录验证装饰器 ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"message": "未授权访问，请先登录"}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- 数据库模型 ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # 关系：一个用户可以有多条图片处理记录
    image_processes = db.relationship('UserImageProcess', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

# UserImageProcess 模型保持不变，用于存储处理流程中的图片信息
class UserImageProcess(db.Model):
    __tablename__ = 'user_image_processes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    input_oss_url = db.Column(db.String(1024), nullable=False) # 存储原始图片的OSS URL
    input_token = db.Column(db.String(512), nullable=True)
    output_oss_url = db.Column(db.String(1024), nullable=True) # 存储处理后图片的OSS URL
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f'<UserImageProcess {self.id} for user {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'input_oss_url': self.input_oss_url,
            'input_token': self.input_token,
            'output_oss_url': self.output_oss_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# 文生图数据库模型
class TextToImageGeneration(db.Model):
    __tablename__ = 'text_to_image_generations'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    generated_image_oss_url = db.Column(db.String(1024), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    user = db.relationship('User', backref=db.backref('text_to_image_generations', lazy='dynamic'))
    
    def __repr__(self):
        return f'<TextToImageGeneration {self.id} for user {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'prompt': self.prompt,
            'generated_image_oss_url': self.generated_image_oss_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
# --- OSS 操作辅助函数 ---
def _generate_oss_key(user_id, original_filename, type_prefix=""):
    """生成唯一的OSS对象键名"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
    safe_filename = os.path.basename(original_filename) # 获取基本文件名
    return f"images/user_{user_id}/{timestamp}_{type_prefix}{safe_filename}"

def _upload_to_oss_and_get_url(oss_bucket, object_key, data_stream, content_type):
    """上传数据流到OSS并返回公共URL"""
    data_stream.seek(0) # 确保从头读取
    result = oss_bucket.put_object(object_key, data_stream, headers={'Content-Type': content_type})
    if result.status == 200:
        # 确保 OSS_BUCKET_NAME 和 OSS_ENDPOINT 是字符串
        return f"https://{str(OSS_BUCKET_NAME)}.{str(OSS_ENDPOINT)}/{object_key}"
    else:
        error_msg = f"OSS upload failed for {object_key}. Status: {result.status}"
        try:
            # 尝试读取响应体，但要注意它可能已经被读取或关闭
            resp_body = result.resp.read(1024) # 只读取一部分避免大响应体
            error_msg += f", Response: {resp_body.decode(errors='ignore')}"
        except Exception:
            pass 
        app.logger.error(error_msg)
        raise Exception(f"OSS upload failed for {object_key}")

# --- 用户认证 API 接口  ---
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"message": "请求参数不完整"}), 400
    username = data['username']
    password = data['password']
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "用户名已存在"}), 409
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password_hash=hashed_password)
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "用户注册成功"}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"注册失败: {e}")
        return jsonify({"message": "数据库错误", "error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"message": "请求参数不完整"}), 400
    username = data['username']
    password = data['password']
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "用户名或密码错误"}), 401
    session['user_id'] = user.id
    session['username'] = user.username
    return jsonify({"message": "登录成功", "user_id": user.id, "username": user.username}), 200

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({"message": "登出成功"}), 200

@app.route('/profile', methods=['GET'])
@login_required
def profile():
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "用户不存在"}), 404
    return jsonify({
        "user_id": user.id,
        "username": user.username,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }), 200

# 图像处理路由
@app.route('/log_image_process', methods=['POST'])
@login_required
def log_image_process_and_upload_ascii():
    if not bucket:
        app.logger.error("OSS 服务未配置或配置错误，无法处理图片。")
        return jsonify({"message": "OSS 服务未配置或配置错误"}), 503

    if 'file' not in request.files:
        app.logger.warning("请求中未包含图片文件 (字段名应为 'file')")
        return jsonify({"message": "请求中未包含图片文件 (字段名应为 'file')"}), 400
    
    file_storage = request.files['file']
    if file_storage.filename == '':
        app.logger.warning("未选择任何图片文件")
        return jsonify({"message": "未选择任何图片文件"}), 400

    token_from_form = request.form.get('token')
    
    # 从表单获取 ASCII 转换参数 (可选)
    ascii_options_from_form = {}
    if request.form.get('ascii_num_cols'):
        try:
            num_cols_val = int(request.form.get('ascii_num_cols'))
            if num_cols_val > 0 and num_cols_val < 1000: # 基本的范围检查
                 ascii_options_from_form['num_cols'] = num_cols_val
            else:
                app.logger.warning("提供的 ascii_num_cols 值无效或超出范围，使用默认值。")
        except ValueError:
            app.logger.warning("提供的 ascii_num_cols 不是有效整数，使用默认值。")
    if request.form.get('ascii_background') in ['black', 'white']:
        ascii_options_from_form['background'] = request.form.get('ascii_background')
    # 你可以按需添加更多参数如 language, mode

    user_id = session['user_id']
    username_in_session = session.get('username')
    if not username_in_session: 
        user = User.query.get(user_id) # @login_required 通常会保证 user_id 有效
        if not user:
            app.logger.error(f"用户 ID {user_id} 在会话或数据库中未找到。")
            return jsonify({"message": "当前会话用户异常"}), 500
        username_in_session = user.username
    
    original_filename_from_upload = file_storage.filename

    try:
        # 1. 将上传的文件内容读入内存 BytesIO 对象
        original_image_bytes_io = io.BytesIO(file_storage.read())
        original_content_type = file_storage.content_type 
        if not original_content_type or not original_content_type.startswith("image/"):
            app.logger.warning(f"上传文件的 Content-Type 无效: {original_content_type}")
            return jsonify({"message": "上传的文件似乎不是有效的图片格式"}), 400

        # 2. 上传原始图片到OSS
        original_oss_key = _generate_oss_key(user_id, original_filename_from_upload, type_prefix="original_")
        original_image_bytes_io.seek(0) # 重置指针以便上传
        original_oss_url = _upload_to_oss_and_get_url(bucket, original_oss_key, original_image_bytes_io, original_content_type)
        if not original_oss_url:
            app.logger.error("上传原始图片到OSS失败。")
            return jsonify({"message": "上传原始图片到OSS失败"}), 500

        # 3. 使用 ascii_processor 处理图片
        original_image_bytes_io.seek(0) # 重置指针以便 ascii_processor 再次读取
        
        current_ascii_options = DEFAULT_ASCII_OPTIONS.copy()
        current_ascii_options.update(ascii_options_from_form) # 用表单参数覆盖默认参数

        app.logger.info(f"开始ASCII转换，选项: {current_ascii_options}")
        pil_ascii_art_image = convert_image_to_ascii_art(original_image_bytes_io, options=current_ascii_options)

        if pil_ascii_art_image is None:
            app.logger.error("图片转换为ASCII艺术画失败 (convert_image_to_ascii_art 返回 None)。")
            return jsonify({"message": "图片转换为ASCII艺术画失败，请检查图片或服务器日志"}), 500

        # 将处理后的 PIL 图片保存到内存 BytesIO 对象
        processed_ascii_image_bytes_io = io.BytesIO()
        # ASCII 艺术图是灰度图 ('L' mode)，PNG 是较好的无损格式，JPEG也可以
        output_format_for_ascii = 'PNG' # 或者 'JPEG'
        pil_ascii_art_image.save(processed_ascii_image_bytes_io, format=output_format_for_ascii)
        processed_ascii_content_type = f'image/{output_format_for_ascii.lower()}' # 例如 'image/png'
        processed_ascii_image_bytes_io.seek(0) # 重置指针以便上传

        # 4. 上传处理后的 ASCII 图片到OSS
        base, ext = os.path.splitext(original_filename_from_upload)
        ascii_art_filename = f"{base}_ascii.{output_format_for_ascii.lower()}" # 例如: myimage_ascii.png
        processed_ascii_oss_key = _generate_oss_key(user_id, ascii_art_filename, type_prefix="processed_ascii_")
        
        processed_ascii_oss_url = _upload_to_oss_and_get_url(
            bucket, 
            processed_ascii_oss_key, 
            processed_ascii_image_bytes_io, 
            processed_ascii_content_type
        )
        if not processed_ascii_oss_url:
            app.logger.error("上传处理后的ASCII图片到OSS失败。")
            # 注意：此时原始图片已上传。可以考虑是否有回滚或清理策略。
            return jsonify({"message": "上传处理后的ASCII图片到OSS失败"}), 500

        # 5. 记录到数据库 (user_image_processes 表)
        new_process_log = UserImageProcess(
            user_id=user_id,
            username=username_in_session,
            input_oss_url=original_oss_url,     # 原始图片的URL
            input_token=token_from_form,        # 用户提供的Token
            output_oss_url=processed_ascii_oss_url # 处理后ASCII图片的URL
            # 可以考虑增加一个字段，例如 process_type="ascii_art" 来区分不同的处理类型
        )
        db.session.add(new_process_log)
        db.session.commit()

        app.logger.info(f"图片成功转换为ASCII艺术画并记录。日志ID: {new_process_log.id}")
        return jsonify({
            "message": "图片成功转换为ASCII艺术画、上传并记录",
            "log_entry_id": new_process_log.id,
            "original_image_url": original_oss_url,
            "processed_ascii_image_url": processed_ascii_oss_url, # 响应中明确指出这是ASCII图的URL
            "token_received": token_from_form, # 响应中明确是接收到的token
            "details": new_process_log.to_dict() if hasattr(new_process_log, 'to_dict') else {"id": new_process_log.id} # 返回完整的记录详情
        }), 201

    except oss2.exceptions.OssError as oe:
        db.session.rollback()
        app.logger.error(f"OSS 操作失败: {oe}", exc_info=True)
        return jsonify({"message": f"OSS 操作失败: {str(oe)}"}), 500
    except FileNotFoundError as fnfe: # 捕获 ascii_processor 中可能因 utils.py 或其资源文件找不到而抛出的错误
        db.session.rollback()
        app.logger.error(f"处理所需文件未找到 (可能与字体或 utils.py 配置有关): {fnfe}", exc_info=True)
        return jsonify({"message": f"服务配置错误，缺少处理所需文件: {str(fnfe)}"}), 503 # 503 Service Unavailable 可能更合适
    except Exception as e:
        db.session.rollback() 
        app.logger.error(f"图片处理和记录过程中发生未知错误: {e}", exc_info=True)
        return jsonify({"message": f"处理图片过程中发生未知错误: {str(e)}"}), 500


# --- 获取图片处理记录 API (保持不变) ---
@app.route('/image_process_logs', methods=['GET'])
@login_required
def get_user_image_process_logs():
    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    logs_pagination = UserImageProcess.query.filter_by(user_id=user_id)\
        .order_by(UserImageProcess.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    logs_data = [log.to_dict() for log in logs_pagination.items]
    return jsonify({
        "message": "成功获取图片处理记录",
        "logs": logs_data,
        "total_logs": logs_pagination.total,
        "current_page": logs_pagination.page,
        "total_pages": logs_pagination.pages,
        "per_page": logs_pagination.per_page
    }), 200

# 文生图路由
@app.route('/generate_image_from_text', methods=['POST'])
@login_required
def generate_image_from_text():
    if not bucket:
        app.logger.error("OSS 服务未配置或配置错误，无法处理图片。")
        return jsonify({"message": "OSS 服务未配置或配置错误"}), 503
    
    data = request.get_json()
    if not data or not data.get('prompt'):
        return jsonify({"message": "缺少必要的prompt参数"}), 400
    
    prompt = data['prompt']
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"message": "用户不存在"}), 404
    
    try:
        # 1. 调用DashScope API生成图片
        api_key = os.environ.get('DASHSCOPE_API_KEY')
        if not api_key:
            return jsonify({"message": "DashScope API密钥未配置"}), 500
        
        # 调用API生成图片
        creation_result = generate_image(prompt, api_key)
        task_id = creation_result["output"]["task_id"]
        
        # 2. 轮询任务状态
        while True:
            status_result = check_task_status(task_id, api_key)
            task_status = status_result["output"]["task_status"]
            
            if task_status == "SUCCEEDED":
                break
            elif task_status in ["FAILED", "CANCELED"]:
                raise Exception(f"任务失败，状态: {task_status}")
            
            time.sleep(5)
        
        # 3. 获取生成的图片URL
        image_url = status_result["output"]["results"][0]["url"]
        
        # 4. 下载图片并上传到OSS
        response = requests.get(image_url)
        if response.status_code != 200:
            raise Exception(f"图片下载失败: {response.status_code}")
        
        # 创建内存中的图片数据流
        image_data = io.BytesIO(response.content)
        image_data.seek(0)
        
        # 生成OSS对象键名
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        oss_key = f"generated_images/user_{user_id}/{timestamp}_generated.jpg"
        
        # 上传到OSS
        oss_url = _upload_to_oss_and_get_url(bucket, oss_key, image_data, 'image/jpeg')
        
        # 5. 保存记录到数据库
        new_generation = TextToImageGeneration(
            user_id=user_id,
            prompt=prompt,
            generated_image_oss_url=oss_url
        )
        
        db.session.add(new_generation)
        db.session.commit()
        
        return jsonify({
            "message": "图片生成并保存成功",
            "generation": new_generation.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"图片生成过程中发生错误: {str(e)}", exc_info=True)
        return jsonify({"message": f"图片生成失败: {str(e)}"}), 500

# 获取文生图的图片内容
@app.route('/text_to_image_logs', methods=['GET'])
@login_required
def get_text_to_image_logs():
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    user_id = session['user_id']

    # 构建基础查询
    query = TextToImageGeneration.query.filter_by(user_id=user_id)


    # 执行分页查询
    logs_pagination = query.order_by(
        TextToImageGeneration.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    # 准备返回数据
    logs_data = [log.to_dict() for log in logs_pagination.items]

    return jsonify({
        'message': '成功获取文字生成图片记录',
        'data': logs_data,
        'pagination': {
            'total': logs_pagination.total,
            'pages': logs_pagination.pages,
            'current_page': logs_pagination.page,
            'per_page': logs_pagination.per_page,
            'has_next': logs_pagination.has_next,
            'has_prev': logs_pagination.has_prev
        }
    }), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    
    if not auth or not bucket:
        print("="*50)
        print("警告: 阿里云 OSS 未正确配置或配置不完整。")
        print("图片上传功能及依赖OSS的图片处理记录功能可能无法正常工作。")
        print("请检查环境变量: OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET_NAME, OSS_ENDPOINT")
        print("="*50)
    else:
        print("阿里云 OSS 配置加载成功。")
        
    app.run(debug=True, port=5000)