from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
BASE_DIR=os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///portfolio.db')
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR,'static','uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    about = db.Column(db.Text, nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    image = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    degree = db.Column(db.String(120), nullable=False)
    school = db.Column(db.String(120), nullable=False)
    field = db.Column(db.String(120), nullable=True)
    start_year = db.Column(db.String(4), nullable=True)
    end_year = db.Column(db.String(4), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    technologies = db.Column(db.String(200), nullable=True)
    link = db.Column(db.String(200), nullable=True)
    image = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    proficiency = db.Column(db.String(50), nullable=True)  # Beginner, Intermediate, Advanced
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    start_date = db.Column(db.String(10), nullable=True)
    end_date = db.Column(db.String(10), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Hobby(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
with app.app_context():      
    db.create_all()
# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes - Authentication
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')
        
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Routes - Public Portfolio
@app.route('/')
def index():
    profile = Profile.query.first()
    education = Education.query.all()
    projects = Project.query.all()
    skills = Skill.query.all()
    experience = Experience.query.all()
    hobbies = Hobby.query.all()
    
    return render_template('index.html', 
                         profile=profile,
                         education=education,
                         projects=projects,
                         skills=skills,
                         experience=experience,
                         hobbies=hobbies)

# Routes - Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    profile = Profile.query.first()
    education = Education.query.all()
    projects = Project.query.all()
    skills = Skill.query.all()
    experience = Experience.query.all()
    hobbies = Hobby.query.all()
    
    return render_template('dashboard.html',
                         profile=profile,
                         education=education,
                         projects=projects,
                         skills=skills,
                         experience=experience,
                         hobbies=hobbies)

# Profile Routes
@app.route('/api/profile', methods=['GET'])
def get_profile():
    profile = Profile.query.first()
    if profile:
        return jsonify({
            'id': profile.id,
            'name': profile.name,
            'about': profile.about,
            'contact_email': profile.contact_email,
            'contact_phone': profile.contact_phone,
            'image': profile.image
        })
    return jsonify({}), 404

@app.route('/api/profile', methods=['POST'])
@login_required
def create_or_update_profile():
    profile = Profile.query.first()
    
    if not profile:
        profile = Profile()
    
    profile.name = request.form.get('name')
    profile.about = request.form.get('about')
    profile.contact_email = request.form.get('contact_email')
    profile.contact_phone = request.form.get('contact_phone')
    
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"profile_{datetime.now().timestamp()}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            profile.image = f"uploads/{filename}"
    
    db.session.add(profile)
    db.session.commit()
    
    return jsonify({'message': 'Profile updated successfully'}), 200

# Education Routes
@app.route('/api/education', methods=['GET'])
def get_education():
    education = Education.query.all()
    return jsonify([{
        'id': e.id,
        'degree': e.degree,
        'school': e.school,
        'field': e.field,
        'start_year': e.start_year,
        'end_year': e.end_year,
        'description': e.description
    } for e in education])

@app.route('/api/education', methods=['POST'])
@login_required
def create_education():
    data = request.get_json()
    education = Education(
        degree=data.get('degree'),
        school=data.get('school'),
        field=data.get('field'),
        start_year=data.get('start_year'),
        end_year=data.get('end_year'),
        description=data.get('description')
    )
    db.session.add(education)
    db.session.commit()
    return jsonify({'id': education.id, 'message': 'Education added'}), 201

@app.route('/api/education/<int:id>', methods=['PUT'])
@login_required
def update_education(id):
    education = Education.query.get(id)
    if not education:
        return jsonify({'error': 'Not found'}), 404
    
    data = request.get_json()
    education.degree = data.get('degree', education.degree)
    education.school = data.get('school', education.school)
    education.field = data.get('field', education.field)
    education.start_year = data.get('start_year', education.start_year)
    education.end_year = data.get('end_year', education.end_year)
    education.description = data.get('description', education.description)
    
    db.session.commit()
    return jsonify({'message': 'Education updated'}), 200

@app.route('/api/education/<int:id>', methods=['DELETE'])
@login_required
def delete_education(id):
    education = Education.query.get(id)
    if not education:
        return jsonify({'error': 'Not found'}), 404
    
    db.session.delete(education)
    db.session.commit()
    return jsonify({'message': 'Education deleted'}), 200

# Projects Routes
@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'description': p.description,
        'technologies': p.technologies,
        'link': p.link,
        'image': p.image
    } for p in projects])

@app.route('/api/projects', methods=['POST'])
@login_required
def create_project():
    project = Project(
        title=request.form.get('title'),
        description=request.form.get('description'),
        technologies=request.form.get('technologies'),
        link=request.form.get('link')
    )
    
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"project_{datetime.now().timestamp()}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            project.image = f"uploads/{filename}"
    
    db.session.add(project)
    db.session.commit()
    return jsonify({'id': project.id, 'message': 'Project added'}), 201

@app.route('/api/projects/<int:id>', methods=['PUT'])
@login_required
def update_project(id):
    project = Project.query.get(id)
    if not project:
        return jsonify({'error': 'Not found'}), 404
    
    project.title = request.form.get('title', project.title)
    project.description = request.form.get('description', project.description)
    project.technologies = request.form.get('technologies', project.technologies)
    project.link = request.form.get('link', project.link)
    
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"project_{datetime.now().timestamp()}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            project.image = f"uploads/{filename}"
    
    db.session.commit()
    return jsonify({'message': 'Project updated'}), 200

@app.route('/api/projects/<int:id>', methods=['DELETE'])
@login_required
def delete_project(id):
    project = Project.query.get(id)
    if not project:
        return jsonify({'error': 'Not found'}), 404
    
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted'}), 200

# Skills Routes
@app.route('/api/skills', methods=['GET'])
def get_skills():
    skills = Skill.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'proficiency': s.proficiency
    } for s in skills])

@app.route('/api/skills', methods=['POST'])
@login_required
def create_skill():
    data = request.get_json()
    skill = Skill(
        name=data.get('name'),
        proficiency=data.get('proficiency', 'Intermediate')
    )
    db.session.add(skill)
    db.session.commit()
    return jsonify({'id': skill.id, 'message': 'Skill added'}), 201

@app.route('/api/skills/<int:id>', methods=['PUT'])
@login_required
def update_skill(id):
    skill = Skill.query.get(id)
    if not skill:
        return jsonify({'error': 'Not found'}), 404
    
    data = request.get_json()
    skill.name = data.get('name', skill.name)
    skill.proficiency = data.get('proficiency', skill.proficiency)
    
    db.session.commit()
    return jsonify({'message': 'Skill updated'}), 200

@app.route('/api/skills/<int:id>', methods=['DELETE'])
@login_required
def delete_skill(id):
    skill = Skill.query.get(id)
    if not skill:
        return jsonify({'error': 'Not found'}), 404
    
    db.session.delete(skill)
    db.session.commit()
    return jsonify({'message': 'Skill deleted'}), 200

# Experience Routes
@app.route('/api/experience', methods=['GET'])
def get_experience():
    experience = Experience.query.all()
    return jsonify([{
        'id': e.id,
        'title': e.title,
        'company': e.company,
        'start_date': e.start_date,
        'end_date': e.end_date,
        'description': e.description
    } for e in experience])

@app.route('/api/experience', methods=['POST'])
@login_required
def create_experience():
    data = request.get_json()
    experience = Experience(
        title=data.get('title'),
        company=data.get('company'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        description=data.get('description')
    )
    db.session.add(experience)
    db.session.commit()
    return jsonify({'id': experience.id, 'message': 'Experience added'}), 201

@app.route('/api/experience/<int:id>', methods=['PUT'])
@login_required
def update_experience(id):
    experience = Experience.query.get(id)
    if not experience:
        return jsonify({'error': 'Not found'}), 404
    
    data = request.get_json()
    experience.title = data.get('title', experience.title)
    experience.company = data.get('company', experience.company)
    experience.start_date = data.get('start_date', experience.start_date)
    experience.end_date = data.get('end_date', experience.end_date)
    experience.description = data.get('description', experience.description)
    
    db.session.commit()
    return jsonify({'message': 'Experience updated'}), 200

@app.route('/api/experience/<int:id>', methods=['DELETE'])
@login_required
def delete_experience(id):
    experience = Experience.query.get(id)
    if not experience:
        return jsonify({'error': 'Not found'}), 404
    
    db.session.delete(experience)
    db.session.commit()
    return jsonify({'message': 'Experience deleted'}), 200

# Hobbies Routes
@app.route('/api/hobbies', methods=['GET'])
def get_hobbies():
    hobbies = Hobby.query.all()
    return jsonify([{
        'id': h.id,
        'name': h.name,
        'description': h.description
    } for h in hobbies])

@app.route('/api/hobbies', methods=['POST'])
@login_required
def create_hobby():
    data = request.get_json()
    hobby = Hobby(
        name=data.get('name'),
        description=data.get('description')
    )
    db.session.add(hobby)
    db.session.commit()
    return jsonify({'id': hobby.id, 'message': 'Hobby added'}), 201

@app.route('/api/hobbies/<int:id>', methods=['PUT'])
@login_required
def update_hobby(id):
    hobby = Hobby.query.get(id)
    if not hobby:
        return jsonify({'error': 'Not found'}), 404
    
    data = request.get_json()
    hobby.name = data.get('name', hobby.name)
    hobby.description = data.get('description', hobby.description)
    
    db.session.commit()
    return jsonify({'message': 'Hobby updated'}), 200

@app.route('/api/hobbies/<int:id>', methods=['DELETE'])
@login_required
def delete_hobby(id):
    hobby = Hobby.query.get(id)
    if not hobby:
        return jsonify({'error': 'Not found'}), 404
    
    db.session.delete(hobby)
    db.session.commit()
    return jsonify({'message': 'Hobby deleted'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
