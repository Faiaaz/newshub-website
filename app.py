from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid

load_dotenv()

app = Flask(__name__)
# Database configuration - use environment variable in production
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:1234d@localhost:5432/news_db')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Admin credentials (in a real app, these would be in a database)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    articles = db.relationship('Article', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    articles = db.relationship('Article', backref='category', lazy=True)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    status = db.Column(db.String(20), default='draft')  # draft, published
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    published_at = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    tags = db.relationship('Tag', secondary='article_tags', backref='articles')
    
    @property
    def reading_time(self):
        return calculate_reading_time(self.content)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

# Association table for many-to-many relationship between articles and tags
article_tags = db.Table('article_tags',
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    
    query = Article.query.filter(Article.status == 'published')
    
    if category_id:
        query = query.filter(Article.category_id == category_id)
    
    if search:
        query = query.filter(Article.title.contains(search) | Article.content.contains(search))
    
    articles = query.order_by(Article.published_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    categories = Category.query.all()
    
    return render_template('index.html', articles=articles, categories=categories, search=search)

@app.route('/article/<int:article_id>')
def article(article_id):
    article = Article.query.get_or_404(article_id)
    if article.status != 'published':
        return "Article not found", 404
    return render_template('article.html', article=article)

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if (request.form['username'] == ADMIN_USERNAME and 
            request.form['password'] == ADMIN_PASSWORD):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin/login.html', error='Invalid credentials')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', type=int)
    search = request.args.get('search', '')
    
    query = Article.query
    
    if status_filter:
        query = query.filter(Article.status == status_filter)
    if category_filter:
        query = query.filter(Article.category_id == category_filter)
    if search:
        query = query.filter(Article.title.contains(search) | Article.content.contains(search))
    
    articles = query.order_by(Article.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    categories = Category.query.all()
    stats = {
        'total_articles': Article.query.count(),
        'published_articles': Article.query.filter_by(status='published').count(),
        'draft_articles': Article.query.filter_by(status='draft').count(),
        'total_categories': Category.query.count()
    }
    
    return render_template('admin/dashboard.html', 
                         articles=articles, 
                         categories=categories, 
                         stats=stats,
                         status_filter=status_filter,
                         category_filter=category_filter,
                         search=search)

@app.route('/admin/create', methods=['GET', 'POST'])
@login_required
def admin_create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        excerpt = request.form.get('excerpt', '')
        category_id = request.form.get('category_id', type=int)
        status = request.form.get('status', 'draft')
        
        # Handle image upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = f"uploads/{filename}"
        
        article = Article(
            title=title,
            content=content,
            excerpt=excerpt,
            image_url=image_url,
            status=status,
            author_id=1,  # Default admin user
            category_id=category_id
        )
        
        if status == 'published':
            article.published_at = datetime.now(timezone.utc)
        
        # Handle tags
        tags_input = request.form.get('tags', '')
        article.tags.clear()  # Clear existing tags first
        if tags_input:
            # Split by comma and clean up each tag
            tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                article.tags.append(tag)
        
        db.session.add(article)
        db.session.commit()
        
        flash('Article created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('admin/create.html', categories=categories, tags=tags)

@app.route('/admin/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
def admin_edit(article_id):
    article = Article.query.get_or_404(article_id)
    
    if request.method == 'POST':
        article.title = request.form['title']
        article.content = request.form['content']
        article.excerpt = request.form.get('excerpt', '')
        article.category_id = request.form.get('category_id', type=int)
        article.status = request.form.get('status', 'draft')
        article.updated_at = datetime.now(timezone.utc)
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                article.image_url = f"uploads/{filename}"
        
        # Handle tags
        tags_input = request.form.get('tags', '')
        article.tags.clear()  # Clear existing tags first
        if tags_input:
            # Split by comma and clean up each tag
            tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                article.tags.append(tag)
        
        if article.status == 'published' and not article.published_at:
            article.published_at = datetime.now(timezone.utc)
        
        db.session.commit()
        flash('Article updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    categories = Category.query.all()
    tags = Tag.query.all()
    return render_template('admin/edit.html', article=article, categories=categories, tags=tags)

@app.route('/admin/delete/<int:article_id>')
@login_required
def admin_delete(article_id):
    article = Article.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    flash('Article deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/categories')
@login_required
def admin_categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/create', methods=['POST'])
@login_required
def admin_create_category():
    name = request.form['name']
    description = request.form.get('description', '')
    
    if Category.query.filter_by(name=name).first():
        flash('Category already exists!', 'error')
    else:
        category = Category(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully!', 'success')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/delete/<int:category_id>')
@login_required
def admin_delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin_categories'))

def calculate_reading_time(content):
    """Calculate estimated reading time in minutes"""
    # Average reading speed is 200-250 words per minute
    words = len(content.split())
    minutes = max(1, round(words / 200))
    return minutes

# Create the database tables
with app.app_context():
    # Only create tables if they don't exist (don't drop them)
    db.create_all()
    
    # Check if admin user exists, if not create it
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
    
    # Check if categories exist, if not create them
    if Category.query.count() == 0:
        categories = [
            Category(name='Technology', description='Tech news and updates'),
            Category(name='Business', description='Business and finance news'),
            Category(name='Sports', description='Sports news and updates'),
            Category(name='Entertainment', description='Entertainment news')
        ]
        for category in categories:
            db.session.add(category)
    
    # Check if tags exist, if not create them
    if Tag.query.count() == 0:
        tags = [
            Tag(name='python'),
            Tag(name='flask'),
            Tag(name='web-development'),
            Tag(name='news')
        ]
        for tag in tags:
            db.session.add(tag)
    
    # Check if sample articles exist, if not create them
    if Article.query.count() == 0:
        sample_articles = [
            Article(
                title='First News Article',
                content='<p>This is the content of our first news article. It contains more detailed information about the topic.</p>',
                excerpt='A brief overview of the first article',
                status='published',
                published_at=datetime.now(timezone.utc),
                author_id=1,
                category_id=1
            ),
            Article(
                title='Second News Article',
                content='<p>This is the content of our second news article. It contains more detailed information about the topic.</p>',
                excerpt='A brief overview of the second article',
                status='published',
                published_at=datetime.now(timezone.utc),
                author_id=1,
                category_id=2
            )
        ]
        
        for article in sample_articles:
            db.session.add(article)
            # Add tags to articles
            tags = Tag.query.all()
            if tags:
                article.tags.append(tags[0])  # python
                article.tags.append(tags[3])  # news
    
    db.session.commit()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False) 