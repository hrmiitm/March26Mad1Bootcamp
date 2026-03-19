from flask import Flask, render_template, redirect, url_for, request, session # Class
from models import db, User
from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph


app = Flask(__name__) # Object
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite3"
app.config['SECRET_KEY'] = "jaldfafaosfv"


# DATABASE CONNECTION
db.init_app(app) # Flask ---> Sqlaclhemy
app.app_context().push() # without changes will not happen
db.create_all() # it update/create the DATABASE


@app.route('/') # Registring the function with url
def home():
    id = session.get('id')
    user_obj = User.query.filter_by(id=id).first()
    email = None
    if user_obj:
        email = user_obj.email
    x = 10
    return f"Hello {email} From Home Function {x}"

@app.route('/access')
def access():
    return render_template('access.html')   



@app.route('/register', methods=['POST'])
def register():
    # Take Data
    # request.form # {name='xyz', email='adfa'}
    # un = request.form.['username'] # 'xyz' or Error
    un = request.form.get('username') # 'xyz' or None
    e = request.form.get('email')
    p1 = request.form.get('password1')
    p2 = request.form.get('password2')

    # Verify Data
    if not e or not p1 or p1!=p2 :
        print('Not email or passwrod not matchecd')
        return redirect(url_for('access'))

    # Do the operation --> db operation
    user = User(username=un, email=e, password=gph(p1))
    db.session.add(user)
    db.session.commit()

    # return
    return redirect(url_for('access'))

@app.route('/login', methods=['POST'])
def login():
    # take data
    e = request.form.get('email')
    p = request.form.get('password')

    # verify
    if not e or not p:
        print('Either not email or not password')
        return redirect(url_for('access'))

    # user_objs = User.query.filter_by(email=e) # [<u1>, <u2>, ....]
    user_obj = User.query.filter_by(email=e).first() # <u1> or None
    if not user_obj:
        print('user email not found')
        return redirect(url_for('access'))

    if not cph(user_obj.password, p):
        print('password mismatched')
        return redirect(url_for('access'))
    
    # operation -> login
    session['id'] = user_obj.id


    # url_for('access') ----> '/access
    return redirect(url_for('home')) 

@app.route('/logout')
def logout():
    session.pop('id')
    return redirect(url_for('access'))

if __name__ == '__main__':
    app.run(debug=True) # Object Method ---> whose object ---> of Flask Class
