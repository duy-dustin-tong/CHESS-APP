# backend/api/utils/__init__.py
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, leave_room
from flask import session
from flask_jwt_extended import decode_token
import logging

logger = logging.getLogger(__name__)

db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")


@socketio.on('connect')
def handle_connect(auth):
    # Expect client to send { auth: { token: '<access_token>' } }
    token = None
    if isinstance(auth, dict):
        token = auth.get('token') or auth.get('access_token')

    if not token:
        raise ConnectionRefusedError('authorization required')

    try:
        decoded = decode_token(token)
        # flask-jwt-extended stores identity in 'sub'
        identity = decoded.get('sub') or decoded.get('identity')
        # attach identity to the session for this socket connection
        session['user_id'] = int(identity) if identity is not None else None
        if session.get('user_id'):
            join_room(f"user_{session['user_id']}")
            logger.info("Socket: authenticated connection for user %s", session['user_id'])
    except Exception as exc:
        logger.exception('Socket connect authentication failed')
        raise ConnectionRefusedError('invalid token')



@socketio.on('join_game')
def on_join_game(data):
    game_id = data.get('gameId')
    if game_id:
        room_name = f"game_{game_id}"
        join_room(room_name)
        logger.info("Socket: Player joined shared room %s", room_name)


@socketio.on('leave_game')
def handle_leave_game(data):
    game_id = data.get('game_id')
    room = f"game_{game_id}"
    leave_room(room)
    logger.info("User left room: %s", room)