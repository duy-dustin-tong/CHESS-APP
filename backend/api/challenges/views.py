# backend/api/challenges/views.py
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields
from flask import request
from http import HTTPStatus

from ..models.users import User
from ..models.challenges import Challenge
from ..models.friendships import Friendship, FriendshipStatus
from ..models.games import Game
from ..utils import db, socketio

challenge_namespace = Namespace('challenges', description='Challenge related operations')


challenge_model = challenge_namespace.model('Challenge', {
    'user1_id': fields.Integer(required=True, description='ID of the user who initiates the challenge'),
    'user2_id': fields.Integer(required=True, description='ID of the user who is being challenged'),
})

@challenge_namespace.route('/challenges')
class CreateDeleteChallenge(Resource):
    @challenge_namespace.expect(challenge_model)
    @jwt_required()
    def post(self):
        """challenge a friend"""
        data = request.get_json()
        user1_id = data.get('user1_id')
        user2_id = data.get('user2_id')

        user_id = int(get_jwt_identity())
        if user_id != user1_id and user_id != user2_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED

        friend_id = user2_id if user_id == user1_id else user1_id
        friendship_status = Friendship.query.filter(
            ((Friendship.user1_id == user_id) & (Friendship.user2_id == friend_id)) |
            ((Friendship.user1_id == friend_id) & (Friendship.user2_id == user_id))
        ).first()

        if not friendship_status or friendship_status.status != FriendshipStatus.ACCEPTED:
            return {'message': 'You are not friends with this user'}, HTTPStatus.BAD_REQUEST
        
        #check if friend is in another game
        ongoing_game = Game.query.filter(
            ((Game.white_user_id == friend_id) | (Game.black_user_id == friend_id) | (Game.white_user_id == user_id) | (Game.black_user_id == user_id)) &
            (Game.in_progress == True)
        ).first()

        if ongoing_game:
            return {'message': 'You or friend is already in an ongoing game'}, HTTPStatus.BAD_REQUEST

        existing_challenge = Challenge.query.filter_by(user1_id=user1_id).first()
        if existing_challenge:
            return {'message': 'You can only wait for 1 challenge at a time'}, HTTPStatus.BAD_REQUEST
        


        new_challenge = Challenge(
            user1_id=user1_id,
            user2_id=user2_id,
        )
        new_challenge.save()

        username = User.query.get(user1_id).username

        socketio.emit('friend_challenge_invite', {
            'challenge_id': new_challenge.id,
            'username' : username
        }, room=f"user_{friend_id}")

        return {'message': 'Friend challenged successfully'}, HTTPStatus.CREATED
    
    @jwt_required()
    def delete(self):

        user_id = int(get_jwt_identity())

        challenge = Challenge.query.filter_by(user1_id=user_id).first()
        if not challenge:
            return {'message': 'You havent made any challenges'}, HTTPStatus.OK

        challenge.delete()
        return {'message': 'Challenge deleted successfully'}, HTTPStatus.OK
    

@challenge_namespace.route('/challenges/pending')
class GetPendingChallenges(Resource):
    @jwt_required()
    def get(self):
        """Get all pending challenges for the current user"""
        user_id = int(get_jwt_identity())
        
        # Find challenges where I am the receiver
        challenges = Challenge.query.filter_by(user2_id=user_id).all()

        if not challenges:
            return [], HTTPStatus.OK

        sender_ids = [c.user1_id for c in challenges]
        senders = User.query.filter(User.id.in_(sender_ids)).all()
        senders_by_id = {s.id: s for s in senders}

        response = []
        for c in challenges:
            sender = senders_by_id.get(c.user1_id)
            response.append({
                # We use the same key names as the socket event for consistency
                'challenge_id': c.id,
                'username': sender.username if sender else 'Unknown',
            })

        return response, HTTPStatus.OK

@challenge_namespace.route('/respond_challenge/<int:challenge_id>/<string:response>')
class RespondChallenge(Resource):

    @jwt_required()
    def post(self, challenge_id, response):
        """Accept a challenge"""

        user_id = int(get_jwt_identity())
        challenge = Challenge.query.get(challenge_id)

        if not challenge:
            return {'message': 'Challenge not found'}, HTTPStatus.NOT_FOUND

        if user_id != challenge.user2_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED
        
        ongoing_game = Game.query.filter(
            ((Game.white_user_id == challenge.user1_id) | (Game.black_user_id == challenge.user1_id) | (Game.white_user_id == challenge.user2_id) | (Game.black_user_id == challenge.user2_id)) &
            (Game.in_progress == True)
        ).first()

        if ongoing_game:
            challenge.delete()
            return {'message': 'You or challenger is already in an ongoing game'}, HTTPStatus.BAD_REQUEST

        if response == 'accept':
            # Logic to create a game can be added here

            

            new_game = Game(
                white_user_id=challenge.user1_id,
                black_user_id=challenge.user2_id,
                in_progress=True
            )

            new_game.save()

            socketio.emit('start_challenge', {
                'game_id': new_game.id
            }, room=f"user_{challenge.user1_id}")

            socketio.emit('start_challenge', {
                'game_id': new_game.id
            }, room=f"user_{challenge.user2_id}")

            challenge.delete()
            return {'message': 'Challenge accepted'}, HTTPStatus.OK
        elif response == 'decline':
            challenge.delete()
            return {'message': 'Challenge declined'}, HTTPStatus.OK
        else:
            return {'message': 'Invalid response'}, HTTPStatus.BAD_REQUEST