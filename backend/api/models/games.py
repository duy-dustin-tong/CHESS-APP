# backend/api/models/games.py
from ..utils import db
from sqlalchemy.dialects.postgresql import JSONB
import json
from enum import Enum
from datetime import datetime
import logging
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)




class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer(), primary_key=True, index=True)
    in_progress = db.Column(db.Boolean(), default=True, index=True)
    current_fen = db.Column(db.String(100), nullable=False, default='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')

    white_user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)
    black_user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)

    winner_id = db.Column(db.Integer(), db.ForeignKey('users.id'), default=None, nullable=True, index=True)
    draw_offer_from = db.Column(db.Integer(), nullable=True, default=None)
    win_by_resignation = db.Column(db.Boolean(), default=False)

    white_time_left = db.Column(db.Integer(), default=600) # 60 seconds
    black_time_left = db.Column(db.Integer(), default=600)

    created_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"Game {self.id} | In Progress: {self.in_progress}"
    
    def save(self):
        self.updated_at = datetime.utcnow()
        db.session.add(self)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            logger.exception('IntegrityError saving Game')
            raise
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('Database error saving Game')
            raise
        except Exception:
            db.session.rollback()
            logger.exception('Unexpected error saving Game')
            raise

    def delete(self):
        db.session.delete(self)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception('Failed to delete Game')
            raise

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)
    
    
