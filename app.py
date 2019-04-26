# coding=utf-8
import os
from flask import Flask, render_template, session, redirect, \
    url_for, flash, current_app, request
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, LoginManager, login_required, \
    login_user, logout_user, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, SubmitField, SelectField, \
    BooleanField, IntegerField, ValidationError
from wtforms.validators import Required, Length, Regexp
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from functions import get_face_encoding_in_image

'''
Config
'''
basedir = os.path.abspath(os.path.dirname(__file__))


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['AdminPassword'] = 000000
app.config['SECRET_KEY'] = "this is a secret_key"
db = SQLAlchemy(app)
manager = Manager(app)
bootstrap = Bootstrap(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)
manager.add_command('shell', Shell(make_shell_context))
login_manager = LoginManager(app)

login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.login_message = u"你需要登录才能访问这个页面."

'''
Models
'''


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = ('Student', 'Admin')
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.SmallInteger, unique=True, index=True)
    username = db.Column(db.String(64), index=True)
    password = db.Column(db.String(128), default=123456)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    face_encoding = db.Column(db.String(128), index=True)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # 新添加的用户，初始其角色为学生。
        if self.role is None:
            self.role = Role.query.filter_by(name='Student').first()

    def __repr__(self):
        return '<User %r>' % self.username

    # 初次运行程序时生成初始管理员的静态方法
    @staticmethod
    def generate_admin():
        admin = Role.query.filter_by(name='Admin').first()
        u = User.query.filter_by(role=admin).first()
        if u is None:
            u = User(number=000000, username='Admin', \
                     password=current_app.config['AdminPassword'], \
                     role=Role.query.filter_by(name='Admin').first())
            db.session.add(u)
        db.session.commit()

    def verify_password(self, password):
        return self.password == password


'''
Forms
'''


class LoginForm(FlaskForm):
    number = StringField(u'学号', validators=[Required()])
    password = PasswordField(u'密码', validators=[Required()])
    remember_me = BooleanField(u'记住我')
    submit = SubmitField(u'登录')


class SearchForm(FlaskForm):
    number = IntegerField(u'学号', validators=[Required(message=u'请输入数字')])
    submit = SubmitField(u'搜索')


class UserForm(FlaskForm):
    username = StringField(u'姓名', validators=[Required()])
    number = IntegerField(u'学号', validators=[Required(message=u'请输入数字')])
    file = FileField('面部照片')
    submit = SubmitField(u'添加')

    def validate_number(self, field):
        if User.query.filter_by(number=field.data).first():
            raise ValidationError(u'此学生已存在，请检查学号！')


class EditForm(FlaskForm):
    username = StringField(u'姓名', validators=[Required()])
    number = IntegerField(u'学号', validators=[Required(message=u'请输入数字')])
    password = StringField(u'密码', validators=[Required(), Length(1, 64), \
                                              Regexp('^[a-zA-Z0-9_.]*$', 0, \
                                                     u'密码由字母、数字和_.组成')])
    role = SelectField(u'身份', coerce=int)
    submit = SubmitField(u'修改')

    def __init__(self, user, *args, **kargs):
        super(EditForm, self).__init__(*args, **kargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_number(self, field):
        if field.data != self.user.number and \
                User.query.filter_by(number=field.data).first():
            raise ValidationError(u'此学生已存在，请检查学号！')


'''
views
'''


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = SearchForm()
    admin = Role.query.filter_by(name='Admin').first()
    if form.validate_on_submit():
        # 获得学生列表，其学号包含form中的数字
        students = User.query.filter(User.number.like \
                                         ('%{}%'.format(form.number.data))).all()
    else:
        students = User.query.order_by(User.role_id.desc(), User.number.asc()).all()
    return render_template('index.html', form=form, students=students, admin=admin)


# 增加新学生
@app.route('/add-user', methods=['GET', 'POST'])
@login_required
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        filename = secure_filename(form.file.data.filename)
        # print(form.username.data)
        # print(form.file.data)
        # < FileStorage: 'wangkang.jpeg'('image/jpeg') >
        try:
            result = get_face_encoding_in_image(form.file.data)
        except OSError:
            flash(u'文件格式有误')
            print(OSError)
            return render_template('add_user.html', form=form)
        if result["face_found_in_image"] == False:
            flash(u'未检测到人脸，添加失败！')
            return render_template('add_user.html', form=form)
        else:
            user = User(username=form.username.data,
                        number=form.number.data,
                        face_encoding=result["unknown_face_encodings"])
            db.session.add(user)
            flash(u'成功添加学生')
            return redirect(url_for('index'))
    return render_template('add_user.html', form=form)


# 删除学生
@app.route('/remove-user/<int:id>', methods=['GET', 'POST'])
@login_required
def remove_user(id):
    user = User.query.get_or_404(id)
    if user.role == Role.query.filter_by(name='Admin').first():
        flash(u'不能删除管理员')
    else:
        db.session.delete(user)
        flash(u'成功删除此学生')
    return redirect(url_for('index'))


# 修改学生资料
@app.route('/edit-user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = EditForm(user=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.number = form.number.data
        user.password = form.password.data
        user.role = Role.query.get(form.role.data)
        db.session.add(user)
        flash(u'个人信息已更改')
        return redirect(url_for('index'))
    form.username.data = user.username
    form.number.data = user.number
    form.password.data = user.password
    form.role.data = user.role_id
    return render_template('edit_user.html', form=form, user=user)


# 登录，系统只允许管理员登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(number=form.number.data).first()
        if user is not None and user.verify_password(form.password.data):
            if user.role != Role.query.filter_by(name='Admin').first():
                flash(u'系统只对管理员开放，请联系管理员获得权限！')
            else:
                login_user(user, form.remember_me.data)
                return redirect(url_for('index'))
        flash(u'用户名或密码错误！')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'成功注销！')
    return redirect(url_for('login'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# 加载用户的回调函数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


'''
增加命令'python app.py init' 
以增加身份与初始管理员帐号
'''


@manager.command
def init():
    from app import Role, User
    Role.insert_roles()
    User.generate_admin()


if __name__ == '__main__':
    manager.run()
