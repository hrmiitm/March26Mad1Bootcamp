# SQLALCHEMY class ---> object ---> inherit the model to make CLASS
# object init with FLASK APP
'''
Python-------------> Database
Class------------> Table
Object----------> Row
Attributes------> Column
list of objects---> List of rows
'''

from flask_sqlalchemy import SQLAlchemy # Class

db = SQLAlchemy() # Instance/Object

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)

    # Roles
    isUser = db.Column(db.Boolean, default=True)
    isCreator = db.Column(db.Boolean, default=False)
    isAdmin = db.Column(db.Boolean, default=False)

    # Is User Blacklisted
    isBlacklisted = db.Column(db.Boolean, default=False)

    # One To Many with songs table
        # <user3Obj>.songs ===> [<song3>, <song4>,....] ==> [(id,name), (id, name)....]
        # <song3>.user ==> <user3Object>
    songs = db.relationship('Song', backref='user', lazy=True)


    # One To Many with Album Table
        # <user3Obj>.albums ===> [<album1>, .....]
        # <album1>.user ======> <user1>
    albums = db.relationship('Album', backref='user', lazy=True)
    playlists = db.relationship('Playlist', backref='user', lazy=True)


#2) new secondary table creation for many to many
SongInAlbum = db.Table('song_in_album',
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True),
    db.Column('album_id', db.Integer, db.ForeignKey('album.id'), primary_key=True)
)

SongInPlaylist = db.Table('song_in_playlist',
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True),
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id'), primary_key=True)
)


# Create a songs table
class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)

    lyrics = db.Column(db.String, default='')
    duration = db.Column(db.String, default='')
    date = db.Column(db.String, default='')
    rating = db.Column(db.Integer, default=0)
    isBlacklisted = db.Column(db.Boolean, default=False)

    # ForeignKey
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

        # song-album ==> many to many
    #1) one line of code
    albums = db.relationship('Album', secondary=SongInAlbum, lazy='subquery', backref=db.backref('songs', lazy=True))

    # Song--Playlist many to many
    playlists = db.relationship('Playlist', secondary=SongInPlaylist, lazy='subquery', backref=db.backref('songs', lazy=True))
    # songObj.playlists ==> return [<p1>, <p2>, ...]

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)

    genre = db.Column(db.String, default='')
    artist = db.Column(db.String, default='')
    isBlacklisted = db.Column(db.Boolean, default=False)

    # For
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)



class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=False)

    # for user-playlist ==> one to many relationship
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class UserRating(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), primary_key=True)
    rating = db.Column(db.Integer, unique=False)