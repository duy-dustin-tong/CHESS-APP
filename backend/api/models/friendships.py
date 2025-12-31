# backend/api/models/friendships.py
from ..utils import db
import json
from datetime import datetime
from enum import Enum

class FriendshipStatus(Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'

class Friendship(db.Model):
    __tablename__ = 'friendships'
    id = db.Column(db.Integer(), primary_key=True, index=True)
    user1_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)
    user2_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)
    status = db.Column(db.Enum(FriendshipStatus), default=FriendshipStatus.PENDING, nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"Friendship {self.id} | Requester: {self.user1_id} | Addressee: {self.user2_id} | Status: {self.status.value}"
    
    def save(self):
        self
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)
    
    @classmethod
    def get_friendship(cls, user1_id, user2_id):
        return cls.query.filter_by(user1_id=user1_id, user2_id=user2_id).first()