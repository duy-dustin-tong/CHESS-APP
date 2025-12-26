# backend/api/models/elo.py
from ..utils import db
import json
from datetime import datetime

class EloEntry(db.Model):
    __tablename__ = 'elo_entries'
    id = db.Column(db.Integer(), primary_key=True, index=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)
    game_id = db.Column(db.Integer(), db.ForeignKey('games.id'), nullable=True, index=True, default=None)
    elo = db.Column(db.Integer(), nullable=False, default=1200)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)


    def __repr__(self):
        return f"EloEntry {self.id} | User ID: {self.user_id} | Game ID: {self.game_id} | Rating: {self.elo} | Created At: {self.created_at}"
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)