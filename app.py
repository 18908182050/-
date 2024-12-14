from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Favorite
from config import Config
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/')
def home():
    user_id = session.get('user_id')  # 获取当前用户的ID
    user = User.query.get(user_id) if user_id else None
    return render_template('home.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('登录成功！')
            return redirect(url_for('home'))
        else:
            flash('账号或密码错误.')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 输入验证：检查用户名和密码的长度
        if len(username) < 3:
            flash('用户名需要至少3个字符.')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('密码需要至少6个字符.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)

        # 尝试添加用户到数据库
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功，现在你可以登录了.')
            return redirect(url_for('login'))
        except IntegrityError:  # 捕获用户名已存在的异常
            db.session.rollback()  # 回滚数据库操作
            flash('用户名已被占用，请选择其他用户名.')

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('你已经退出登录.')
    return redirect(url_for('home'))


@app.route('/user', methods=['GET', 'POST'])
def user():
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if not user:
        flash('请先登录.')
        return redirect(url_for('login'))

    # 获取用户收藏
    favorites = Favorite.query.filter_by(user_id=user.id).all()

    if request.method == 'POST':
        new_password = request.form['new_password']
        if len(new_password) < 6:
            flash('密码需要至少6个字符.')
        else:
            hashed_password = generate_password_hash(new_password)
            user.password = hashed_password
            db.session.commit()
            flash('密码修改成功.')

    return render_template('user.html', user=user, favorites=favorites)


@app.route('/favorite/<string:anime_title>', methods=['POST'])
def add_favorite(anime_title):
    user_id = session.get('user_id')
    if not user_id:
        flash('请先登录.')
        return redirect(url_for('login'))

    # 假设您有一个字典来存储动漫标题与图片 URL 的映射
    anime_images = {
        '进击的巨人': 'images/jr.jpg',
        '你的名字': 'images/ndmz.jpg',
        '败犬女主': 'images/baiquan.jpg',
        '鬼灭之刃': 'images/gmzr.jpg',
        '咒术回战': 'images/jujutsu.jpg',
        '间谍家家酒': 'images/spy-family.jpg',
        '海贼王': 'images/one-piece.jpg',
        '这个是僵尸吗？': 'images/kono_subarashii.jpg',
        '地狱乐园': 'images/hells_paradise.jpg',
        'Fate/strange Fake': 'images/typemoon.jpg',
        '蓝锁': 'images/blue_lock.jpg',
        '刀剑神域': 'images/djsy.jpg',
    }

    # 检查收藏是否已经存在
    favorite_exist = Favorite.query.filter_by(user_id=user_id, anime_title=anime_title).first()
    if favorite_exist:
        flash('该动漫已经在您的收藏中.')
    else:
        # 从字典中获取对应的图片 URL
        image_url = anime_images.get(anime_title, 'default_image.jpg')  # 默认图片
        new_favorite = Favorite(anime_title=anime_title, user_id=user_id, image_url=image_url)
        db.session.add(new_favorite)
        db.session.commit()
        flash('收藏成功！')

    return redirect(url_for('home'))  # 或者你可以重定向到之前的页面

@app.route('/favorite/remove/<int:fav_id>', methods=['POST'])
def remove_favorite(fav_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('请先登录.')
        return redirect(url_for('login'))

    favorite = Favorite.query.filter_by(id=fav_id, user_id=user_id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        flash('取消收藏成功！')
    else:
        flash('该收藏不存在。')

    return redirect(url_for('user'))  # 返回用户页面



if __name__ == '__main__':
    app.run(debug=True)
