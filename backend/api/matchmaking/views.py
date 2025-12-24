# backend/api/matchmaking/views.py
from flask_restx import Resource, Namespace, fields
from http import HTTPStatus
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request
from ..models.queue import Queue
from ..models.games import Game
from ..utils import db, socketio
import threading

# Simple process-local lock to serialize pairing operations.
# This is safe for a single-process dev server. For production use
# prefer Redis or database-level locking.
pair_lock = threading.Lock()

matchmaking_namespace = Namespace('matchmaking', description = "matchmaking namespace")



@matchmaking_namespace.route('/matchmaking')
class MatchMaking(Resource):
    @jwt_required()
    def post(self):
        """join the queue"""

        user_id = int(get_jwt_identity())
        #check if user is already in queue

        existing_entry = Queue.query.filter_by(user_id=user_id).first()
        if existing_entry:
            return {'message': f'User already in queue'}, HTTPStatus.BAD_REQUEST

        #check if user is already in a game
        ongoing_game = Game.query.filter(
            ((Game.white_user_id == user_id) | (Game.black_user_id == user_id)) &
            (Game.in_progress == True)
        ).first()
        if ongoing_game:
            return {'message': 'User is already in an ongoing game'}, HTTPStatus.BAD_REQUEST
        #if not, add to queue
        new_entry = Queue(user_id=user_id)
        new_entry.save()

        # Try to pair the first two users in queue. Use a lock to avoid races
        # on a single-process server. We remove the two queue entries and
        # create a Game for them inside the lock.
        paired_game = None
        with pair_lock:
            # fetch two earliest entries
            entries = Queue.query.order_by(Queue.created_at.asc()).limit(2).all()
            if len(entries) >= 2:
                u1 = entries[0].user_id
                u2 = entries[1].user_id
                try:
                    # create the game (white = first queued)
                    game = Game(white_user_id=u1, black_user_id=u2)
                    db.session.add(game)
                    # remove the two queue entries
                    for e in entries:
                        db.session.delete(e)
                    db.session.commit()
                    paired_game = game

                    # --- SOCKET NOTIFICATION START ---
                    
                    # 1. Notify the WAITING user (u1)
                    # They are sitting on the 'waiting' screen. This forces the redirect.
                    socketio.emit('start_game', {
                        'game_id': game.id,
                        'opponent': u2,
                        'color': 'white'
                    }, to=f"user_{u1}")

                    # 2. Notify the CURRENT user (u2)
                    # Ideally, their HTTP response handles the redirect, but 
                    # sending a socket event to them too ensures consistency 
                    # (e.g., if they have multiple tabs open).
                    socketio.emit('start_game', {
                        'game_id': game.id,
                        'opponent': u1,
                        'color': 'black'
                    }, to=f"user_{u2}")

                    # --- SOCKET NOTIFICATION END ---
                except Exception as e:
                    print(f"Matchmaking Error: {e}")
                    db.session.rollback()

        if paired_game:
            return {
                'message': 'Paired',
                'game_id': paired_game.id,
                'white_user_id': paired_game.white_user_id,
                'black_user_id': paired_game.black_user_id
            }, HTTPStatus.CREATED

        return {'message': 'User added to queue'}, HTTPStatus.CREATED

    @jwt_required()
    def delete(self):
        """leave the queue"""
        user_id = int(get_jwt_identity())
        existing_entry = Queue.query.filter_by(user_id=user_id).first()
        if not existing_entry:
            return {'message': 'User not in queue'}, HTTPStatus.BAD_REQUEST
        existing_entry.delete()
        return {'message': 'User removed from queue'}, HTTPStatus.OK


@matchmaking_namespace.route('/status')
class MatchStatus(Resource):
    @jwt_required()
    def get(self):
        """Check whether the current user has been paired into a game."""
        user_id = int(get_jwt_identity())
        # look for an in-progress game where the user is white or black
        game = Game.query.filter(
            (Game.white_user_id == user_id) | (Game.black_user_id == user_id)
        ).filter_by(in_progress=True).first()

        if not game:
            return {'paired': False}, HTTPStatus.OK

        return {
            'paired': True,
            'game_id': game.id,
            'white_user_id': game.white_user_id,
            'black_user_id': game.black_user_id
        }, HTTPStatus.OK

