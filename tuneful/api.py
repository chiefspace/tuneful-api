import os.path
import json
import jsonschema

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

from . import models
from . import decorators
from . import app
from .database import session
from .utils import upload_path

# JSON Schema describing the structure of a song
song_schema = {
    "definitions": {
        "file": {
            "type": "object",
            "properties": {
                "id": {"type": "number"}
            }
        }
    },
    "properties": {
        "file": {"$ref": "#/definitions/file"}
    },
    "required": ["file"]
}


@app.route('/api/songs', methods=['GET'])
@decorators.accept("application/json")
def get_songs():
    data = session.query(models.Song)

    data = data.order_by(models.Song.id)
    return Response(json.dumps([song.as_dict() for song in data]),
                    200, mimetype='application/json')

@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def post_song():
    """ Add a new song """
    data = request.json

    # Check that the JSON supplied is valid
    # If not you return a 422 Unprocessable Entity
    try:
        jsonschema.validate(data, song_schema)
    except jsonschema.ValidationError as error:
        error = json.dumps({"message": error.message})
        return Response(error, 422, mimetype="application/json")

    file_ = session.query(models.File).get(data['file']['id'])
    if not file_:
        message = 'Could not find file with id {}'.format(data['file']['id'])
        error = json.dumps({'message': message})
        return Response(error, 404, mimetype='application/json')

    # Add the song to the database
    song = models.Song(file_=file_)
    session.add(song)
    session.commit()

    # Return a 201 Created, containing the song as JSON and with the
    # Location header set to the location of the song
    data = json.dumps(song.as_dict())
    headers = {"Location": url_for("get_song", id=song.id)}
    return Response(data, 201, headers=headers,
                    mimetype="application/json")





