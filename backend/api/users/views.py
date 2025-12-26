# backend/api/users/views.py
from flask_restx import Resource, Namespace, fields
from http import HTTPStatus
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.users import User
from ..models.games import Game
from ..models.elo import EloEntry
from flask import request
from werkzeug.security import generate_password_hash
from ..models.friendships import Friendship
from ..models.friendships import FriendshipStatus

users_namespace = Namespace('users', description = "namespace for users")

user_model = users_namespace.model('User', {
    'id': fields.Integer(required=True, description='User ID'), 
    'username': fields.String(required=True, description='Username'),
    'elo': fields.Integer(required=True, description='Elo Rating'),
    'in_game': fields.Boolean(required=True, description='Is user currently in a game'),
})

user_update_model = users_namespace.model('UserUpdate', {
    'username': fields.String(required=False, description='Username'),
    'email': fields.String(required=False, description='Email'),
    'password': fields.String(required=False, description='Password'),
})


@users_namespace.route('/users/<int:user_id>')
class UserInfoAndStatus(Resource):


    @users_namespace.marshal_with(user_model)
    def get(self, user_id):
        """ get user info and status """

        try:
            user = User.get_by_id(user_id)

            in_game = Game.query.filter(
                ((Game.white_user_id == user.id) | (Game.black_user_id == user.id)) &
                (Game.in_progress == True) 
            ).first() is not None

            elo = EloEntry.query.filter_by(user_id=user.id).order_by(EloEntry.created_at.desc()).first()

            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'in_game': in_game,
                'elo': elo
            }, HTTPStatus.OK
        except:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND


        
    @jwt_required()
    @users_namespace.expect(user_update_model)
    def put(self, user_id):
        """ update user info and status """

        jwt_user_id = int(get_jwt_identity())

        if jwt_user_id != user_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED

        data = request.get_json()

        try:
            user = User.get_by_id(user_id)

            try:
                if 'username' in data:
                    user.username = data['username']
                if 'email' in data:
                    user.email = data['email']
                if 'password' in data:
                    user.password_hash = generate_password_hash(data['password'])  # In real implementation, hash the password

                user.save()

                return {'message': 'User updated successfully'}, HTTPStatus.OK
            except Exception as e:
                return {'message': 'Failed to update user', 'error': str(e)}, HTTPStatus.BAD_REQUEST

        except:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND


    @jwt_required()
    def delete(self, user_id):
        """delete user with user_id"""

        jwt_user_id = int(get_jwt_identity())
        if jwt_user_id != user_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED

        try:
            user = User.get_by_id(user_id)
            user.delete()
            return {'message': 'User deleted successfully'}, HTTPStatus.OK
        except:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND

@users_namespace.route('/users/<int:user_id>/friends')
class GetFriendsOfUser(Resource):
    

    def get(self, user_id):
        """ get json list of friends of user with user_id"""
        
        friendListFetch = Friendship.query.filter(
            ((Friendship.user1_id == user_id) | (Friendship.user2_id == user_id)) &
            (Friendship.status == FriendshipStatus.ACCEPTED)
        ).all()

        friendIds = [entry.user1_id if entry.user1_id != user_id else entry.user2_id for entry in friendListFetch]

        if not friendIds:
            return [], HTTPStatus.OK

        friends = User.query.filter(User.id.in_(friendIds)).all()

        def get_elo(user_id):
            elo_entry = EloEntry.query.filter_by(user_id=user_id).order_by(EloEntry.created_at.desc()).first()
            return elo_entry.elo if elo_entry else 'N/A'  # Default Elo if none found



        return [{'id': friend.id, 'username': friend.username, 'elo': get_elo(friend.id)} for friend in friends], HTTPStatus.OK

@users_namespace.route('/users/<int:user_id>/friends/pending')
class GetPendingFriendsRequestsToUser(Resource):
    
    @jwt_required()
    def get(self, user_id):
        """ get json list of pending friend requests of user with user_id"""

        jwt_user_id = int(get_jwt_identity())
        if jwt_user_id != user_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED

        pendingFetch = Friendship.query.filter(
            (Friendship.user2_id == user_id) &
            (Friendship.status == FriendshipStatus.PENDING)
        ).all()

        pendingIds = [entry.user1_id for entry in pendingFetch]

        if not pendingIds:
            return [], HTTPStatus.OK

        pending = User.query.filter(User.id.in_(pendingIds)).all()

        response = []
        for i in range(len(pending)):
            friend = pending[i]
            response.append({
                'id': pendingFetch[i].id,
                'username': friend.username
            })

        return response, HTTPStatus.OK


@users_namespace.route('/users/<int:user_id>/history')
class GetGameHistoryOfUser(Resource):

    def get(self, user_id):
        """get completed game history of user with user_id"""

        gameHistory = Game.query.filter(
            ((Game.white_user_id == user_id) | (Game.black_user_id == user_id)) &
            (Game.in_progress == False)
        ).all()

        return [{'id': game.id, 'white_user_id': game.white_user_id, 'black_user_id': game.black_user_id, 'winner': game.winner} for game in gameHistory], HTTPStatus.OK



