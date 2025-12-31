# backend/api/models/queue.py
from ..utils import db
from datetime import datetime
import logging
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)

class Queue(db.Model):
    __tablename__ = 'queue'
    id = db.Column(db.Integer(), primary_key=True, index=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"Queue Entry {self.id} | User ID: {self.user_id}"
    
    def save(self):
        db.session.add(self)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            logger.exception('IntegrityError saving Queue entry')
            raise
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('Database error saving Queue entry')
            raise
        except Exception:
            db.session.rollback()
            logger.exception('Unexpected error saving Queue entry')
            raise

    def delete(self):
        db.session.delete(self)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception('Failed to delete Queue entry')
            raise

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)