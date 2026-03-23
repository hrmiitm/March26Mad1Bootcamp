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
def song():
    user = get_current_user()
    songs = user.songs
    song = None
    song_id = request.args.get('song_id')
    if song_id:
        song = Song.query.filter_by(id=song_id).first()
    return render_template('songs.html', user=user, songs=songs, song=song)

@app.route('/playlists')
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
def profile():
    user = get_current_user()
    stats = get_current_user_stats()
    return render_template('profile.html', user=user, stats=stats)

@app.route('/make_creator')
def make_creator():
    user = get_current_user()
    user.isCreator = True
    db.session.commit()
    flash('You are now a creator', 'success')
    return redirect(url_for('profile'))


#_______________________________________________________________
#---------------------Upload Routes---------------------------
@app.route('/upload_song', methods=['POST'])
def upload_song():
    user = get_current_user()
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
def rate_song():
    user = get_current_user()
    song_id = request.form.get('song_id')
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

    # Get the SONGID, PLAYLIST ID ====> (2,5)
    song_id = request.args.get('song_id')
    playlist_id = request.args.get('playlist_id')

    # I GET THE OBJECTS ===> (<songObj>, <playlistObj>)
    song = Song.query.filter_by(id=song_id).first()
    playlist = Playlist.query.filter_by(id=playlist_id).first()

    # Validation
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


if __name__ == '__main__':
    app.run(debug=True)
