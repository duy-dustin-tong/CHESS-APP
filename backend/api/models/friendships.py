# backend/api/models/friendships.py
from ..utils import db
from datetime import datetime
from enum import Enum
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)


class FriendshipStatus(Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'


class Friendship(db.Model):
    __tablename__ = 'friendships'
    __table_args__ = (db.UniqueConstraint('user1_id', 'user2_id', name='uq_friendship_pair'),)

    id = db.Column(db.Integer(), primary_key=True, index=True)
    user1_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)
    user2_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)
    status = db.Column(db.Enum(FriendshipStatus), default=FriendshipStatus.PENDING, nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"Friendship {self.id} | Requester: {self.user1_id} | Addressee: {self.user2_id} | Status: {self.status.value}"

    def save(self):
        # Normalize ordering so (user1_id, user2_id) is consistent for uniqueness
        if self.user1_id and self.user2_id and self.user1_id > self.user2_id:
            self.user1_id, self.user2_id = self.user2_id, self.user1_id

        db.session.add(self)
        try:
            db.session.commit()
        except IntegrityError as ie:
            db.session.rollback()
            logger.exception('IntegrityError saving Friendship')
            raise
        except Exception as e:
            db.session.rollback()
            logger.exception('Unexpected error saving Friendship')
            raise

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)

    @classmethod
    def get_friendship(cls, user1_id, user2_id):
        return cls.query.filter_by(user1_id=user1_id, user2_id=user2_id).first()