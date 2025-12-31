# backend/api/models/challenges.py
from ..utils import db
from datetime import datetime
import logging
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)

class Challenge(db.Model):
    __tablename__ = 'challenges'
    id = db.Column(db.Integer(), primary_key=True, index=True)
    user1_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)
    user2_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)
    
    created_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"Challenge {self.id} | User1 ID: {self.user1_id} | User2 ID: {self.user2_id} | Status: {self.status} | Created At: {self.created_at} | Updated At: {self.updated_at}"
    
    def save(self):
        db.session.add(self)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            logger.exception('IntegrityError saving Challenge')
            raise
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('Database error saving Challenge')
            raise
        except Exception:
            db.session.rollback()
            logger.exception('Unexpected error saving Challenge')
            raise

    def delete(self):
        db.session.delete(self)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception('Failed to delete Challenge')
            raise

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)