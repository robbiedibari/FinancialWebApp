from flask_sqlalchemy import SQLAlchemy 
from flask_login import UserMixin
from datetime import datetime 

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    monthly_budget = db.Column(db.Float, default=0.0)
    expenses = db.relationship('Expense', backref = 'user', lazy = True)
    categories = db.relationship('Category',backref = 'user', lazy = True)
    savings_goal = db.Column(db.Float, default = 0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    


class Category(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    budget = db.Column(db.Float, default= 0.0)
    color = db.Column(db.String(7), default = "#000000")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expenses = db.relationship('Expense', backref = 'category_rel', lazy=True)
    

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_frequency = db.Column(db.String(20), nullable=True)  # 'weekly', 'monthly', 'yearly'

