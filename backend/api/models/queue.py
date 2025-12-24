# backend/api/models/queue.py
from ..utils import db
from datetime import datetime

class Queue(db.Model):
    __tablename__ = 'queue'
    id = db.Column(db.Integer(), primary_key=True, index=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"Queue Entry {self.id} | User ID: {self.user_id}"
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)