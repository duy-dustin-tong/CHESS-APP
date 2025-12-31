# Consolidated users views (clean single copy)
from flask_restx import Resource, Namespace, fields
from http import HTTPStatus
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.exceptions import NotFound
from sqlalchemy.exc import IntegrityError
import logging

from ..models.users import User
from ..models.games import Game
from ..models.elo import EloEntry
from flask import request
from werkzeug.security import generate_password_hash
from ..models.friendships import Friendship
from ..models.friendships import FriendshipStatus
from ..models.moves import Move
from ..utils import db
from sqlalchemy import func

logger = logging.getLogger(__name__)


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

game_list_model = users_namespace.model('GameListElement', {
    'id': fields.Integer(description='Game ID'),
    'in_progress': fields.Boolean(description='Is the game in progress'),
    'white_user_id': fields.Integer(description='White Player User ID'),
    'black_user_id': fields.Integer(description='Black Player User ID'),
    'white_username': fields.String(description='White Player Username'),
    'black_username': fields.String(description='Black Player Username'),
    'white_elo': fields.Integer(description='White Player ELO at game time'),
    'black_elo': fields.Integer(description='Black Player ELO at game time'),
    'created_at': fields.DateTime(description='Game creation timestamp'),
    'moves': fields.List(fields.String, description='List of moves in UCI format'),
    'winner_id': fields.Integer(description='Winner User ID, null if draw or ongoing'),
})


@users_namespace.route('/users/<int:user_id>')
class UserInfoAndStatus(Resource):
    
    def get(self, user_id):
        """ get user info and status """
        try:
            user = User.get_by_id(user_id)

            in_game = Game.query.filter(
                ((Game.white_user_id == user.id) | (Game.black_user_id == user.id)) &
                (Game.in_progress == True)
            ).first() is not None

            elo_entry = EloEntry.query.filter_by(user_id=user.id).order_by(EloEntry.created_at.desc()).first()
            elo = elo_entry.elo if elo_entry else 'N/A'

            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'in_game': in_game,
                'elo': elo
            }, HTTPStatus.OK
        except NotFound:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND
        except Exception as e:
            logger.exception('Unexpected error in UserInfoAndStatus.get')
            return {'message': 'Internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR


        
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
        except NotFound:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND

        try:
            if 'username' in data:
                user.username = data['username']
            if 'email' in data:
                user.email = data['email']
            if 'password' in data:
                user.password_hash = generate_password_hash(data['password'])

            try:
                user.save()
            except IntegrityError as ie:
                logger.exception('Integrity error updating user')
                return {'message': 'Username or email already taken'}, HTTPStatus.CONFLICT

            return {'message': 'User updated successfully'}, HTTPStatus.OK
        except Exception as e:
            logger.exception('Failed to update user')
            return {'message': 'Failed to update user', 'error': str(e)}, HTTPStatus.BAD_REQUEST


    @jwt_required()
    def delete(self, user_id):
        """delete user with user_id"""

        jwt_user_id = int(get_jwt_identity())
        if jwt_user_id != user_id:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED

        try:
            user = User.get_by_id(user_id)
        except NotFound:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND

        try:
            user.delete()
            return {'message': 'User deleted successfully'}, HTTPStatus.OK
        except Exception as e:
            logger.exception('Failed to delete user')
            return {'message': 'Failed to delete user'}, HTTPStatus.INTERNAL_SERVER_ERROR

@users_namespace.route('/users/<int:user_id>/friends')
class GetFriendsOfUser(Resource):
    

    def get(self, user_id):
        """ get json list of friends of user with user_id"""
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)

        # Base query for accepted friendships involving the user
        base_q = Friendship.query.filter(
            ((Friendship.user1_id == user_id) | (Friendship.user2_id == user_id)) &
            (Friendship.status == FriendshipStatus.ACCEPTED)
        ).order_by(Friendship.created_at.desc())

        total_count = base_q.count()

        if offset is not None:
            base_q = base_q.offset(offset)
        if limit is not None:
            base_q = base_q.limit(limit)

        friendListFetch = base_q.all()

        if not friendListFetch:
            return [], HTTPStatus.OK, {'X-Total-Count': total_count}

        # Determine friend user ids in the same order as friendships
        friendIds = [entry.user1_id if entry.user1_id != user_id else entry.user2_id for entry in friendListFetch]

        # Fetch users and elos in bulk to avoid N+1 queries
        users = User.query.filter(User.id.in_(friendIds)).all()

        # Map user id -> user object
        user_by_id = {u.id: u for u in users}

        elo_by_user = {}
        if friendIds:
            # subquery to get latest created_at per user
            latest_sq = db.session.query(
                EloEntry.user_id.label('user_id'),
                func.max(EloEntry.created_at).label('max_created')
            ).filter(EloEntry.user_id.in_(friendIds)).group_by(EloEntry.user_id).subquery()

            latest_elos = db.session.query(EloEntry).join(
                latest_sq,
                (EloEntry.user_id == latest_sq.c.user_id) & (EloEntry.created_at == latest_sq.c.max_created)
            ).all()

            for e in latest_elos:
                elo_by_user[e.user_id] = e.elo

        response = []
        for idx, friendship in enumerate(friendListFetch):
            fid = friendIds[idx]
            friend = user_by_id.get(fid)
            if not friend:
                continue
            response.append({
                'id': friend.id,
                'friendshipId': friendship.id,
                'username': friend.username,
                'elo': elo_by_user.get(friend.id, 'N/A')
            })

        return response, HTTPStatus.OK, {'X-Total-Count': total_count}

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

    @users_namespace.marshal_list_with(game_list_model)
    def get(self, user_id):
        """get game history for a user. Supports pagination via ?limit=&offset="""

        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)

        user = User.get_by_id(user_id)
        if not user:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND

        games_as_white = Game.query.filter_by(white_user_id=user_id)
        games_as_black = Game.query.filter_by(black_user_id=user_id)

        all_games_query = games_as_white.union_all(games_as_black).order_by(Game.created_at.desc())

        if offset is not None:
            all_games_query = all_games_query.offset(offset)
        if limit is not None:
            all_games_query = all_games_query.limit(limit)

        all_games = all_games_query.all()

        # Bulk-fetch related data to avoid N+1 queries
        game_ids = [g.id for g in all_games]

        # Moves grouped by game_id
        moves_q = Move.query.filter(Move.game_id.in_(game_ids)).order_by(Move.move_number).all() if game_ids else []
        moves_by_game = {}
        for m in moves_q:
            moves_by_game.setdefault(m.game_id, []).append(m.uci)

        # Fetch all involved users in bulk
        user_ids = set()
        for g in all_games:
            user_ids.add(g.white_user_id)
            user_ids.add(g.black_user_id)
        users = User.query.filter(User.id.in_(list(user_ids))).all() if user_ids else []
        username_by_id = {u.id: u.username for u in users}

        # Fetch Elo entries tied to these games (game-specific elos)
        elo_entries = EloEntry.query.filter(EloEntry.game_id.in_(game_ids)).all() if game_ids else []
        elo_by_user_game = {}
        for e in elo_entries:
            elo_by_user_game[(e.user_id, e.game_id)] = e.elo

        all_games_formatted = []
        for game in all_games:
            moves = moves_by_game.get(game.id, [])
            white_username = username_by_id.get(game.white_user_id)
            black_username = username_by_id.get(game.black_user_id)
            white_elo = elo_by_user_game.get((game.white_user_id, game.id))
            black_elo = elo_by_user_game.get((game.black_user_id, game.id))

            game_data = {
                'id': game.id,
                'in_progress': game.in_progress,
                'white_user_id': game.white_user_id,
                'black_user_id': game.black_user_id,
                'white_username': white_username,
                'black_username': black_username,
                'white_elo': white_elo,
                'black_elo': black_elo,
                'created_at': game.created_at,
                'moves': moves,
                'winner_id': game.winner_id
            }
            all_games_formatted.append(game_data)

        return all_games_formatted, HTTPStatus.OK


@users_namespace.route('/users/search')
class SearchUsers(Resource):

    def get(self):
        """Search users by username prefix. Query params: q, limit, offset"""
        q = request.args.get('q', '').strip()
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)

        if q == '':
            return {'message': 'Query parameter q required'}, HTTPStatus.BAD_REQUEST

        base_q = User.query.filter(User.username.ilike(f"{q}%")).order_by(User.username.asc())

        total_count = base_q.count()

        if offset is not None:
            base_q = base_q.offset(offset)
        if limit is not None:
            base_q = base_q.limit(limit)

        users = base_q.all()

        result = []
        user_ids = [u.id for u in users]

        elo_by_user = {}
        if user_ids:
            latest_sq = db.session.query(
                EloEntry.user_id.label('user_id'),
                func.max(EloEntry.created_at).label('max_created')
            ).filter(EloEntry.user_id.in_(user_ids)).group_by(EloEntry.user_id).subquery()

            latest_elos = db.session.query(EloEntry).join(
                latest_sq,
                (EloEntry.user_id == latest_sq.c.user_id) & (EloEntry.created_at == latest_sq.c.max_created)
            ).all()

            for e in latest_elos:
                elo_by_user[e.user_id] = e.elo

        for u in users:
            result.append({'id': u.id, 'username': u.username, 'elo': elo_by_user.get(u.id, 'N/A')})

        return result, HTTPStatus.OK, {'X-Total-Count': total_count}



