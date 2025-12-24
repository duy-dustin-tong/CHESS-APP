# backend/api/models/userGames.py
from ..utils import db
from sqlalchemy.dialects.postgresql import JSONB
import json
from datetime import datetime

class UserGame(db.Model):
    __tablename__ = 'user_games'
    id = db.Column(db.Integer(), primary_key=True, index=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)
    game_id = db.Column(db.Integer(), db.ForeignKey('games.id'), nullable=False, index=True)
    role = db.Column(db.String(5), nullable=False)  # e.g., 'white', 'black'
    joined_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"UserGames {self.id} | User ID: {self.user_id} | Game ID: {self.game_id} | Role: {self.role}"
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_user_and_game(cls, user_id, game_id):
        return cls.query.filter_by(user_id=user_id, game_id=game_id).first()