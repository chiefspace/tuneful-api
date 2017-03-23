import unittest
import os
import shutil
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Py2 compatibility
from io import StringIO, BytesIO

import sys; print(list(sys.modules.keys()))
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())
        
    def test_get_songs(self):
        file_A = models.File(name='file_A.mp3')
        song_A = models.Song(file_=file_A)
        file_B = models.File(name='file_B.mp3')
        song_B = models.Song(file_=file_B)

        session.add_all([file_A, file_B, song_A, song_B])
        session.commit()

        response = self.client.get(
            '/api/songs',
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/json')

        data = json.loads(response.data.decode('ascii'))
        self.assertEqual(len(data), 2)

        response_song_A, response_song_B = data
        self.assertEqual(response_song_A['id'], song_A.id)
        self.assertEqual(response_song_A['file']['id'], song_A.file_.id)
        self.assertEqual(response_song_A['file']['name'], song_A.file_.name)
        self.assertEqual(response_song_B['id'], song_B.id)
        self.assertEqual(response_song_B['file']['id'], song_B.file_.id)
        self.assertEqual(response_song_B['file']['name'], song_B.file_.name)
        
    def test_post_song(self):
        file_A = models.File(name='file_A.mp3')
        session.add(file_A)
        session.commit()

        data = {
            "file": {
                "id": file_A.id
            }
        }

        response = self.client.post(
            "/api/songs",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(
            urlparse(response.headers.get("Location")).path, "/api/songs/1")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["file"]["id"], 1)
        self.assertEqual(data["file"]["name"], "file_A.mp3")

        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 1)

        song = songs[0]
        self.assertEqual(song.id, 1)
        self.assertEqual(song.file_.id, 1)
        self.assertEqual(song.file_.name, "file_A.mp3")
        
    def test_get_song(self):
        file_A = models.File(name='file_A.mp3')
        file_B = models.File(name='file_B.mp3')
        song_A = models.Song(file_=file_A)
        song_B = models.Song(file_=file_B)

        session.add_all([file_A, file_B, song_A, song_B])
        session.commit()

        response = self.client.get(
            '/api/songs/{}'.format(song_B.id),
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/json')

        song = json.loads(response.data.decode('ascii'))
        self.assertEqual(song['id'], song_B.id)
        self.assertEqual(song['file']['id'], song_B.file_.id)
        self.assertEqual(song['file']['name'], song_B.file_.name)
        
    def test_get_uploaded_file(self):
        path = upload_path('test.txt')
        with open(path, "wb") as f:
            f.write(b"File contents")

        response = self.client.get("/uploads/test.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/plain")
        self.assertEqual(response.data, b"File contents")

    def test_file_upload(self):
        data = {
            "file": (BytesIO(b"File contents"), "test.txt")
        }

        response = self.client.post("/api/files",
            data=data,
            content_type="multipart/form-data",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(urlparse(data["path"]).path, "/uploads/test.txt")

        path = upload_path("test.txt")
        self.assertTrue(os.path.isfile(path))
        with open(path, "rb") as f:
            contents = f.read()
        self.assertEqual(contents, b"File contents")

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())


