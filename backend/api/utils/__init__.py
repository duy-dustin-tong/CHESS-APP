# backend/api/utils/__init__.py
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, leave_room

db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")


@socketio.on('register_user')
def on_register(data):
    user_id = data.get('userId')
    if user_id:
        room_name = f"user_{user_id}"
        join_room(room_name)
        print(f"Socket: User {user_id} joined room {room_name}")

@socketio.on('deregister_user')
def on_deregister(data):
    user_id = data.get('userId')
    if user_id:
        room_name = f"user_{user_id}"
        leave_room(room_name)
        print(f"Socket: User {user_id} left room {room_name}")


@socketio.on('join_game')
def on_join_game(data):
    game_id = data.get('gameId')
    if game_id:
        room_name = f"game_{game_id}"
        join_room(room_name)
        print(f"Socket: Player joined shared room {room_name}")

@socketio.on('leave_game')
def handle_leave_game(data):
    game_id = data.get('game_id')
    room = f"game_{game_id}"
    leave_room(room)
    print(f"User left room: {room}")