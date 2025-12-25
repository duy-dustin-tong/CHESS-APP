# backend/api/models/moves.py
from ..utils import db
import json
from datetime import datetime

class Move(db.Model):
    __tablename__ = 'moves'
    id = db.Column(db.Integer(), primary_key=True, index=True)
    game_id = db.Column(db.Integer(), db.ForeignKey('games.id'), nullable=False, index=True)
    move_number = db.Column(db.Integer(), nullable=False)
    uci = db.Column(db.String(), nullable=False)  # Universal Chess Interface notation
    created_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"Move {self.id} | Game ID: {self.game_id} | Move Number: {self.move_number} | UCI: {self.uci}"
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_moves_by_game_id(cls, game_id):
        return cls.query.filter_by(game_id=game_id).order_by(cls.move_number).all()