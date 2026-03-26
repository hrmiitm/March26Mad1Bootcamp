from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Song, Album, Playlist, UserRating
from datetime import datetime
import os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend — must be before pyplot import
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'ADFADSFA'
app.config['SONG_UPLOAD_FOLDER'] = 'static/songs'

# Connect(db--app), Edit, create if not exist
db.init_app(app)
app.app_context().push()
db.create_all() # create/update the database


# ===================RestFul=============================

from flask_restful import Api
api = Api(app)

# Routes setups for api
from test_api import Test, Song as SongAPI
api.add_resource(Test, '/api/test_x', endpoint='api_test')
api.add_resource(SongAPI, '/api/songs_api', endpoint='api_songs')

# =======================================================


def get_current_user():
    id = session.get('id')
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

def get_songs_stats():
    all_songs = Song.query.all()
    all_users = User.query.all()
    creators = [u for u in all_users if u.isCreator]
    blacklisted_songs = [s for s in all_songs if s.isBlacklisted]
    blacklisted_creators = [u for u in creators if u.isBlacklisted]

    # Average rating across rated songs
    rated_songs = [s for s in all_songs if s.rating and s.rating > 0]
    avg_rating = round(sum(s.rating for s in rated_songs) / len(rated_songs), 1) if rated_songs else 0

    return {
        'total_songs': len(all_songs),
        'active_songs': len(all_songs) - len(blacklisted_songs),
        'blacklisted_songs': len(blacklisted_songs),
        'total_albums': len(Album.query.all()),
        'total_playlists': len(Playlist.query.all()),
        'total_users': len(all_users),
        'total_creators': len(creators),
        'blacklisted_creators': len(blacklisted_creators),
        'avg_rating': avg_rating,
        'total_ratings': len(UserRating.query.all()),
    }

def create_graphs():
    """Generate 4 analytics charts and save to static/graphs/."""
    graphs_dir = os.path.join('static', 'graphs')
    os.makedirs(graphs_dir, exist_ok=True)

    # --- Shared style settings ---
    COLORS = ['#4361ee', '#f72585', '#4cc9f0', '#7209b7', '#3a0ca3', '#560bad']
    plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 10})

    # ---- 1. User Distribution (pie chart) ----
    all_users = User.query.all()
    n_admins   = sum(1 for u in all_users if u.isAdmin)
    n_creators = sum(1 for u in all_users if u.isCreator and not u.isAdmin)
    n_regular  = len(all_users) - n_admins - n_creators
    labels  = ['Regular Users', 'Creators', 'Admins']
    values  = [n_regular, n_creators, n_admins]
    colors  = ['#4361ee', '#f72585', '#7209b7']
    # Remove zero-value slices
    filtered = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
    if filtered:
        fl, fv, fc = zip(*filtered)
        fig, ax = plt.subplots(figsize=(5, 4))
        wedges, texts, autotexts = ax.pie(
            fv, labels=fl, colors=fc, autopct='%1.0f%%',
            startangle=140, pctdistance=0.75,
            wedgeprops=dict(width=0.55, edgecolor='white', linewidth=2)
        )
        for at in autotexts:
            at.set_fontsize(9)
            at.set_color('white')
        ax.set_title('User Distribution', fontweight='bold', pad=12)
        fig.tight_layout()
        fig.savefig(os.path.join(graphs_dir, 'user_distribution.png'), dpi=100, bbox_inches='tight')
        plt.close(fig)

    # ---- 2. Song Status (pie chart) ----
    all_songs = Song.query.all()
    n_active = sum(1 for s in all_songs if not s.isBlacklisted)
    n_black  = sum(1 for s in all_songs if s.isBlacklisted)
    if all_songs:
        fig, ax = plt.subplots(figsize=(5, 4))
        wedges, texts, autotexts = ax.pie(
            [n_active, n_black],
            labels=['Active', 'Blacklisted'],
            colors=['#4cc9f0', '#f72585'],
            autopct='%1.0f%%', startangle=90,
            wedgeprops=dict(width=0.55, edgecolor='white', linewidth=2)
        )
        for at in autotexts:
            at.set_fontsize(9)
            at.set_color('white')
        ax.set_title('Song Status', fontweight='bold', pad=12)
        fig.tight_layout()
        fig.savefig(os.path.join(graphs_dir, 'song_status.png'), dpi=100, bbox_inches='tight')
        plt.close(fig)

    # ---- 3. Top Rated Songs (horizontal bar chart) ----
    rated_songs = [s for s in all_songs if s.rating and s.rating > 0]
    rated_songs.sort(key=lambda s: s.rating, reverse=True)
    top_songs = rated_songs[:8]
    if top_songs:
        names   = [s.name[:18] + '…' if len(s.name) > 18 else s.name for s in top_songs]
        ratings = [s.rating for s in top_songs]
        bar_colors = ['#f72585' if r >= 4 else '#4361ee' if r >= 2 else '#adb5bd' for r in ratings]
        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.barh(names[::-1], ratings[::-1], color=bar_colors[::-1],
                       height=0.6, edgecolor='none')
        for bar, val in zip(bars, ratings[::-1]):
            ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                    f'  {val}/5', va='center', fontsize=9)
        ax.set_xlim(0, 5.8)
        ax.set_xlabel('Rating', fontsize=9)
        ax.xaxis.set_major_locator(mticker.MultipleLocator(1))
        ax.set_title('Top Rated Songs', fontweight='bold', pad=12)
        ax.spines[['top', 'right']].set_visible(False)
        ax.tick_params(axis='y', labelsize=9)
        fig.tight_layout()
        fig.savefig(os.path.join(graphs_dir, 'top_rated_songs.png'), dpi=100, bbox_inches='tight')
        plt.close(fig)

    # ---- 4. Songs per Creator (vertical bar chart) ----
    creators = [u for u in all_users if u.isCreator]
    creators_with_songs = [(u.username, len(u.songs)) for u in creators if u.songs]
    creators_with_songs.sort(key=lambda x: x[1], reverse=True)
    top_creators = creators_with_songs[:7]
    if top_creators:
        c_names, c_counts = zip(*top_creators)
        short_names = [n[:10] + '…' if len(n) > 10 else n for n in c_names]
        fig, ax = plt.subplots(figsize=(5, 4))
        bar_colors = [COLORS[i % len(COLORS)] for i in range(len(short_names))]
        bars = ax.bar(short_names, c_counts, color=bar_colors, edgecolor='none', width=0.55)
        for bar, val in zip(bars, c_counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                    str(val), ha='center', va='bottom', fontsize=9)
        ax.set_ylabel('Songs', fontsize=9)
        ax.set_title('Songs per Creator', fontweight='bold', pad=12)
        ax.spines[['top', 'right']].set_visible(False)
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        plt.xticks(rotation=20, ha='right', fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(graphs_dir, 'songs_per_creator.png'), dpi=100, bbox_inches='tight')
        plt.close(fig)


#+++++++++++++++++++++++++++++++++++++++++++
# RBAC
#Function
def isUser(): # return true/false
    return True if get_current_user() != None else False

def isCreator():
    u = get_current_user()
    if u and u.isCreator: return True
    return False

def isAdmin():
    u = get_current_user()
    if u and u.isAdmin: return True
    return False

#Decorator
def user_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            
            curr_id = session.get('id', None)
            curr_user_obj = User.query.filter_by(id=curr_id).first()

            # login
            if curr_user_obj:
                return fn(*args, **kwargs)
            else:
                flash('You are not LoggedIn!', 'danger')
                return redirect(url_for('access'))

        return decorator

    return wrapper

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            curr_id = session.get('id', None)
            curr_user_obj = User.query.filter_by(id=curr_id).first()

            # login and admin
            if curr_user_obj and curr_user_obj.isAdmin:
                return fn(*args, **kwargs)
            else:
                flash('You are not Admin!', 'danger')
                return redirect(url_for('access'))

        return decorator

    return wrapper

# greet("hi", "how", message="Welcome!", name="Bob")

def creator_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):

            curr_id = session.get('id', None)
            curr_user_obj = User.query.filter_by(id=curr_id).first()

            # login and creator
            if curr_user_obj and curr_user_obj.isCreator:
                return fn(*args, **kwargs)
            else:
                flash('You are not Creator!', 'danger')
                return redirect(url_for('access'))

        return decorator

    return wrapper
# =======================================================

#---------------------------------------------
# 'localhost:5000/
# localhost:5000/?song_id=4
@app.route('/')
@user_required()
def home():
    user = get_current_user()           # <u1>
    # songs = Song.query.filter_by(isBlacklisted=False).all() # [<s1>, <s2>,.....]

    song = None
    song_id = request.args.get('song_id') # 2

    songs = Song.query.filter_by(isBlacklisted=False).order_by(Song.rating.desc()).all()
    search = request.args.get('search')  # None, "leoabc"
    if search:
        songs = Song.query.filter_by(isBlacklisted=False).filter(Song.name.contains(search)).order_by(Song.rating.desc()).all()

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
        session['id'] = user.id # Login
        flash('Logged in successfully', 'success')
        if user.isAdmin:
            return redirect(url_for('admin'))
        
    else:
        flash('Invalid credentials', 'danger')
        return redirect(url_for('access'))

    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('id')
    return redirect(url_for('access'))

#--------------------------------------------





@app.route('/register', methods=['POST'])
def register():
    # # data caputure ----------> html -----> input ----> name(username, email, password1, password2)
    # un = request.form.get('username') # string or none
    # e = request.form.get('email')
    # p1 = request.form.get('passsword1')
    # p2 = request.form.get('password2')

    # # task with data -----> User table ----> Create the Row ---> insert row
    # # --------------------- User Class -----> Object of User ---> db.session.add(obje) db.session.commit()
    # # ----------------------import it ----
    # object1 = User(username=un, email = e, password=p1)
    # db.session.add(object1)
    # db.sesssion.commit()



    # # redirect/render template
    # return redirect(url_for('access'))















    username = request.form.get('username') # String or None
    email = request.form.get('email') # String or None
    password1 = request.form.get('password1') # String or None
    password2 = request.form.get('password2') # String or None

    # Validate
    if password1 != password2:
        flash('Passwords do not match', 'danger')
    elif User.query.filter_by(email=email).first():
        flash('User already exists with this email', 'danger')
    else:
        user = User(username=username, email=email, password=password1)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully', 'success')
    
    return redirect(url_for('access'))


# --------------------View Routes---------------------------
@app.route('/songs')
@creator_required()
def song():
    user = get_current_user()
    songs = user.songs
    song = None
    song_id = request.args.get('song_id')
    if song_id:
        song = Song.query.filter_by(id=song_id).first()
    return render_template('songs.html', user=user, songs=songs, song=song)

@app.route("/xyz")
@creator_required()
def greetme():
    return "<h1> Hi Creator </h1>"

@app.route('/playlists')
@user_required()
def playlist():

    user = get_current_user()
    playlists = user.playlists
    song = None
    song_id = request.args.get('song_id')
    if song_id:
        song = Song.query.filter_by(id=song_id).first()

    selected_playlist = None
    playlist_id = request.args.get('playlist_id')
    if playlist_id:
        selected_playlist = Playlist.query.filter_by(id=playlist_id).first()

    return render_template('playlists.html', user=user, playlists=playlists, song=song, selected_playlist=selected_playlist)

@app.route('/albums')
@creator_required()
def album():
    user = get_current_user()
    albums = user.albums
    song = None
    song_id = request.args.get('song_id')
    if song_id:
        song = Song.query.filter_by(id=song_id).first()
        
    selected_album = None
    album_id = request.args.get('album_id')
    if album_id:
        selected_album = Album.query.filter_by(id=album_id).first()

    return render_template('albums.html', user=user, albums=albums, song=song, selected_album=selected_album)

@app.route('/profile')
@user_required()
def profile():
    user = get_current_user()
    stats = get_current_user_stats()
    return render_template('profile.html', user=user, stats=stats)

@app.route('/make_creator')
@user_required()
def make_creator():
    user = get_current_user()
    user.isCreator = True
    db.session.commit()
    flash('You are now a creator', 'success')
    return redirect(url_for('profile'))


#_______________________________________________________________
#---------------------Upload Routes---------------------------
@app.route('/upload_song', methods=['POST'])
@creator_required()
def upload_song():
    user = get_current_user()
    if user.isBlacklisted:
        flash('You are blacklisted so not allowed the upload song route', 'danger')
        return redirect(url_for('access'))


    name = request.form.get('name')
    lyrics = request.form.get('lyrics')
    duration = request.form.get('duration')
    date = datetime.now().strftime('%d-%m-%Y')

    song_file = request.files.get('song_file')
    
    if not name:
        flash('Song name is required', 'danger')
    elif Song.query.filter_by(name=name).first():
        flash('Song already exists', 'danger')
    elif not song_file:
        flash('Song file is required', 'danger')
    else:
        song = Song(name=name, lyrics=lyrics, duration=duration, date=date, user_id=user.id)
        db.session.add(song)
        db.session.commit()

        song_file.save(os.path.join(app.config['SONG_UPLOAD_FOLDER'], str(song.id) + '.mp3'))

        flash('Song uploaded successfully', 'success')

    return redirect(url_for('song'))

@app.route('/upload_album', methods=['POST'])
@creator_required()
def upload_album():
    user = get_current_user()
    name = request.form.get('name')
    genre = request.form.get('genre')
    artist = request.form.get('artist')
    date = datetime.now().strftime('%d-%m-%Y')

    album_files = request.files.getlist('album_files')

    if not album_files or not album_files[0].filename:
        flash('Album files are required', 'danger')
    elif not name:
        flash('Album name is required', 'danger')
    elif Album.query.filter_by(name=name).first():
        flash('Album already exists', 'danger')
    else:
        album = Album(name=name, genre=genre, artist=artist, user_id=user.id)
        db.session.add(album)
        db.session.commit()

        for album_file in album_files:
            if album_file.filename:
                # get filename securely 
                filename = album_file.filename
                # we only want the name, not the extension, for the database
                base_name = os.path.splitext(filename)[0]
                
                # Check if a song with this name already exists
                existing_song = Song.query.filter_by(name=base_name).first()
                if existing_song:
                    # Append next song id to ensure a truly unique name
                    last_song = Song.query.order_by(Song.id.desc()).first()
                    new_song_id = (last_song.id + 1) if last_song else 1
                    base_name = f"{base_name}_{new_song_id}"
                
                song = Song(name=base_name, date=date, user_id=user.id)
                db.session.add(song)
                db.session.commit()
                album.songs.append(song) # Many To Many Relationship
                album_file.save(os.path.join(app.config['SONG_UPLOAD_FOLDER'], str(song.id) + '.mp3'))

        flash('Album uploaded successfully', 'success')

    return redirect(url_for('album'))

@app.route('/create_playlist', methods=['POST'])
@user_required()
def create_playlist():
    user = get_current_user()
    name = request.form.get('name')

    if not name:
        flash('Playlist name is required', 'danger')
    elif Playlist.query.filter_by(name=name).first():
        flash('Playlist already exists', 'danger')
    else:
        playlist = Playlist(name=name, user_id=user.id)
        db.session.add(playlist)
        db.session.commit()
        flash('Playlist created successfully', 'success')
    
    return redirect(url_for('playlist'))

#______________________________________________________________
#----------------------Update Routes--------------------------------
@app.route('/update_song', methods=['POST'])
@creator_required()
def update_song():
    # data ----
    user = get_current_user()

    song_id = request.form.get('song_id')
    name = request.form.get('name')
    lyrics = request.form.get('lyrics')
    duration = request.form.get('duration')

    # Validate
    song = Song.query.filter_by(id=song_id).first()
    if not song:
        flash('Song not found', 'danger')
    elif song.user_id != user.id:
        flash('You are not authorized to update this song', 'danger')
    else:
        # task ---> READ ---> objec.att = vlaue ---> commit

        song = Song.query.filter_by(id=song_id).first() # READ
        song.name = name    # Object.att = name
        song.lyrics = lyrics # -------
        song.duration = duration # ------
        db.session.commit() # commit
        
        flash('Song updated successfully', 'success')
    return redirect(url_for('song'))

@app.route('/rate_song', methods=['POST'])
@user_required()
def rate_song():
    user = get_current_user()
    song_id = request.args.get('song_id')
    rating_val = request.form.get('rating')
    
    if not user:
        flash('You must be logged in to rate songs', 'danger')
        return redirect(url_for('access'))
        
    if not song_id or not rating_val:
        flash('Invalid rating submission', 'danger')
        return redirect(request.referrer or url_for('home'))
        
    try:
        rating_val = int(rating_val)
        if rating_val < 1 or rating_val > 5:
            raise ValueError
    except ValueError:
        flash('Rating must be between 1 and 5', 'danger')
        return redirect(request.referrer or url_for('home'))
        
    song = Song.query.filter_by(id=song_id).first()
    if not song:
        flash('Song not found', 'danger')
        return redirect(request.referrer or url_for('home'))
        
    # Check if user already rated
    existing_rating = UserRating.query.filter_by(user_id=user.id, song_id=song.id).first()
    if existing_rating:
        existing_rating.rating = rating_val
    else:
        new_rating = UserRating(user_id=user.id, song_id=song.id, rating=rating_val)
        db.session.add(new_rating)
        
    db.session.commit()
    
    # Calculate new average rating for the song
    all_ratings = UserRating.query.filter_by(song_id=song.id).all()
    if all_ratings:
        avg_rating = sum(r.rating for r in all_ratings) / len(all_ratings)
        # Update song rating (as integer since column is integer)
        song.rating = int(round(avg_rating))
        db.session.commit()
        
    flash('Rating submitted successfully', 'success')
    return redirect(request.referrer or url_for('home'))

@app.route('/update_album', methods=['POST'])
@creator_required()
def update_album():
    user = get_current_user()

    album_id = request.form.get('album_id')
    name = request.form.get('name')
    genre = request.form.get('genre')
    artist = request.form.get('artist')

    album = Album.query.filter_by(id=album_id).first()
    if not album:
        flash('Album not found', 'danger')
    elif album.user_id != user.id:
        flash('You are not authorized to update this album', 'danger')
    else:
        album = Album.query.filter_by(id=album_id).first()
        album.name = name
        album.genre = genre
        album.artist = artist
        db.session.commit()
        
        flash('Album updated successfully', 'success')
    return redirect(url_for('album'))

@app.route('/update_playlist', methods=['POST'])
@user_required()
def update_playlist():
    user = get_current_user()

    playlist_id = request.form.get('playlist_id')
    name = request.form.get('name')

    playlist = Playlist.query.filter_by(id=playlist_id).first()
    if not playlist:
        flash('Playlist not found', 'danger')
    elif playlist.user_id != user.id:
        flash('You are not authorized to update this playlist', 'danger')
    else:
        playlist = Playlist.query.filter_by(id=playlist_id).first()
        playlist.name = name
        db.session.commit()
        
        flash('Playlist updated successfully', 'success')
    return redirect(url_for('playlist'))

@app.route('/update_profile', methods=['POST'])
@user_required()
def update_profile():
    user = get_current_user()

    # get data
    username = request.form.get('username')
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_new_password = request.form.get('confirm_new_password')

    # validtioina
    user = User.query.filter_by(id=user.id).first() # READ
    if username:
        user.username = username # Object.att = vlaue
    if old_password and new_password and confirm_new_password:
        if user.password == old_password:
            if new_password == confirm_new_password:
                user.password = new_password # objec.att = value
            else:
                flash('New password and confirm new password do not match', 'danger')
        else:
            flash('Old password is incorrect', 'danger')
    db.session.commit() # commit
    
    flash('Profile updated successfully', 'success')
    return redirect(url_for('profile'))

#_______________________________________________________________
#--------------------Add Songs To Playlist----------------------
@app.route('/add_song_to_playlist')
def add_song_to_playlist():
    user = get_current_user()

    song_id = request.args.get('song_id')
    playlist_id = request.args.get('playlist_id')

    song = Song.query.filter_by(id=song_id).first()
    playlist = Playlist.query.filter_by(id=playlist_id).first()
    if not song:
        flash('Song not found', 'danger')
    elif not playlist:
        flash('Playlist not found', 'danger')
    elif playlist.user_id != user.id:
        flash('You are not authorized to add this song to this playlist', 'danger')
    else:
        playlist.songs.append(song)
        db.session.commit()
        flash('Song added to playlist successfully', 'success')
    return redirect(url_for('playlist'))

@app.route('/remove_song_from_playlist')
def remove_song_from_playlist():
    user = get_current_user()

    song_id = request.args.get('song_id')
    playlist_id = request.args.get('playlist_id')

    song = Song.query.filter_by(id=song_id).first()
    playlist = Playlist.query.filter_by(id=playlist_id).first()
    if not song:
        flash('Song not found', 'danger')
    elif not playlist:
        flash('Playlist not found', 'danger')
    elif playlist.user_id != user.id:
        flash('You are not authorized to remove this song from this playlist', 'danger')
    else:
        playlist.songs.remove(song)
        db.session.commit()
        flash('Song removed from playlist successfully', 'success')
    return redirect(url_for('playlist'))    


#______________________________________________________________
#--------------------Delete Routes--------------------------------
# /delete_song?song_id=5
@app.route('/delete_song')
def delete_song():
    # to delete song ---> data? ---> song_id(query?song_id={{song_id}}), user_id(loogeing --session),
    user = get_current_user()

    song_id = request.args.get('song_id')
    song = Song.query.filter_by(id=song_id).first()
    if not song:
        flash('Song not found', 'danger')
    elif song.user_id != user.id:
        flash('You are not authorized to delete this song', 'danger')
    else:
        song.playlists = []
        song.albums = []
        ur = song.user_ratings
        for i in ur:
            db.session.delete(i)
        
        db.session.delete(song)
        db.session.commit()
        flash('Song deleted successfully', 'success')
    return redirect(url_for('song'))

@app.route('/delete_album')
def delete_album():
    user = get_current_user()

    album_id = request.args.get('album_id')
    album = Album.query.filter_by(id=album_id).first()
    if not album:
        flash('Album not found', 'danger')
    elif album.user_id != user.id:
        flash('You are not authorized to delete this album', 'danger')
    else:
        album.songs = []
        
        db.session.delete(album)
        db.session.commit()
        flash('Album deleted successfully', 'success')
    return redirect(url_for('album'))

@app.route('/delete_playlist')
def delete_playlist():
    user = get_current_user()

    playlist_id = request.args.get('playlist_id')
    playlist = Playlist.query.filter_by(id=playlist_id).first()
    if not playlist:
        flash('Playlist not found', 'danger')
    elif playlist.user_id != user.id:
        flash('You are not authorized to delete this playlist', 'danger')
    else:
        playlist.songs = []

        db.session.delete(playlist)
        db.session.commit()
        flash('Playlist deleted successfully', 'success')
    return redirect(url_for('playlist'))

#----------------------------------------------------------------------
#______________________________________________________________________
@app.route('/admin')
@admin_required()
def admin():
    user = get_current_user()

    stats = get_songs_stats() # {totla_song=10, ....}
    create_graphs() # create new images and store in STATIC

    return render_template('admin_dashboard.html', user=user, stats=stats)

# /admin/songs
# /admin/songs?song_id=5
@app.route('/admin/songs')
@admin_required()
def admin_songs():
    user = get_current_user()

    whitelisted_songs = Song.query.filter_by(isBlacklisted=False).order_by(Song.rating.desc()).all()
    blacklisted_songs = Song.query.filter_by(isBlacklisted=True).all()

    song_id = request.args.get('song_id') # None or 5
    song = Song.query.filter_by(id=song_id).first() if song_id else None

    return render_template('admin_songs.html', user=user,
                           whitelisted_songs=whitelisted_songs,
                           blacklisted_songs=blacklisted_songs,
                           song=song)

@app.route('/admin/users')
@admin_required()
def admin_users():
    user = get_current_user()

    users = User.query.all()
    all_creators = User.query.filter_by(isCreator=True).all()

    whitelisted_creators = [c for c in all_creators if not c.isBlacklisted]

    blacklisted_creators = [c for c in all_creators if c.isBlacklisted]

    return render_template('admin_users.html', user=user, users=users,
                           whitelisted_creators=whitelisted_creators,
                           blacklisted_creators=blacklisted_creators)
#----------------------------------------------------------------------










@app.route('/admin/blacklist_song')
@admin_required()
def blacklist_song():
    user = get_current_user()
    song_id = request.args.get('song_id')
    song = Song.query.filter_by(id=song_id).first()
    if not song:
        flash('Song not found', 'danger')
    else:
        song.isBlacklisted = True
        db.session.commit()
        flash('Song blacklisted successfully', 'success')
    return redirect(url_for('admin_songs'))

@app.route('/admin/whitelist_song')
@admin_required()
def whitelist_song():
    user = get_current_user()
    song_id = request.args.get('song_id')
    song = Song.query.filter_by(id=song_id).first() # READ
    if not song:
        flash('Song not found', 'danger')
    else:
        song.isBlacklisted = False # object.att = value
        db.session.commit() # commit
        flash('Song whitelisted successfully', 'success')
    return redirect(url_for('admin_songs'))

@app.route('/admin/delete_song')
@admin_required()
def admin_delete_song():
    user = get_current_user()
    song_id = request.args.get('song_id')
    song = Song.query.filter_by(id=song_id).first()
    if not song:
        flash('Song not found', 'danger')
    else:
        song.playlists = []
        song.albums = []
        ratings = UserRating.query.filter_by(song_id=song.id).all()
        for r in ratings:
            db.session.delete(r)
        db.session.delete(song)
        db.session.commit()
        flash('Song deleted successfully', 'success')
    return redirect(url_for('admin_songs'))

@app.route('/admin/blacklist_creator')
@admin_required()
def blacklist_creator():
    user = get_current_user()
    creator_id = request.args.get('creator_id')
    creator = User.query.filter_by(id=creator_id).first()
    if not creator:
        flash('Creator not found', 'danger')
    else:
        creator.isBlacklisted = True
        db.session.commit()
        flash('Creator blacklisted successfully', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/whitelist_creator')
@admin_required()
def whitelist_creator():
    user = get_current_user()
    creator_id = request.args.get('creator_id')
    creator = User.query.filter_by(id=creator_id).first()
    if not creator:
        flash('Creator not found', 'danger')
    else:
        creator.isBlacklisted = False
        db.session.commit()
        flash('Creator whitelisted successfully', 'success')
    return redirect(url_for('admin_users'))


if __name__ == '__main__':
    app.run(debug=True)
