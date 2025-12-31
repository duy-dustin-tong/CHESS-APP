# backend/api/games/views.py
from flask_restx import Resource, Namespace, fields
from http import HTTPStatus
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request

from ..models.users import User
from ..models.games import Game
from ..models.friendships import Friendship, FriendshipStatus
from ..models.moves import Move
from ..models.elo import EloEntry
from ..models.challenges import Challenge
from ..utils import db, socketio
from ..utils.eloChange import calculate_new_elo_pair_after_draw, calculate_new_elo_pair_after_win
import chess
from datetime import datetime
import logging
import functools
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

def handle_db_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.exception('Database error in %s', func.__name__)
            try:
                db.session.rollback()
            except Exception:
                pass
            return {'message': 'Database error'}, HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception as e:
            logger.exception('Unexpected error in %s', func.__name__)
            return {'message': 'Internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR
    return wrapper
from sqlalchemy import func

games_namespace = Namespace('games', description= "games namespace")


def get_latest_elo_map(user_ids):
    """Return a map user_id -> latest EloEntry for the given user_ids."""
    if not user_ids:
        return {}
    latest_sq = db.session.query(
        EloEntry.user_id.label('user_id'),
        func.max(EloEntry.created_at).label('max_created')
    ).filter(EloEntry.user_id.in_(user_ids)).group_by(EloEntry.user_id).subquery()

    latest_elos = db.session.query(EloEntry).join(
        latest_sq,
        (EloEntry.user_id == latest_sq.c.user_id) & (EloEntry.created_at == latest_sq.c.max_created)
    ).all()

    return {e.user_id: e for e in latest_elos}


game_model = games_namespace.model('Game', {
    'id': fields.Integer(description='Game ID'),
    'in_progress': fields.Boolean(description='Is the game in progress'),
    'current_fen': fields.String(description='Current FEN string of the game'),
    'white_user_id': fields.Integer(description='White Player User ID'),
    'black_user_id': fields.Integer(description='Black Player User ID'),
    'white_time_left': fields.Integer(),
    'black_time_left': fields.Integer(),
    'created_at': fields.DateTime(description='Game creation timestamp'),
    'updated_at': fields.DateTime(description='Game last update timestamp'),
})



draw_response_model = games_namespace.model('DrawResponse', {
    'accept': fields.Boolean(required=True, description='Accept or reject the draw offer'),
})


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

    @handle_db_errors
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

        game.draw_offer_from = None  # Clear any existing draw offers on move

        board = chess.Board(game.current_fen) if game.current_fen else chess.Board()
        
        
        current_turn_user_id = game.white_user_id if board.turn == chess.WHITE else game.black_user_id

        if user_id != current_turn_user_id:
            return {'message': "It is not your turn"}, HTTPStatus.FORBIDDEN
        
        
        # 2. Update Clocks
        
        now = datetime.utcnow()
        seconds_elapsed = int((now - game.updated_at).total_seconds())

        # If it was white's turn, subtract time from white
        if board.turn == chess.WHITE:
            game.white_time_left = max(0, game.white_time_left - seconds_elapsed)
        else:
            game.black_time_left = max(0, game.black_time_left - seconds_elapsed)
        
        # Check for time-out
        if game.white_time_left <= 0 or game.black_time_left <= 0:
            game.in_progress = False
            game.winner_id = game.black_user_id if game.white_time_left <= 0 else game.white_user_id
            reason = "Time out"

            elo_map = get_latest_elo_map([game.black_user_id, game.white_user_id])
            black_elo_entry = elo_map.get(game.black_user_id)
            white_elo_entry = elo_map.get(game.white_user_id)
            new_elos = calculate_new_elo_pair_after_win(black_elo_entry.elo, white_elo_entry.elo, game.winner_id == game.black_user_id)

            if(board.is_insufficient_material()):
                game.winner_id = None  # Draw due to insufficient material
                reason = "Draw due to insufficient material"
                new_elos = calculate_new_elo_pair_after_draw(black_elo_entry.elo, white_elo_entry.elo)
            
            new_black_elo = EloEntry(
                user_id=game.black_user_id,
                game_id=game.id,
                elo=new_elos[0]
            )
            new_white_elo = EloEntry(
                user_id=game.white_user_id,
                game_id=game.id,
                elo=new_elos[1]
            )
            new_black_elo.save()
            new_white_elo.save()

            game.save()

            socketio.emit('game_over', {
                'winner_id': game.winner_id,
                'reason': reason
            }, to=f"game_{game_id}")


            return game, HTTPStatus.OK
        
        
        
        
        
        
        # 3. Validate and Push Move
        try:
            # move is expected in UCI format like "e2e4"
            chess_move = chess.Move.from_uci(move)
            if chess_move in board.legal_moves:
                board.push(chess_move)
            else:
                return {'message': 'Illegal move'}, HTTPStatus.BAD_REQUEST
        except ValueError:
            return {'message': 'Invalid move format (use UCI)'}, HTTPStatus.BAD_REQUEST
        
        # 4. Update Game Object
        game.current_fen = board.fen()
        

        new_move = Move(
            game_id=game.id,
            move_number=Move.query.filter_by(game_id=game.id).count() + 1,
            uci=move
        )

        new_move.save()


            


        # 5. Check for Game End (Checkmate/Draw)
        if board.is_game_over():
            game.in_progress = False

            elo_map = get_latest_elo_map([game.black_user_id, game.white_user_id])
            black_elo_entry = elo_map.get(game.black_user_id)
            white_elo_entry = elo_map.get(game.white_user_id)
            new_elos = None


            if board.is_checkmate():
                # The winner is the one who just moved
                game.winner_id = user_id
                new_elos = calculate_new_elo_pair_after_win(black_elo_entry.elo, white_elo_entry.elo, game.winner_id == game.black_user_id)
            else:
                # Draw
                game.winner_id = None
                new_elos = calculate_new_elo_pair_after_draw(black_elo_entry.elo, white_elo_entry.elo)
            
            new_black_elo = EloEntry(
                user_id=game.black_user_id,
                game_id=game.id,
                elo=new_elos[0]
            )

            new_white_elo = EloEntry(
                user_id=game.white_user_id,
                game_id=game.id,
                elo=new_elos[1]
            )

            new_black_elo.save()
            new_white_elo.save()

        

        game.save()

        # 6. Socket Emit
        # We send the FEN and the UCI move to the game room
        socketio.emit('move_made', {
            'move': move,
            'current_fen': game.current_fen,
            'is_game_over': not game.in_progress,
            #'winner_id': getattr(game, 'winner_id', None)
            'white_time_left': game.white_time_left,
            'black_time_left': game.black_time_left
        }, to=f"game_{game_id}")


        # ADD THIS: Explicitly emit game_over if the board is done
        if not game.in_progress:
            reason = "draw"
            if board.is_checkmate():
                reason = "checkmate"

            elif game.white_time_left <= 0 or game.black_time_left <= 0:
                reason = "time_out"
            
            socketio.emit('game_over', {
                'winner_id': game.winner_id,
                'reason': reason
            }, to=f"game_{game_id}")


            return game, HTTPStatus.OK

@games_namespace.route('/games/<int:game_id>/resign')
class Resign(Resource):

    @handle_db_errors
    @jwt_required()
    @games_namespace.marshal_with(game_model)
    def post(self, game_id):
        """resigns the game"""

        game = Game.get_by_id(game_id)
        if not game:
            return {'message': 'Game not found'}, HTTPStatus.NOT_FOUND
        if not game.in_progress:
            return {'message': 'Game has already ended'}, HTTPStatus.BAD_REQUEST
        
        user_id = int(get_jwt_identity())
        if user_id != game.white_user_id and user_id != game.black_user_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED
        
        game.winner_id = game.black_user_id if user_id == game.white_user_id else game.white_user_id

        game.in_progress = False
        game.win_by_resignation = True
        game.save()

        # Update Elo elos (batch fetch latest entries)
        elo_map = get_latest_elo_map([game.black_user_id, game.white_user_id])
        black_elo_entry = elo_map.get(game.black_user_id)
        white_elo_entry = elo_map.get(game.white_user_id)
        new_elos = calculate_new_elo_pair_after_win(black_elo_entry.elo, white_elo_entry.elo, game.winner_id == game.black_user_id)

        

        new_black_elo = EloEntry(
            user_id=game.black_user_id,
            game_id=game.id,
            elo=new_elos[0]
        )
        new_white_elo = EloEntry(
            user_id=game.white_user_id,
            game_id=game.id,
            elo=new_elos[1]
        )

        
        new_black_elo.save()
        new_white_elo.save()

        socketio.emit('game_over', {
            'winner_id': game.winner_id,
            'reason': 'resignation'
        }, to=f"game_{game_id}")

        return game, HTTPStatus.OK

@games_namespace.route('/games/<int:game_id>/offer-draw')
class OfferDraw(Resource):

    @handle_db_errors
    @jwt_required()
    def post(self, game_id):
        """offer a draw"""

        user_id = int(get_jwt_identity())

        game = Game.get_by_id(game_id)
        if not game:
            return {'message': 'Game not found'}, HTTPStatus.NOT_FOUND
        if not game.in_progress:
            return {'message': 'Game has already ended'}, HTTPStatus.BAD_REQUEST

        game.draw_offer_from = user_id
        game.save()

        socketio.emit('draw_offered', {
            'offerer_id': user_id
        }, to=f"game_{game_id}")

        return {'message': 'Draw offer sent'}, HTTPStatus.OK
    
@games_namespace.route('/games/<int:game_id>/respond-draw')
class RespondDraw(Resource):

    @handle_db_errors
    @jwt_required()
    @games_namespace.expect(draw_response_model)
    @games_namespace.marshal_with(game_model)
    def post(self, game_id):
        """accept a draw"""

        data = request.get_json()
        accepted = data.get('accepted')

        game = Game.get_by_id(game_id)
        if not game:
            return {'message': 'Game not found'}, HTTPStatus.NOT_FOUND
        if not game.in_progress:
            return {'message': 'Game has already ended'}, HTTPStatus.BAD_REQUEST
        
        user_id = int(get_jwt_identity())
        if (user_id != game.white_user_id and user_id != game.black_user_id) or game.draw_offer_from == user_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED
        

        
        if not accepted:
            game.draw_offer_from = None
            game.save()
            socketio.emit('draw_declined', {}, to=f"game_{game_id}")
            return {'message': 'Draw declined'}, HTTPStatus.OK
        
        game.in_progress = False
        game.winner_id = None  # Draw
        game.save()

        elo_map = get_latest_elo_map([game.black_user_id, game.white_user_id])
        black_elo_entry = elo_map.get(game.black_user_id)
        white_elo_entry = elo_map.get(game.white_user_id)

        new_elos = calculate_new_elo_pair_after_draw(black_elo_entry.elo, white_elo_entry.elo)

        new_black_elo = EloEntry(
            user_id=game.black_user_id,
            game_id=game.id,
            elo=new_elos[0]
        )

        new_white_elo = EloEntry(
            user_id=game.white_user_id,
            game_id=game.id,
            elo=new_elos[1]
        )
        
        new_black_elo.save()
        new_white_elo.save()

        socketio.emit('game_over', {
            'winner_id': None,
            'reason': 'draw_agreement'
        }, to=f"game_{game_id}")

        return game, HTTPStatus.OK


@games_namespace.route('/games/<int:game_id>/claim-timeout')
class ClaimTimeout(Resource):
    @handle_db_errors
    @jwt_required()
    def post(self, game_id):
        game = Game.get_by_id(game_id)
        if not game.in_progress:
            return {'message': 'Game already ended'}, HTTPStatus.BAD_REQUEST

        now = datetime.utcnow()
        seconds_elapsed = int((now - game.updated_at).total_seconds())
        
        board = chess.Board(game.current_fen)
        
        # Calculate current actual time
        w_time = game.white_time_left - (seconds_elapsed if board.turn == chess.WHITE else 0)
        b_time = game.black_time_left - (seconds_elapsed if board.turn == chess.BLACK else 0)

        if w_time <= 0 or b_time <= 0:
            game.in_progress = False
            game.winner_id = game.black_user_id if w_time <= 0 else game.white_user_id
            reason = "Time out"

            game.save()
            
            # Update Elo elos
            elo_map = get_latest_elo_map([game.black_user_id, game.white_user_id])
            black_elo_entry = elo_map.get(game.black_user_id)
            white_elo_entry = elo_map.get(game.white_user_id)
            new_elos = calculate_new_elo_pair_after_win(black_elo_entry.elo, white_elo_entry.elo, game.winner_id == game.black_user_id)
            
            if(board.is_insufficient_material()):
                game.winner_id = None  # Draw due to insufficient material
                reason = "Draw due to insufficient material"
                new_elos = calculate_new_elo_pair_after_draw(black_elo_entry.elo, white_elo_entry.elo)

            new_black_elo = EloEntry(
                user_id=game.black_user_id,
                game_id=game.id,
                elo=new_elos[0]
            )       
            new_white_elo = EloEntry(
                user_id=game.white_user_id,
                game_id=game.id,
                elo=new_elos[1]
            )
            new_black_elo.save()
            new_white_elo.save()


            
            socketio.emit('game_over', {
                'winner_id': game.winner_id,
                'reason': reason
            }, to=f"game_{game_id}")
            return {'message': 'timeout claimed'}, HTTPStatus.OK
            
        return {'message': 'Time has not expired yet'}, HTTPStatus.BAD_REQUEST


    