from flask import Flask, render_template, url_for, redirect, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, FloatField, SelectField, DateField, TextAreaField, validators
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired, NumberRange, Email, EqualTo
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from flask_bcrypt import Bcrypt
from utils import import_csv
from models import db, User, Category, Expense
import tempfile
import calendar
import os


# Define your User model outside of create_app
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

    # Define routes
    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('home'))

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
                flash('Login unsuccessful. Please check your username and password.', 'danger')
        return render_template('login.html', form=form)

    # Register
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        form = RegistrationForm()
        if form.validate_on_submit():
            # Check if passwords match
            if form.password.data != form.confirm_password.data:
                flash('Passwords do not match. Please try again.', 'danger')
                return render_template('register.html', form=form)

            # Check if email is already registered
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Email is already registered. Please use a different email or log in.', 'danger')
                return render_template('register.html', form=form)

            try:
            # Create and add the new user to the database
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                new_user = User(
                    email=form.email.data,
                    password=hashed_password,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data
                )
                db.session.add(new_user)
                db.session.commit()

                # Log the user in
                login_user(new_user)

                flash('Registration successful! Welcome to your dashboard.', 'success')
                return redirect(url_for('dashboard'))

            except Exception as e:
            # Rollback the database changes in case of any error
                db.session.rollback()
                app.logger.error(f"Registration error: {e}")  # Log the error for debugging
                flash('An unexpected error occurred during registration. Please try again.', 'danger')

        return render_template('register.html', form=form)
    

    # Dashboard data
    @app.route('/dashboard', methods=['GET', 'POST'])
    @login_required
    def dashboard():
        # Capitalize user's first name for display
        first_name = current_user.first_name.capitalize()

        # Handle statement upload
        if request.method == 'POST':
            file = request.files.get('file')
            if file:
                with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                    file.save(temp_file.name)
                    try:
                        import_csv(temp_file.name, current_user.id)
                        flash('Statement uploaded and processed successfully!', 'success')
                    except Exception as e:
                        flash(f'Error processing the statement: {str(e)}', 'danger')

            # Fetch user's expenses (recent 50 transactions for display)
        expenses = db.session.query(Expense).filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(50).all()

            # Get current month's data
        today = datetime.today()
        start_of_month = datetime(today.year, today.month, 1)
        end_of_month = datetime(today.year, today.month, calendar.monthrange(today.year, today.month)[1])

            # Category breakdown for the current month
        category_expenses = db.session.query(
            Category.name,
            func.sum(Expense.amount).label('total')
        ).join(Expense)\
        .filter(
            Expense.date.between(start_of_month, end_of_month),
            Category.user_id == current_user.id
        )\
        .group_by(Category.id)\
        .all()

            # Calculate the total debit (sum of all positive amounts)
        total_debit = db.session.query(func.sum(Expense.amount))\
            .filter(
                Expense.user_id == current_user.id,
                Expense.amount > 0,
                Expense.date.between(start_of_month, end_of_month)
            )\
            .scalar() or 0.0
        total_debit = round(total_debit, 2)

      
        return render_template(
            'dashboard.html',
            first_name=first_name,
            expenses=expenses,
            category_expenses=category_expenses,
            total_debit=total_debit,
        )



    # Import CSV route 
    @app.route('/import', methods=['GET', 'POST'])
    @login_required
    def import_csv_route():
        if request.method == "POST":
            file = request.files.get('file')
            if not file:
                flash('No file selected!', 'danger')
                return redirect(url_for('dashboard'))

        # Process the file as in the dashboard route
            try:
                with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                    file.save(temp_file.name)
                    import_csv(temp_file.name, current_user.id)
                    flash('Statement imported successfully!', 'success')
            except Exception as e:
                flash(f'Error processing the statement: {str(e)}', 'danger')

        return redirect(url_for('dashboard'))
        

    @app.route('/categories', methods=['GET', 'POST'])
    @login_required
    def categories():
        form = CategoryForm()
        if form.validate_on_submit():
            category = Category(
                name=form.name.data,
                budget=form.budget.data,
                color=form.color.data,
                user_id=current_user.id
            )
            db.session.add(category)
            db.session.commit()
            flash('Category added successfully!', 'success')
            return redirect(url_for('categories'))

        categories = Category.query.filter_by(user_id=current_user.id).all()
        return render_template('categories.html', form=form, categories=categories)

    
    return app


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=50)])
    budget = FloatField('Category Budget', validators=[DataRequired(), NumberRange(min=0)])
    color = StringField('Color', validators=[DataRequired(), Length(min=7, max=7)])
    submit = SubmitField('Add Category')

class ExpenseForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    description = StringField('Description', validators=[DataRequired(), Length(max=100)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    notes = TextAreaField('Notes')
    is_recurring = SelectField('Recurring Expense', choices=[('0', 'No'), ('1', 'Yes')])
    recurring_frequency = SelectField('Frequency', 
                                   choices=[('none', 'None'),
                                          ('weekly', 'Weekly'),
                                          ('monthly', 'Monthly'),
                                          ('yearly', 'Yearly')])
    submit = SubmitField('Add Expense')


class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', [validators.DataRequired()])
    last_name = StringField('Last Name', [validators.DataRequired()])
    email = EmailField(
        'Email', [validators.DataRequired(), validators.Email()])
    password = PasswordField(
        'Password', [validators.DataRequired(), validators.Length(min=6)])
    confirm_password = PasswordField('Confirm Password', [validators.DataRequired(
    ), validators.EqualTo('password', message='Passwords must match')])
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
    with app.app_context():
        db.create_all()  # Creates all tables in the database
    app.run(port=5001, debug=True)