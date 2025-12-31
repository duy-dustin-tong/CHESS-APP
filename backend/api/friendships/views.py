# backend/api/friendships/views.py
from flask_restx import Resource, Namespace, fields
from http import HTTPStatus
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from ..models.friendships import Friendship, FriendshipStatus
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import NotFound
import logging

logger = logging.getLogger(__name__)

friendships_namespace = Namespace('friendships', description = "friendship namespace")

friendship_model = friendships_namespace.model('Friendship', {
    'user1_id': fields.Integer(required=True, description='User 1 ID'),
    'user2_id': fields.Integer(required=True, description='User 2 ID'),
})



@friendships_namespace.route('/friendships')
class CreateAnEntry(Resource):
    @jwt_required()
    @friendships_namespace.expect(friendship_model)
    @friendships_namespace.marshal_with(friendship_model)
    def post(self):
        """create a friendship entry"""
        data = request.get_json()
        user1_id = data.get('user1_id')
        user2_id = data.get('user2_id')
        # basic validation
        if user1_id is None or user2_id is None:
            return {'message': 'Both user1_id and user2_id are required'}, HTTPStatus.BAD_REQUEST
        try:
            user1_id = int(user1_id)
            user2_id = int(user2_id)
        except (TypeError, ValueError):
            return {'message': 'Invalid user ids'}, HTTPStatus.BAD_REQUEST

        if user1_id == user2_id:
            return {'message': 'Cannot befriend yourself'}, HTTPStatus.BAD_REQUEST

        current_user_id = int(get_jwt_identity())
        if current_user_id != user1_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED

        # Check if a friendship already exists in either ordering
        existing_friendship = Friendship.query.filter(
            ((Friendship.user1_id == user1_id) & (Friendship.user2_id == user2_id)) |
            ((Friendship.user1_id == user2_id) & (Friendship.user2_id == user1_id))
        ).first()

        if existing_friendship:
            # If there's a pending request in the opposite direction, inform client
            return {'message': 'You are already friends or a request already exists'}, HTTPStatus.CONFLICT

        entry = Friendship(
            user1_id=user1_id,
            user2_id=user2_id
        )
        try:
            entry.save()
        except IntegrityError:
            return {'message': 'Friendship already exists'}, HTTPStatus.CONFLICT
        except SQLAlchemyError:
            logger.exception('Database error creating friendship')
            return {'message': 'Database error'}, HTTPStatus.INTERNAL_SERVER_ERROR

        return entry, HTTPStatus.CREATED

@friendships_namespace.route('/friendships/<int:friendship_id>')
class UpdateDeleteEntry(Resource):

    @jwt_required()
    @friendships_namespace.marshal_with(friendship_model)
    def put(self, friendship_id):
        """accept a friend request"""

        current_user_id = int(get_jwt_identity())
        try:
            friendship = Friendship.get_by_id(friendship_id)
        except NotFound:
            return {'message': 'Friendship not found'}, HTTPStatus.NOT_FOUND
        except SQLAlchemyError:
            logger.exception('DB error fetching friendship')
            return {'message': 'Database error'}, HTTPStatus.INTERNAL_SERVER_ERROR

        if current_user_id != friendship.user2_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED
        if friendship.status == FriendshipStatus.ACCEPTED:
            return friendship, HTTPStatus.OK

        friendship.status = FriendshipStatus.ACCEPTED
        try:
            friendship.save()
        except IntegrityError:
            return {'message': 'Failed to accept request due to database constraint'}, HTTPStatus.INTERNAL_SERVER_ERROR
        except SQLAlchemyError:
            logger.exception('DB error accepting friendship')
            return {'message': 'Database error'}, HTTPStatus.INTERNAL_SERVER_ERROR

        return friendship, HTTPStatus.OK

    @jwt_required()
    @friendships_namespace.marshal_with(friendship_model)
    def delete(self, friendship_id):
        """reject or cancel a friend request"""
        current_user_id = int(get_jwt_identity())
        try:
            friendship = Friendship.get_by_id(friendship_id)
        except NotFound:
            return {'message': 'Friendship not found'}, HTTPStatus.NOT_FOUND
        except SQLAlchemyError:
            logger.exception('DB error fetching friendship')
            return {'message': 'Database error'}, HTTPStatus.INTERNAL_SERVER_ERROR

        if current_user_id != friendship.user1_id and current_user_id != friendship.user2_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED

        friendship.status = FriendshipStatus.REJECTED
        try:
            friendship.delete()
        except SQLAlchemyError:
            logger.exception('DB error deleting friendship')
            return {'message': 'Database error'}, HTTPStatus.INTERNAL_SERVER_ERROR

        return friendship, HTTPStatus.OK