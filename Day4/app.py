from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Song, Album, Playlist, UserRating
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'ADFADSFA'
app.config['SONG_UPLOAD_FOLDER'] = 'static/songs'

# Connect(db--app), Edit, create if not exist
db.init_app(app)
app.app_context().push()
db.create_all() # create/update the database


def get_current_user():
    id = session.get('id') # None or expectedValue
    if id:
        user = User.query.filter_by(id=id).first()
    else:
        user = None
    return user

def get_current_user_stats():
    user = get_current_user()
    if user:
        return {
            'total_songs': len(user.songs),
            'total_albums': len(user.albums),
            'total_playlists': len(user.playlists)
        }
    return None


#---------------------------------------------
# 'localhost:5000/
# localhost:5000/?song_id=4
@app.route('/')
def home():
    user = get_current_user()           # <u1>
    songs = Song.query.filter_by(isBlacklisted=False).all() # [<s1>, <s2>,.....]

    song = None
    song_id = request.args.get('song_id') # 2

    if song_id:
        song = Song.query.filter_by(id=song_id, isBlacklisted=False).first() # <s2>
    return render_template('home.html', user=user, songs=songs, song=song)

@app.route('/access')
def access():
    user = get_current_user()
    return render_template('access.html', user=user)

#--------------------------------------------


# Login register logout
# -----> Take the data -----> do the task -------> redirect to pages
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email') # String or None
    password = request.form.get('password') # String or None

    # Data Vaidation
    # Check email/passwrod in Table(Class) User
    # User.query.filter_by(email=email, password=password) # [], [<user1> , ...]
    user = User.query.filter_by(email=email, password=password).first() # <user1>

    # LogIn
    if user:
        print(user.id)
        session['id'] = user.id
        flash('Logged in successfully', 'success')
    else:
        flash('Invalid credentials', 'danger')
        return redirect(url_for('access'))

    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('id')
    return redirect(url_for('access'))

#--------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5001)
