# backend/api/models/challenges.py
from ..utils import db
from datetime import datetime

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
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)