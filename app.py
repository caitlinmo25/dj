from flask import Flask, redirect, render_template, flash
from flask_debugtoolbar import DebugToolbarExtension

from models import db, connect_db, Playlist, Song, PlaylistSong
from forms import NewSongForPlaylistForm, SongForm, PlaylistForm

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:549721@localhost:5432/playlist-app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)
with app.app_context():
    # Create all tables
    db.create_all()

app.config['SECRET_KEY'] = "I'LL NEVER TELL!!"

# Having the Debug Toolbar show redirects explicitly is often useful;
# however, if you want to turn it off, you can uncomment this line:
#
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)


@app.route("/")
def root():
    """Homepage: redirect to /playlists."""

    return redirect("/playlists")


##############################################################################
# Playlist routes


@app.route("/playlists")
def show_all_playlists():
    """Return a list of playlists."""

    playlists = Playlist.query.all()
    return render_template("playlists.html", playlists=playlists)


@app.route("/playlists/<int:playlist_id>")
def show_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    songs = PlaylistSong.query.filter_by(playlist_id=playlist_id).join(Song).add_columns(Song.title, Song.artist).all()
    return render_template("playlist.html", playlist=playlist, songs=songs)



@app.route("/playlists/add", methods=["GET", "POST"])
def add_playlist():
    form = PlaylistForm()

    if form.validate_on_submit():
        # Check if the playlist name already exists
        existing_playlist = Playlist.query.filter_by(name=form.name.data).first()

        if existing_playlist is not None:
            # If the playlist exists, flash a message and render the form again
            flash('A playlist with this name already exists. Please choose a different name.', 'error')
            return render_template("new_playlist.html", form=form)

        # If the playlist does not exist, create a new one
        new_playlist = Playlist(name=form.name.data)
        db.session.add(new_playlist)
        db.session.commit()
        flash('New playlist added successfully!', 'success')
        return redirect("/playlists")

    return render_template("new_playlist.html", form=form)



##############################################################################
# Song routes


@app.route("/songs")
def show_all_songs():
    """Show list of songs."""

    songs = Song.query.all()
    return render_template("songs.html", songs=songs)


@app.route("/songs/<int:song_id>")
def show_song(song_id):
    song = Song.query.get_or_404(song_id)
    return render_template("song.html", song=song)



@app.route("/songs/add", methods=["GET", "POST"])
def add_song():
    form = SongForm()
    if form.validate_on_submit():
        new_song = Song(title=form.title.data, artist=form.artist.data)
        db.session.add(new_song)
        db.session.commit()
        return redirect("/songs")
    return render_template("new_song.html", form=form)



@app.route("/playlists/<int:playlist_id>/add-song", methods=["GET", "POST"])
def add_song_to_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    form = NewSongForPlaylistForm()

    # Restrict form to songs not already on this playlist
    existing_songs = [ps.song_id for ps in PlaylistSong.query.filter_by(playlist_id=playlist_id).all()]
    available_songs = Song.query.filter(Song.id.notin_(existing_songs)).all()
    form.song.choices = [(s.id, s.title) for s in available_songs]

    if form.validate_on_submit():
        playlist_song = PlaylistSong(playlist_id=playlist_id, song_id=form.song.data)
        db.session.add(playlist_song)
        db.session.commit()
        return redirect(f"/playlists/{playlist_id}")

    return render_template("add_song_to_playlist.html", playlist=playlist, form=form)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, port=5001)  # set debug=False in production