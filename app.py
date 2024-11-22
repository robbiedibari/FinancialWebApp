from flask import Flask, render_template, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, TelField, validators
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import os


# Define your User model outside of create_app
db = SQLAlchemy()  # Define SQLAlchemy instance here
bcrypt = Bcrypt()


def create_app():
    app = Flask(__name__)
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SECRET_KEY'] = 'secretpassword'
    db.init_app(app)  # Initialize db with app
    bcrypt.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Define routes within the create_app function
    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                flash('Login successful', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Login unsuccessful, Please check your username and passoword')
        return render_template('login.html', form=form)

    @app.route('/dashboard', methods=['GET', 'POST'])
    @login_required
    def dashboard():
        username = current_user.username.capitalize()
        return render_template('dashboard.html', username=username)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        form = RegistrationForm()
        if form.validate_on_submit():
            print('Form Submitted Successfully')
            try:
                hashed_password = bcrypt.generate_password_hash(
                    form.password.data).decode('utf-8')
                new_user = User(
                    username=form.username.data,
                    email=form.email.data,
                    password=hashed_password,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                )
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                flash('Your account has been created!', 'success')
                return redirect(url_for('dashboard'))

            except Exception as e:
                db.session.rollback()
                flash(
                    'An error occurred during registration. Please try again.', 'danger')
                print(f"Error: {e}")
        else:
            print('Form did not validate!')
        return render_template('register.html', form=form)

    return app


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(20), nullable=False, unique=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)


class RegistrationForm(FlaskForm):
    username = StringField(
        'Username', [validators.DataRequired(), validators.Length(min=4, max=25)])
    email = EmailField(
        'Email', [validators.DataRequired(), validators.Email()])
    password = PasswordField(
        'Password', [validators.DataRequired(), validators.Length(min=6)])
    confirm_password = PasswordField('Confirm Password', [validators.DataRequired(
    ), validators.EqualTo('password', message='Passwords must match')])
    first_name = StringField('First Name', [validators.DataRequired()])
    last_name = StringField('Last Name', [validators.DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, email):
        existing_user_email = User.query.filter_by(email=email.data).first()
        if existing_user_email:
            raise ValidationError(
                'Email already exists. Please Choose a different one.'
            )


class LoginForm(FlaskForm):
    email = EmailField(
        'Email', 
        validators=[InputRequired(), Length(max=50), validators.Email()],
        render_kw={'placeholder': 'Email'}
    )
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={'placeholder': 'password'})
  
    submit = SubmitField('Login Now')


if __name__ == '__main__':
    app = create_app()
    app.run(port=5001, debug=True)
