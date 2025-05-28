from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_default_secret_key_change_this')

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '20050309syw',
    'database': 'triblog'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"数据库连接错误: {err}")
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录以访问此页面。', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# (其他路由保持不变：index, register, login, create_post, logout, profile, my_posts, edit_post, delete_post)

@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('welcome.html')

    db = get_db_connection()
    posts = []
    if db is None:
        flash("数据库连接失败，请稍后重试。", "danger")
        return render_template('index.html', posts=posts, active_page='index', current_user_id=session.get('user_id'))

    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT bp.*, u.username AS author_username
            FROM BlogPostModel bp
            JOIN UserModel u ON bp.user_id = u.id
            ORDER BY bp.created_at DESC
        """)
        posts = cursor.fetchall()
    except mysql.connector.Error as err:
        flash("加载文章失败，请稍后重试。", "danger")
        posts = []
    finally:
        if cursor: cursor.close()
        if db: db.close()

    return render_template('index.html', posts=posts, active_page='index', current_user_id=session.get('user_id'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    form_data = request.form if request.method == 'POST' else {}

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        phone = request.form.get('phone')
        bio = request.form.get('bio')
        region = request.form.get('region')

        avatar_file = request.files.get('avatar')
        avatar_path = None
        if avatar_file and allowed_file(avatar_file.filename):
            filename = secure_filename(avatar_file.filename)
            avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            avatar_file.save(avatar_path)
            avatar_path = avatar_path.replace('\\', '/')
        else:
            avatar_path = None

        if not username or not password or not email:
            flash("用户名、密码和邮箱为必填项。", "warning")
            return render_template('register.html', form_data=form_data), 400
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            flash("邮箱格式不正确。", "warning")
            return render_template('register.html', form_data=form_data), 400
        if phone and not re.match(r'^\d{7,20}$', phone):
            flash("手机号格式不正确。", "warning")
            return render_template('register.html', form_data=form_data), 400

        hashed_password = generate_password_hash(password)

        db = get_db_connection()
        if db is None:
            flash("数据库连接失败，请稍后重试。", "danger")
            return render_template('error.html', message="无法连接到数据库。"), 500

        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id FROM UserModel WHERE username = %s", (username,))
            if cursor.fetchone():
                flash(f"用户名 '{username}' 已存在，请尝试其他用户名。", "warning")
                return render_template('register.html', form_data=form_data), 409

            cursor.execute("SELECT id FROM UserModel WHERE email = %s", (email,))
            if cursor.fetchone():
                flash(f"邮箱 '{email}' 已被注册，请尝试其他邮箱或直接登录。", "warning")
                return render_template('register.html', form_data=form_data), 409

            sql = """
                  INSERT INTO UserModel (username, password, email, phone, bio, avatar, region)
                  VALUES (%s, %s, %s, %s, %s, %s, %s)
                  """
            values = (username, hashed_password, email, phone, bio, avatar_path, region)
            cursor.execute(sql, values)
            db.commit()

            flash("注册成功，请登录。", "success")
            return redirect(url_for('login'))

        except mysql.connector.Error as err:
            db.rollback()
            print(f"注册用户失败: {err}")
            flash("注册失败，请稍后重试或联系管理员。", "danger")
            return render_template('register.html', form_data=form_data), 500
        finally:
            if cursor: cursor.close()
            if db: db.close()

    return render_template('register.html', form_data={})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("请输入用户名和密码。", "warning")
            return render_template('login.html'), 400

        db = get_db_connection()
        if db is None:
            flash("数据库连接失败，请稍后重试。", "danger")
            return render_template('error.html', message="无法连接到数据库。"), 500

        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, username, password FROM UserModel WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash(f"欢迎回来, {user['username']}!", "success")
                return redirect(url_for('index'))
            else:
                flash('登录失败，请检查用户名和密码。', "danger")
                return render_template('login.html'), 401

        except mysql.connector.Error as err:
            print(f"登录失败: {err}")
            flash("登录过程中发生错误，请稍后重试。", "danger")
            return render_template('login.html'), 500
        finally:
            if cursor: cursor.close()
            if db: db.close()

    return render_template('login.html')

@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    user_id = session.get('user_id')

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        if not title or not content:
            flash("标题和内容不能为空。", "warning")
            return render_template('create_post.html', active_page='create_post'), 400

        db = get_db_connection()
        if db is None:
            flash("数据库连接失败，请稍后重试。", "danger")
            return render_template('error.html', message="无法连接到数据库。"), 500

        cursor = db.cursor()
        try:
            sql = "INSERT INTO BlogPostModel (user_id, title, content) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_id, title, content))
            db.commit()
            flash("文章发布成功！", "success")
            return redirect(url_for('index'))
        except mysql.connector.Error as err:
            db.rollback()
            print(f"创建文章失败: {err}")
            flash("发布文章失败，请稍后重试。", "danger")
            return render_template('create_post.html', active_page='create_post'), 500
        finally:
            if cursor: cursor.close()
            if db: db.close()

    return render_template('create_post.html', active_page='create_post')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash("您已成功登出。", "info")
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    user_id = session.get('user_id')

    db = get_db_connection()
    user_info = None
    if db:
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT username, email, phone, bio, avatar, region, created_at FROM UserModel WHERE id = %s", (user_id,))
            user_info = cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"查询用户信息失败: {err}")
            flash("加载用户信息失败。", "danger")
        finally:
            if cursor: cursor.close()
            if db: db.close()
    else:
         flash("数据库连接失败，无法加载用户信息。", "danger")

    return render_template('profile.html', active_page='profile', user_info=user_info)

@app.route('/my_posts')
@login_required
def my_posts():
    user_id = session.get('user_id')

    db = get_db_connection()
    my_articles = []
    if db:
        cursor = db.cursor(dictionary=True)
        try:
             sql = """
                   SELECT bp.id, bp.title, bp.content, bp.created_at, bp.user_id, um.username as author_username
                   FROM BlogPostModel bp
                            JOIN UserModel um ON bp.user_id = um.id
                   WHERE bp.user_id = %s
                   ORDER BY bp.created_at DESC
                   """
             cursor.execute(sql, (user_id,))
             my_articles = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"查询我的文章失败: {err}")
            flash("加载我的文章失败。", "danger")
        finally:
            if cursor: cursor.close()
            if db: db.close()
    else:
        flash("数据库连接失败，无法加载我的文章。", "danger")

    return render_template('my_posts.html', active_page='my_posts', posts=my_articles, current_user_id=user_id)

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    user_id = session.get('user_id')

    db = get_db_connection()
    if db is None:
        flash("数据库连接失败，请稍后重试。", "danger")
        return render_template('error.html', message="无法连接到数据库。"), 500

    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, title, content, user_id FROM BlogPostModel WHERE id = %s", (post_id,))
        post = cursor.fetchone()

        if post is None:
            flash("文章不存在。", "danger")
            return redirect(url_for('index'))
        if post['user_id'] != user_id:
            flash("您无权编辑此文章。", "danger")
            return redirect(url_for('index'))

        if request.method == 'POST':
            title = request.form.get('title')
            content = request.form.get('content')

            if not title or not content:
                flash("标题和内容不能为空。", "warning")
                return render_template('edit_post.html', post=post, active_page='my_posts'), 400

            sql = "UPDATE BlogPostModel SET title = %s, content = %s WHERE id = %s AND user_id = %s"
            cursor.execute(sql, (title, content, post_id, user_id))
            db.commit()

            flash("文章更新成功！", "success")
            return redirect(url_for('post_detail', post_id=post_id))

        return render_template('edit_post.html', post=post, active_page='my_posts')

    except mysql.connector.Error as err:
        db.rollback()
        print(f"编辑文章失败 (ID: {post_id}): {err}")
        flash("编辑文章失败，请稍后重试。", "danger")
        return redirect(url_for('my_posts'))
    finally:
        if cursor: cursor.close()
        if db: db.close()

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    user_id = session.get('user_id')

    db = get_db_connection()
    if db is None:
        flash("数据库连接失败，请稍后重试。", "danger")
        return redirect(url_for('index'))

    cursor = db.cursor()
    try:
        sql = "DELETE FROM BlogPostModel WHERE id = %s AND user_id = %s"
        cursor.execute(sql, (post_id, user_id))
        db.commit()

        if cursor.rowcount == 0:
             flash("文章不存在或您无权删除此文章。", "danger")
        else:
             flash("文章删除成功！", "success")

    except mysql.connector.Error as err:
        db.rollback()
        print(f"删除文章失败 (ID: {post_id}): {err}")
        flash("删除文章失败，请稍后重试。", "danger")
    finally:
        if cursor: cursor.close()
        if db: db.close()

    return redirect(url_for('my_posts'))

# --- 修改后的文章详情和评论路由 ---
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    db = get_db_connection()
    if db is None:
        flash("数据库连接失败，请稍后重试。", "danger")
        return render_template('error.html', message="无法连接到数据库。"), 500

    cursor = db.cursor(dictionary=True)

    try:
        # 获取文章详情
        cursor.execute("""
            SELECT bp.id, bp.title, bp.content, bp.created_at, bp.user_id, um.username as author_username
            FROM BlogPostModel bp
            JOIN UserModel um ON bp.user_id = um.id
            WHERE bp.id = %s
        """, (post_id,))
        post = cursor.fetchone()

        if post is None:
            flash("文章不存在。", "danger")
            abort(404)

        # 获取该文章的所有评论，并带上评论者的用户名
        cursor.execute("""
            SELECT c.id, c.content, c.created_at, um.username as commenter_username
            FROM CommentModel c
            JOIN UserModel um ON c.user_id = um.id
            WHERE c.post_id = %s
            ORDER BY c.created_at ASC
        """, (post_id,))
        comments = cursor.fetchall()

        # 处理评论提交 (POST 请求)
        if request.method == 'POST':
            if 'user_id' not in session:
                 flash("请先登录才能发表评论。", "warning")
                 return redirect(url_for('post_detail', post_id=post_id))

            comment_content = request.form.get('comment_content')
            user_id = session.get('user_id')

            if not comment_content:
                flash("评论内容不能为空。", "warning")
            else:
                try:
                    comment_cursor = db.cursor()
                    sql = "INSERT INTO CommentModel (post_id, user_id, content) VALUES (%s, %s, %s)"
                    comment_cursor.execute(sql, (post_id, user_id, comment_content))
                    db.commit()
                    flash("评论发表成功！", "success")
                    return redirect(url_for('post_detail', post_id=post_id))
                except mysql.connector.Error as err:
                    db.rollback()
                    print(f"发表评论失败: {err}")
                    flash("发表评论失败，请稍后重试。", "danger")
                finally:
                     if comment_cursor: comment_cursor.close()

        # 检查是否已收藏
        is_favorited = False
        if 'user_id' in session:
          # 使用主查询游标来执行此查询
          cursor.execute("SELECT id FROM FavoriteModel WHERE user_id=%s AND post_id=%s", (session['user_id'], post_id))
          is_favorited = cursor.fetchone() is not None

        return render_template('post_detail.html',
                               post=post,
                               comments=comments,
                               active_page='index',
                               current_user_id=session.get('user_id'),
                               is_favorited=is_favorited) # 传递收藏状态

    except mysql.connector.Error as err:
        print(f"加载文章详情或评论失败 (ID: {post_id}): {err}")
        flash("加载文章详情失败，请稍后重试。", "danger")
        return render_template('error.html', message="加载文章详情时发生错误。"), 500
    finally:
        if cursor: cursor.close()
        if db: db.close()

UPLOAD_FOLDER = 'static/uploads/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user_id = session.get('user_id')
    db = get_db_connection()
    if db is None:
        flash("数据库连接失败，请稍后重试。", "danger")
        return render_template('error.html', message="无法连接到数据库。"), 500

    cursor = db.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            email = request.form.get('email') or None
            phone = request.form.get('phone') or None
            bio = request.form.get('bio') or None
            region = request.form.get('region') or None

            avatar_file = request.files.get('avatar')
            avatar_path = None
            if avatar_file and avatar_file.filename:
                filename = secure_filename(avatar_file.filename)
                upload_folder = app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                avatar_path = os.path.join(upload_folder, filename)
                if os.path.exists(avatar_path):
                    flash("文件已存在，请重命名后再上传。", "warning")
                    return redirect(url_for('edit_profile'))
                avatar_file.save(avatar_path)
                avatar_path = avatar_path.replace('\\', '/')

            if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                flash("邮箱格式不正确。", "warning")
                return redirect(url_for('edit_profile'))
            if phone and not re.match(r'^\d{7,20}$', phone):
                flash("手机号格式不正确。", "warning")
                return redirect(url_for('edit_profile'))

            sql = """
                UPDATE UserModel
                SET email=%s, phone=%s, bio=%s, region=%s {avatar_sql}
                WHERE id=%s
            """
            avatar_sql = ", avatar=%s" if avatar_path else ""
            sql = sql.format(avatar_sql=avatar_sql)
            values = [email, phone, bio, region]
            if avatar_path:
                values.append(avatar_path)
            values.append(user_id)
            cursor.execute(sql, tuple(values))
            db.commit()
            flash("个人信息已更新。", "success")
            return redirect(url_for('profile'))

        cursor.execute("SELECT username, email, phone, bio, avatar, region FROM UserModel WHERE id=%s", (user_id,))
        user_info = cursor.fetchone()
        return render_template('edit_profile.html', user_info=user_info, active_page='profile')
    except mysql.connector.Error as err:
        db.rollback()
        flash("更新个人信息失败，请稍后重试。", "danger")
        return redirect(url_for('profile'))
    finally:
        if cursor: cursor.close()
        if db: db.close()

# --- 新增的“我的收藏”路由 ---
@app.route('/my_favorites')
@login_required
def my_favorites():
    user_id = session.get('user_id')
    db = get_db_connection()
    favorites = []
    if db:
        cursor = db.cursor(dictionary=True)
        try:
            sql = """
                SELECT bp.id, bp.title, bp.content, f.created_at, bp.user_id, u.username as author_username
                FROM FavoriteModel f
                JOIN BlogPostModel bp ON f.post_id = bp.id
                JOIN UserModel u ON bp.user_id = u.id
                WHERE f.user_id = %s
                ORDER BY f.created_at DESC
            """
            cursor.execute(sql, (user_id,))
            favorites = cursor.fetchall()
        except mysql.connector.Error as err:
            flash("加载我的收藏失败，请稍后重试。", "danger")
            print(f"加载收藏失败: {err}")
        finally:
            if cursor: cursor.close()
            if db: db.close()
    else:
        flash("数据库连接失败，无法加载我的收藏。", "danger")
    return render_template('my_favorites.html', posts=favorites, active_page='my_favorites', current_user_id=user_id) # 将 active_page 改为 'my_favorites'

# --- 新增的收藏/取消收藏路由 ---
@app.route('/favorite/<int:post_id>', methods=['POST'])
@login_required
def favorite_post(post_id):
    user_id = session.get('user_id')
    db = get_db_connection()
    if db is None:
        flash("数据库连接失败，请稍后重试。", "danger")
        return redirect(url_for('post_detail', post_id=post_id))

    cursor = db.cursor()
    try:
        # 检查是否已经收藏
        cursor.execute("SELECT id FROM FavoriteModel WHERE user_id = %s AND post_id = %s", (user_id, post_id))
        favorite_entry = cursor.fetchone()

        if favorite_entry:
            # 已收藏，则取消收藏
            cursor.execute("DELETE FROM FavoriteModel WHERE id = %s", (favorite_entry[0],))
            flash("已取消收藏。", "info")
        else:
            # 未收藏，则添加收藏
            cursor.execute("INSERT INTO FavoriteModel (user_id, post_id) VALUES (%s, %s)", (user_id, post_id))
            flash("收藏成功！", "success")
        db.commit()

    except mysql.connector.Error as err:
        db.rollback()
        print(f"收藏/取消收藏操作失败: {err}")
        flash("操作失败，请稍后重试。", "danger")
    finally:
        if cursor: cursor.close()
        if db: db.close()

    return redirect(url_for('post_detail', post_id=post_id))


if __name__ == '__main__':
    if not os.path.exists('static/uploads/avatars'):
        os.makedirs('static/uploads/avatars')
    if not os.path.exists('static/images'):
        os.makedirs('static/images')
    app.run(debug=True, port=5003)

