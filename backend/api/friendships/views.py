from flask_restx import Resource, Namespace, fields
from http import HTTPStatus
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.friendships import Friendship

friendships_namespace = Namespace('friendships', description = "friendship namespace")

friendship_model = friendships_namespace.model('Friendship', {
    'user1_id': fields.Integer(required=True, description='User 1 ID'),
    'user2_id': fields.Integer(required=True, description='User 2 ID'),
    'status': fields.String(required=False, description='Friendship status', enum=['pending', 'accepted', 'rejected']),
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


        current_user_id = int(get_jwt_identity())
        if current_user_id != user1_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED
        
        # Logic to create a friendship entry goes here
        entry = Friendship(
            user1_id=user1_id, 
            user2_id=user2_id
        )
        entry.save()

        return entry, HTTPStatus.CREATED

@friendships_namespace.route('/friendships/<int:friendship_id>')
class UpdateDeleteEntry(Resource):

    @jwt_required()
    @friendships_namespace.marshal_with(friendship_model)
    def put(self, friendship_id):
        """accept a friend request"""

        current_user_id = int(get_jwt_identity())
        friendship = Friendship.get_by_id(friendship_id)

        if current_user_id != friendship.user2_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED

        friendship.status = 'accepted'
        friendship.save()

        return friendship, HTTPStatus.OK

    @jwt_required()
    @friendships_namespace.marshal_with(friendship_model)
    def delete(self, friendship_id):
        """reject or cancel a friend request"""
        current_user_id = int(get_jwt_identity())
        friendship = Friendship.get_by_id(friendship_id)

        if current_user_id != friendship.user2_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED

        friendship.status = 'rejected'
        friendship.delete()

        return friendship, HTTPStatus.GONE