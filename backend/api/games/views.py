from flask_restx import Resource, Namespace, fields
from http import HTTPStatus
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request
from ..models.games import Game
from ..models.friendships import Friendship

games_namespace = Namespace('games', description= "games namespace")

game_start_model = games_namespace.model('GameStart', {
    'white_user_id': fields.Integer(required=True, description='White Player User ID'),     
    'black_user_id': fields.Integer(required=True, description='Black Player User ID'),
})

game_model = games_namespace.model('Game', {
    'id': fields.Integer(description='Game ID'),
    'in_progress': fields.Boolean(description='Is the game in progress'),
    'moves': fields.String(description='Moves made in the game'),
    'current_fen': fields.String(description='Current FEN string of the game'),
    'white_user_id': fields.Integer(description='White Player User ID'),
    'black_user_id': fields.Integer(description='Black Player User ID'),
    'created_at': fields.DateTime(description='Game creation timestamp'),
    'updated_at': fields.DateTime(description='Game last update timestamp'),
})

@games_namespace.route('/games')
class CreateNewGameWithFriend(Resource):

    @games_namespace.expect(game_start_model)
    @games_namespace.marshal_with(game_model)
    @jwt_required()
    def post(self):
        """create a new game with a friend"""
        data = request.get_json()
        white_user_id = data.get('white_user_id')
        black_user_id = data.get('black_user_id')

        user_id = int(get_jwt_identity())
        if user_id != white_user_id and user_id != black_user_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED

        friend_id = black_user_id if user_id == white_user_id else white_user_id
        friendship_status = Friendship.query.filter(
            ((Friendship.user1_id == user_id) & (Friendship.user2_id == friend_id)) |
            ((Friendship.user1_id == friend_id) & (Friendship.user2_id == user_id))
        ).first()

        if not friendship_status or friendship_status.status != 'accepted':
            return {'message': 'You are not friends with this user'}, HTTPStatus.BAD_REQUEST
        
        #check if friend is in another game
        ongoing_game = Game.query.filter(
            ((Game.white_user_id == friend_id) | (Game.black_user_id == friend_id) | (Game.white_user_id == user_id) | (Game.black_user_id == user_id)) &
            (Game.in_progress == True)
        ).first()

        if ongoing_game:
            return {'message': 'You or friend is already in an ongoing game'}, HTTPStatus.BAD_REQUEST

        new_game = Game(
            white_user_id=white_user_id,
            black_user_id=black_user_id
        )
        new_game.save()
        return new_game, HTTPStatus.CREATED


@games_namespace.route('/games/<int:game_id>')
class GameStatus(Resource):

    @games_namespace.marshal_with(game_model)
    @jwt_required()
    def get(self, game_id):
        """get current state of game"""
        game = Game.get_by_id(game_id)

        if not game:
            return {'message': 'Game not found'}, HTTPStatus.NOT_FOUND

        user_id = int(get_jwt_identity())

        if user_id != game.white_user_id and user_id != game.black_user_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED

        return game, HTTPStatus.OK

@games_namespace.route('/games/<int:game_id>/<string:move>')
class MakeMove(Resource):

    @jwt_required()
    @games_namespace.marshal_with(game_model)
    def put(self, game_id, move):
        """make a move"""

        game = Game.get_by_id(game_id)
        if not game:
            return {'message': 'Game not found'}, HTTPStatus.NOT_FOUND
        
        if not game.in_progress:
            return {'message': 'Game has already ended'}, HTTPStatus.BAD_REQUEST

        user_id = int(get_jwt_identity())
        if user_id != game.white_user_id and user_id != game.black_user_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED
        # Here you would add logic to validate and make the move
        # For now, we just append the move to the moves list
        if game.moves:
            game.moves += f" {move}"
        game.save()
        return game, HTTPStatus.OK

@games_namespace.route('/games/<int:game_id>/resign')
class Resign(Resource):

    @jwt_required()
    @games_namespace.marshal_with(game_model)
    def post(self, game_id):
        """resigns the game"""

        game = Game.get_by_id(game_id)
        if not game:
            return {'message': 'Game not found'}, HTTPStatus.NOT_FOUND
        user_id = int(get_jwt_identity())
        if user_id != game.white_user_id and user_id != game.black_user_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED
        
        game.winner_id = game.black_user_id if user_id == game.white_user_id else game.white_user_id

        game.in_progress = False
        game.save()
        return game, HTTPStatus.OK

        

