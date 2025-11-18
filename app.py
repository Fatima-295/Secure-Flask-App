from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp
from flask_bcrypt import Bcrypt
from sqlalchemy import text

# Initialize Flask app
app = Flask(__name__)

# -------------------------------------------------------------------
# Basic Configurations
# -------------------------------------------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Secret key for CSRF + Sessions
app.config['SECRET_KEY'] = 'supersecretkey123'

# Secure session settings
app.config['SESSION_COOKIE_SECURE'] = True       # send only via HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True     # JS can’t access cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'    # reduce CSRF risk

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)

# -------------------------------------------------------------------
# Database Model
# -------------------------------------------------------------------
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(100))
    lname = db.Column(db.String(100))
    email = db.Column(db.String(120))

    def __repr__(self):
        return f"<Student {self.id} - {self.fname}>"

# Create tables if not exist
with app.app_context():
    db.create_all()

# -------------------------------------------------------------------
# WTForms for Secure Input Handling
# -------------------------------------------------------------------
class StudentForm(FlaskForm):
    fname = StringField("First Name", validators=[
        DataRequired(),
        Length(min=2, max=50),
        Regexp('^[A-Za-z ]*$', message="Only letters allowed")
    ])
    lname = StringField("Last Name", validators=[
        DataRequired(),
        Length(min=2, max=50),
        Regexp('^[A-Za-z ]*$', message="Only letters allowed")
    ])
    email = StringField("Email", validators=[
        DataRequired(), Email(message="Invalid email format")
    ])
    submit = SubmitField("Submit")

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------

# CREATE + READ
@app.route('/', methods=['GET', 'POST'])
def index():
    form = StudentForm()
    if form.validate_on_submit():
        # Input sanitized and validated by WTForms
        new_student = Student(
            fname=form.fname.data.strip(),
            lname=form.lname.data.strip(),
            email=form.email.data.strip()
        )
        db.session.add(new_student)
        db.session.commit()
        flash("Student added successfully and securely!", "success")
        return redirect('/')
    
    students = Student.query.all()
    return render_template('index.html', form=form, students=students)

# UPDATE
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    student = Student.query.get_or_404(id)
    form = StudentForm(obj=student)
    if form.validate_on_submit():
        student.fname = form.fname.data.strip()
        student.lname = form.lname.data.strip()
        student.email = form.email.data.strip()
        db.session.commit()
        flash("Record updated securely!", "info")
        return redirect('/')
    return render_template('update.html', form=form, student=student)

# DELETE
@app.route('/delete/<int:id>')
def delete(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash("Student deleted securely!", "danger")
    return redirect('/')

# -------------------------------------------------------------------
# Secure Example of Parameterized Query (for Report)
# -------------------------------------------------------------------
@app.route('/search')
def search():
    """Example of secure parameterized query"""
    email = request.args.get('email', '')
    if email:
        result = db.session.execute(
            text("SELECT * FROM student WHERE email=:email"),
            {"email": email}
        ).fetchall()
        return {"result": [dict(r) for r in result]}
    return {"result": []}

# -------------------------------------------------------------------
# Custom Error Pages (No sensitive info exposed)
# -------------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/hash_password/<pwd>')
def hash_password(pwd):
    hashed = bcrypt.generate_password_hash(pwd).decode('utf-8')
    return f"Original: {pwd}<br>Hashed: {hashed}"

# -------------------------------------------------------------------
# Run
# -------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
