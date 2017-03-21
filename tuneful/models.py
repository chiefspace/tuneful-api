import os.path

from flask import url_for
from sqlalchemy import Column, Integer, String, Sequence, ForeignKey
from sqlalchemy.orm import backref, relationship

from tuneful import app
from .database import Base, engine


class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def as_dictionary(self):
        return {
            "id": self.id,
            "name": self.name,
            "path": url_for("uploaded_file", filename=self.name)
        }


class Song(Base):
    __tablename__ = 'songs'

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'))
    file_ = relationship(File, backref=backref('song', uselist=False),
                         single_parent=True, cascade="all, delete-orphan")

    def as_dictionary(self):
        return {
            'id': self.id,
            'file': self.file_.as_dictionary()
}