# backend/api/models/games.py
from ..utils import db
from sqlalchemy.dialects.postgresql import JSONB
import json
from enum import Enum
from datetime import datetime




class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer(), primary_key=True, index=True)
    in_progress = db.Column(db.Boolean(), default=True, index=True)
    moves = db.Column(db.Text, nullable=False, default="")
    current_fen = db.Column(db.String(100), nullable=False, default='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')

    white_user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)
    black_user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)

    winner_id = db.Column(db.Integer(), db.ForeignKey('users.id'), default=None, nullable=True, index=True)
    draw_offer_from = db.Column(db.Integer(), nullable=True, default=None)
    win_by_resignation = db.Column(db.Boolean(), default=False)

    created_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"Game {self.id} | In Progress: {self.in_progress}"
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)
    
    
