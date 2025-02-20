# models.py

from flask_sqlalchemy import SQLAlchemy

# Create an instance of SQLAlchemy (this manages connections, models, etc.)
db = SQLAlchemy()

class NewsSource(db.Model): # Inheriting the db.Model class from SQLAlchemy
    """
    A table representing each news source (CNN, Fox, etc.)
    """
    __tablename__ = 'news_sources'  # Explicitly name the table in the DB. SQLAlchemy will look for this since we inherited db.Model

    # Primary key: a unique auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True)

    # Name of the source (e.g. 'CNN', 'Fox News')
    name = db.Column(db.String(100), unique=True, nullable=False)

    # Bias score: from -10 (most liberal) to +10 (most conservative)
    bias_score = db.Column(db.Integer, nullable=False)

class Headline(db.Model):
    """
    A table storing news headlines.
    """
    __tablename__ = 'headlines'

    # Primary key: a unique auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True)

    # The headline text
    title = db.Column(db.String(300), nullable=False)

    # A URL linking to the actual news article on its website
    url = db.Column(db.String(300), nullable=False)

    # A foreign key linking this headline to a specific NewsSource
    source_id = db.Column(db.Integer, db.ForeignKey('news_sources.id'), nullable=False)

    # Stores artiocle publish data
    published_at = db.Column(db.String(50), nullable=False)

    # Relationship so we can easily access the NewsSource data from a Headline object
    source = db.relationship('NewsSource', backref='headlines')
