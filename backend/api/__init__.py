# backend/api/__init__.py
from flask import Flask
from flask_restx import Api
from .auth.views import auth_namespace
from .friendships.views import friendships_namespace
from .games.views import games_namespace
from .matchmaking.views import matchmaking_namespace
from .users.views import users_namespace
from .config.config import config_dict
from .utils import db, socketio
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from .models import users, games, friendships, userGames
from .challenges.views import challenge_namespace
from flask_cors import CORS


def create_app(config = config_dict['dev']):
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config)

    api = Api(app)

    api.add_namespace(auth_namespace)
    api.add_namespace(friendships_namespace)
    api.add_namespace(games_namespace)
    api.add_namespace(matchmaking_namespace)
    api.add_namespace(users_namespace)
    api.add_namespace(challenge_namespace)

    db.init_app(app)
    socketio.init_app(app)

    jwt = JWTManager(app)
    migrate = Migrate(app, db)

    @app.shell_context_processor
    def make_shell_context():
        return{
            'db': db
        }

    return app
