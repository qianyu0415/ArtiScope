import os
from flask_cors import CORS
from flask import Flask, request, jsonify, session
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import oss2
from PIL import Image as PILImage
import io
from img2img import convert_image_to_ascii_art, DEFAULT_ASCII_OPTIONS
from video2video import main as video2video_main
from video2video_color import main as video2video_color_main
from api import generate_image, check_task_status
import requests
import time
import tempfile
import argparse

app = Flask(__name__)

# 配置 CORS，允许 localhost:5173 访问，支持凭据

# 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:123456@localhost/ArtiScope')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-very-secure-and-long-secret-key-here')
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": ["http://localhost:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

db = SQLAlchemy(app)
load_dotenv()

# 阿里云 OSS 配置
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
    app.logger.warning("OSS 配置不完整，图片和视频上传功能可能受限。")

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"message": "未授权访问，请先登录"}), 401
        return f(*args, **kwargs)
    return decorated_function

# 数据库模型
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    image_processes = db.relationship('UserImageProcess', backref='user', lazy='dynamic')
    video_processes = db.relationship('UserVideoProcess', backref='user', lazy='dynamic')
    text_to_image_generations = db.relationship('TextToImageGeneration', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

class UserImageProcess(db.Model):
    __tablename__ = 'user_image_processes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    input_oss_url = db.Column(db.String(1024), nullable=False)
    input_token = db.Column(db.String(512), nullable=True)
    output_oss_url = db.Column(db.String(1024), nullable=True)
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

class UserVideoProcess(db.Model):
    __tablename__ = 'user_video_processes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    input_oss_url = db.Column(db.String(1024), nullable=False)
    input_token = db.Column(db.String(512), nullable=True)
    output_oss_url = db.Column(db.String(1024), nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f'<UserVideoProcess {self.id} for user {self.username}>'

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

class TextToImageGeneration(db.Model):
    __tablename__ = 'text_to_image_generations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    generated_image_oss_url = db.Column(db.String(1024), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

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

# OSS 操作辅助函数
def _generate_oss_key(user_id, original_filename, type_prefix="", is_video=False):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
    safe_filename = os.path.basename(original_filename)
    folder = "videos" if is_video else "images"
    return f"{folder}/user_{user_id}/{timestamp}_{type_prefix}{safe_filename}"

def _upload_to_oss_and_get_url(oss_bucket, object_key, data_stream, content_type):
    data_stream.seek(0)
    result = oss_bucket.put_object(object_key, data_stream, headers={'Content-Type': content_type})
    if result.status == 200:
        return f"https://{str(OSS_BUCKET_NAME)}.{str(OSS_ENDPOINT)}/{object_key}"
    else:
        error_msg = f"OSS upload failed for {object_key}. Status: {result.status}"
        try:
            resp_body = result.resp.read(1024)
            error_msg += f", Response: {resp_body.decode(errors='ignore')}"
        except Exception:
            pass
        app.logger.error(error_msg)
        raise Exception(f"OSS upload failed for {object_key}")

# 用户注册
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

# 用户登录
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

# 用户登出
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({"message": "登出成功"}), 200

# 获取用户信息
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

# 图片处理路由
@app.route('/log_image_process', methods=['POST'])
@login_required
def log_image_process():
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
    ascii_options_from_form = {}
    if request.form.get('ascii_num_cols'):
        try:
            num_cols_val = int(request.form.get('ascii_num_cols'))
            if 0 < num_cols_val < 1000:
                ascii_options_from_form['num_cols'] = num_cols_val
            else:
                app.logger.warning("提供的 ascii_num_cols 值无效或超出范围，使用默认值。")
        except ValueError:
            app.logger.warning("提供的 ascii_num_cols 不是有效整数，使用默认值。")
    if request.form.get('ascii_background') in ['black', 'white']:
        ascii_options_from_form['background'] = request.form.get('ascii_background')

    user_id = session['user_id']
    username_in_session = session.get('username')
    if not username_in_session:
        user = User.query.get(user_id)
        if not user:
            app.logger.error(f"用户 ID {user_id} 在会话或数据库中未找到。")
            return jsonify({"message": "当前会话用户异常"}), 500
        username_in_session = user.username
    
    original_filename = file_storage.filename

    try:
        original_image_bytes_io = io.BytesIO(file_storage.read())
        original_content_type = file_storage.content_type
        if not original_content_type or not original_content_type.startswith("image/"):
            app.logger.warning(f"上传文件的 Content-Type 无效: {original_content_type}")
            return jsonify({"message": "上传的文件似乎不是有效的图片格式"}), 400

        original_oss_key = _generate_oss_key(user_id, original_filename, type_prefix="original_")
        original_image_bytes_io.seek(0)
        original_oss_url = _upload_to_oss_and_get_url(bucket, original_oss_key, original_image_bytes_io, original_content_type)
        if not original_oss_url:
            app.logger.error("上传原始图片到OSS失败。")
            return jsonify({"message": "上传原始图片到OSS失败"}), 500

        original_image_bytes_io.seek(0)
        current_ascii_options = DEFAULT_ASCII_OPTIONS.copy()
        current_ascii_options.update(ascii_options_from_form)
        app.logger.info(f"开始ASCII转换，选项: {current_ascii_options}")
        pil_ascii_art_image = convert_image_to_ascii_art(original_image_bytes_io, options=current_ascii_options)

        if pil_ascii_art_image is None:
            app.logger.error("图片转换为ASCII艺术画失败 (convert_image_to_ascii_art 返回 None)。")
            return jsonify({"message": "图片转换为ASCII艺术画失败，请检查图片或服务器日志"}), 500

        processed_ascii_image_bytes_io = io.BytesIO()
        output_format_for_ascii = 'PNG'
        pil_ascii_art_image.save(processed_ascii_image_bytes_io, format=output_format_for_ascii)
        processed_ascii_content_type = f'image/{output_format_for_ascii.lower()}'
        processed_ascii_image_bytes_io.seek(0)

        base, ext = os.path.splitext(original_filename)
        ascii_art_filename = f"{base}_ascii.{output_format_for_ascii.lower()}"
        processed_ascii_oss_key = _generate_oss_key(user_id, ascii_art_filename, type_prefix="processed_ascii_")
        
        processed_ascii_oss_url = _upload_to_oss_and_get_url(bucket, processed_ascii_oss_key, processed_ascii_image_bytes_io, processed_ascii_content_type)
        if not processed_ascii_oss_url:
            app.logger.error("上传处理后的ASCII图片到OSS失败。")
            return jsonify({"message": "上传处理后的ASCII图片到OSS失败"}), 500

        new_process_log = UserImageProcess(
            user_id=user_id,
            username=username_in_session,
            input_oss_url=original_oss_url,
            input_token=token_from_form,
            output_oss_url=processed_ascii_oss_url
        )
        db.session.add(new_process_log)
        db.session.commit()

        app.logger.info(f"图片成功转换为ASCII艺术画并记录。日志ID: {new_process_log.id}")
        return jsonify({
            "message": "图片处理、上传并记录成功",
            "log_entry_id": new_process_log.id,
            "original_image_url": original_oss_url,
            "processed_image_url": processed_ascii_oss_url,
            "token": token_from_form,
            "details": new_process_log.to_dict()
        }), 201

    except oss2.exceptions.OssError as oe:
        db.session.rollback()
        app.logger.error(f"OSS 操作失败: {oe}", exc_info=True)
        return jsonify({"message": f"OSS 操作失败: {str(oe)}"}), 500
    except FileNotFoundError as fnfe:
        db.session.rollback()
        app.logger.error(f"处理所需文件未找到: {fnfe}", exc_info=True)
        return jsonify({"message": f"服务配置错误，缺少处理所需文件: {str(fnfe)}"}), 503
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"图片处理和记录过程中发生未知错误: {e}", exc_info=True)
        return jsonify({"message": f"处理图片过程中发生未知错误: {str(e)}"}), 500

# 获取图片处理记录
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

# 视频处理路由
@app.route('/log_video_process', methods=['POST'])
@login_required
def log_video_process():
    if not bucket:
        app.logger.error("OSS 服务未配置或配置错误，无法处理视频。")
        return jsonify({"message": "OSS 服务未配置或配置错误"}), 503

    if 'file' not in request.files:
        app.logger.warning("请求中未包含视频文件 (字段名应为 'file')")
        return jsonify({"message": "请求中未包含视频文件 (字段名应为 'file')"}), 400
    
    file_storage = request.files['file']
    if file_storage.filename == '':
        app.logger.warning("未选择任何视频文件")
        return jsonify({"message": "未选择任何视频文件"}), 400

    token_from_form = request.form.get('token')
    video_options_from_form = {}
    if request.form.get('num_cols'):
        try:
            num_cols_val = int(request.form.get('num_cols'))
            if 10 <= num_cols_val <= 1000:
                video_options_from_form['num_cols'] = num_cols_val
            else:
                app.logger.warning("提供的 num_cols 值无效或超出范围，使用默认值 100。")
                video_options_from_form['num_cols'] = 100
        except ValueError:
            app.logger.warning("提供的 num_cols 不是有效整数，使用默认值 100。")
            video_options_from_form['num_cols'] = 100
    if request.form.get('background') in ['black', 'white']:
        video_options_from_form['background'] = request.form.get('background')
    if request.form.get('mode') in ['simple', 'complex']:
        video_options_from_form['mode'] = request.form.get('mode')
    if request.form.get('scale'):
        try:
            scale_val = int(request.form.get('scale'))
            if 1 <= scale_val <= 10:
                video_options_from_form['scale'] = scale_val
            else:
                app.logger.warning("提供的 scale 值无效，使用默认值 1。")
                video_options_from_form['scale'] = 1
        except ValueError:
            app.logger.warning("提供的 scale 不是有效整数，使用默认值 1。")
            video_options_from_form['scale'] = 1
    if request.form.get('fps'):
        try:
            fps_val = int(request.form.get('fps'))
            if 0 <= fps_val <= 60:
                video_options_from_form['fps'] = fps_val
            else:
                app.logger.warning("提供的 fps 值无效，使用默认值 0。")
                video_options_from_form['fps'] = 0
        except ValueError:
            app.logger.warning("提供的 fps 不是有效整数，使用默认值 0。")
            video_options_from_form['fps'] = 0
    if request.form.get('overlay_ratio'):
        try:
            overlay_ratio_val = float(request.form.get('overlay_ratio'))
            if 0 <= overlay_ratio_val <= 1:
                video_options_from_form['overlay_ratio'] = overlay_ratio_val
            else:
                app.logger.warning("提供的 overlay_ratio 值无效，使用默认值 0.2。")
                video_options_from_form['overlay_ratio'] = 0.2
        except ValueError:
            app.logger.warning("提供的 overlay_ratio 不是有效浮点数，使用默认值 0.2。")
            video_options_from_form['overlay_ratio'] = 0.2

    user_id = session['user_id']
    username_in_session = session.get('username')
    if not username_in_session:
        user = User.query.get(user_id)
        if not user:
            app.logger.error(f"用户 ID {user_id} 在会话或数据库中未找到。")
            return jsonify({"message": "当前会话用户异常"}), 500
        username_in_session = user.username
    
    original_filename = file_storage.filename

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_filename)[1]) as temp_input:
            file_storage.save(temp_input)
            temp_input_path = temp_input.name

        original_content_type = file_storage.content_type
        if not original_content_type or not original_content_type.startswith("video/"):
            os.unlink(temp_input_path)
            app.logger.warning(f"上传文件的 Content-Type 无效: {original_content_type}")
            return jsonify({"message": "上传的文件似乎不是有效的视频格式"}), 400

        original_oss_key = _generate_oss_key(user_id, original_filename, type_prefix="original_", is_video=True)
        with open(temp_input_path, 'rb') as video_file:
            original_oss_url = _upload_to_oss_and_get_url(bucket, original_oss_key, video_file, original_content_type)
        if not original_oss_url:
            os.unlink(temp_input_path)
            app.logger.error("上传原始视频到OSS失败。")
            return jsonify({"message": "上传原始视频到OSS失败"}), 500

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_output:
            temp_output_path = temp_output.name

        video_options = {
            'input': temp_input_path,
            'output': temp_output_path,
            'mode': video_options_from_form.get('mode', 'simple'),
            'background': video_options_from_form.get('background', 'black'),
            'num_cols': video_options_from_form.get('num_cols', 100),
            'scale': video_options_from_form.get('scale', 1),
            'fps': video_options_from_form.get('fps', 0),
            'overlay_ratio': video_options_from_form.get('overlay_ratio', 0.2),
            'codec': 'mp4v'
        }
        args = argparse.Namespace(**video_options)

        app.logger.info(f"开始视频处理，选项: {video_options}")
        if video_options['mode'] == 'complex':
            video2video_color_main(args)
        else:
            video2video_main(args)

        base, ext = os.path.splitext(original_filename)
        ascii_video_filename = f"{base}_ascii.mp4"
        processed_oss_key = _generate_oss_key(user_id, ascii_video_filename, type_prefix="processed_ascii_", is_video=True)
        with open(temp_output_path, 'rb') as processed_file:
            processed_oss_url = _upload_to_oss_and_get_url(bucket, processed_oss_key, processed_file, 'video/mp4')
        
        os.unlink(temp_input_path)
        os.unlink(temp_output_path)

        if not processed_oss_url:
            app.logger.error("上传处理后的ASCII视频到OSS失败。")
            return jsonify({"message": "上传处理后的ASCII视频到OSS失败"}), 500

        new_process_log = UserVideoProcess(
            user_id=user_id,
            username=username_in_session,
            input_oss_url=original_oss_url,
            input_token=token_from_form,
            output_oss_url=processed_oss_url
        )
        db.session.add(new_process_log)
        db.session.commit()

        app.logger.info(f"视频成功转换为ASCII艺术并记录。日志ID: {new_process_log.id}")
        return jsonify({
            "message": "视频处理、上传并记录成功",
            "log_entry_id": new_process_log.id,
            "original_video_url": original_oss_url,
            "processed_video_url": processed_oss_url,
            "token": token_from_form,
            "details": new_process_log.to_dict()
        }), 201

    except oss2.exceptions.OssError as oe:
        db.session.rollback()
        app.logger.error(f"OSS 操作失败: {oe}", exc_info=True)
        return jsonify({"message": f"OSS 操作失败: {str(oe)}"}), 500
    except FileNotFoundError as fnfe:
        db.session.rollback()
        app.logger.error(f"处理所需文件未找到: {fnfe}", exc_info=True)
        return jsonify({"message": f"服务配置错误，缺少处理所需文件: {str(fnfe)}"}), 503
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"视频处理和记录过程中发生未知错误: {e}", exc_info=True)
        return jsonify({"message": f"处理视频过程中发生未知错误: {str(e)}"}), 500
    

@app.route('/video_process_logs', methods=['GET'])
@login_required
def get_video_process_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    user_id = session['user_id']
    logs = UserVideoProcess.query.filter_by(user_id=user_id).order_by(UserVideoProcess.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    logs_data = [{
        "id": log.id,
        "user_id": log.user_id,
        "username": session['username'],
        "input_oss_url": log.input_oss_url,
        "input_token": log.input_token,
        "output_oss_url": log.output_oss_url,
        "created_at": log.created_at.isoformat(),
        "updated_at": log.updated_at.isoformat()
    } for log in logs.items]
    response = {
        "message": "成功获取视频处理记录",
        "logs": logs_data,
        "total_logs": logs.total,
        "current_page": logs.page,
        "total_pages": logs.pages,
        "per_page": per_page
    }
    return jsonify(response), 200

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
        api_key = os.environ.get('DASHSCOPE_API_KEY')
        if not api_key:
            return jsonify({"message": "DashScope API密钥未配置"}), 500
        
        creation_result = generate_image(prompt, api_key)
        task_id = creation_result["output"]["task_id"]
        
        while True:
            status_result = check_task_status(task_id, api_key)
            task_status = status_result["output"]["task_status"]
            
            if task_status == "SUCCEEDED":
                break
            elif task_status in ["FAILED", "CANCELED"]:
                raise Exception(f"任务失败，状态: {task_status}")
            
            time.sleep(5)
        
        image_url = status_result["output"]["results"][0]["url"]
        response = requests.get(image_url)
        if response.status_code != 200:
            raise Exception(f"图片下载失败: {response.status_code}")
        
        image_data = io.BytesIO(response.content)
        image_data.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        oss_key = f"generated_images/user_{user_id}/{timestamp}_generated.jpg"
        
        oss_url = _upload_to_oss_and_get_url(bucket, oss_key, image_data, 'image/jpeg')
        
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

# 获取文生图记录
@app.route('/text_to_image_logs', methods=['GET'])
@login_required
def get_text_to_image_logs():
    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    logs_pagination = TextToImageGeneration.query.filter_by(user_id=user_id)\
        .order_by(TextToImageGeneration.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    logs_data = [log.to_dict() for log in logs_pagination.items]
    return jsonify({
        "message": "成功获取文字生成图片记录",
        "data": logs_data,
        "pagination": {
            "total": logs_pagination.total,
            "pages": logs_pagination.pages,
            "current_page": logs_pagination.page,
            "per_page": logs_pagination.per_page,
            "has_next": logs_pagination.has_next,
            "has_prev": logs_pagination.has_prev
        }
    }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    if not auth or not bucket:
        print("="*50)
        print("警告: 阿里云 OSS 未正确配置或配置不完整。")
        print("图片和视频上传功能及依赖OSS的处理记录功能可能无法正常工作。")
        print("请检查环境变量: OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET_NAME, OSS_ENDPOINT")
        print("="*50)
    else:
        print("阿里云 OSS 配置加载成功。")
        
    app.run(debug=True, port=8088)