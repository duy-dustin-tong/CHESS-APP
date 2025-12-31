# backend/api/models/users.py
from ..utils import db
from sqlalchemy.dialects.postgresql import JSONB
import json
from datetime import datetime
import logging
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True, index=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"User {self.id} | Username: {self.username} | Email: {self.email}"
    
    def save(self):
        self.updated_at = datetime.utcnow()
        db.session.add(self)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            logger.exception('IntegrityError saving User')
            raise
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('Database error saving User')
            raise
        except Exception:
            db.session.rollback()
            logger.exception('Unexpected error saving User')
            raise

    def delete(self):
        db.session.delete(self)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception('Failed to delete User')
            raise

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)
    
    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()