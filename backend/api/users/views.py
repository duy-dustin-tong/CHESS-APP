# Consolidated users views (clean single copy)
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
from ..models.moves import Move


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

    @users_namespace.marshal_with(user_model)
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
                    user.password_hash = generate_password_hash(data['password'])

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
        """ get json list of friends of user with user_id. Supports pagination via ?limit=&offset="""

        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)

        friendship_query = Friendship.query.filter(
            ((Friendship.user1_id == user_id) | (Friendship.user2_id == user_id)) &
            (Friendship.status == FriendshipStatus.ACCEPTED)
        ).order_by(Friendship.id.desc())

        total_count = friendship_query.count()

        if offset is not None:
            friendship_query = friendship_query.offset(offset)
        if limit is not None:
            friendship_query = friendship_query.limit(limit)

        friend_entries = friendship_query.all()

        friend_ids = [entry.user1_id if entry.user1_id != user_id else entry.user2_id for entry in friend_entries]

        if not friend_ids:
            return [], HTTPStatus.OK, {'X-Total-Count': str(total_count)}

        friends = User.query.filter(User.id.in_(friend_ids)).all()
        friends_by_id = {f.id: f for f in friends}

        def get_elo(u_id):
            elo_entry = EloEntry.query.filter_by(user_id=u_id).order_by(EloEntry.created_at.desc()).first()
            return elo_entry.elo if elo_entry else 'N/A'

        result = []
        for fid in friend_ids:
            f = friends_by_id.get(fid)
            if not f:
                continue
            result.append({'id': f.id, 'username': f.username, 'elo': get_elo(f.id)})

        return result, HTTPStatus.OK, {'X-Total-Count': str(total_count)}


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

        total_count = games_as_white.count() + games_as_black.count()

        all_games_query = games_as_white.union_all(games_as_black).order_by(Game.created_at.desc())

        if offset is not None:
            all_games_query = all_games_query.offset(offset)
        if limit is not None:
            all_games_query = all_games_query.limit(limit)

        all_games = all_games_query.all()

        all_games_formatted = []
        for game in all_games:
            moves = [move.uci for move in Move.get_moves_by_game_id(game.id)]
            white_username = User.get_by_id(game.white_user_id).username
            black_username = User.get_by_id(game.black_user_id).username
            white_elo_entry = EloEntry.query.filter_by(user_id=game.white_user_id, game_id=game.id).first()
            black_elo_entry = EloEntry.query.filter_by(user_id=game.black_user_id, game_id=game.id).first()
            white_elo = white_elo_entry.elo if white_elo_entry else None
            black_elo = black_elo_entry.elo if black_elo_entry else None
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

        return all_games_formatted, HTTPStatus.OK, {'X-Total-Count': str(total_count)}


@users_namespace.route('/users/search')
class SearchUsers(Resource):

    def get(self):
        """Search users by username prefix. Query params: q, limit, offset"""
        q = request.args.get('q', '').strip()
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)

        if q == '':
            return {'message': 'Query parameter q required'}, HTTPStatus.BAD_REQUEST

        base_query = User.query.filter(User.username.ilike(f"{q}%"))
        total_count = base_query.count()

        query = base_query.order_by(User.username.asc())

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        users = query.all()
        result = []
        for u in users:
            elo_entry = EloEntry.query.filter_by(user_id=u.id).order_by(EloEntry.created_at.desc()).first()
            result.append({'id': u.id, 'username': u.username, 'elo': elo_entry.elo if elo_entry else 'N/A'})

        return result, HTTPStatus.OK, {'X-Total-Count': str(total_count)}


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

        all_games_formatted = []
        for game in all_games:
            moves = [move.uci for move in Move.get_moves_by_game_id(game.id)]
            white_username = User.get_by_id(game.white_user_id).username
            black_username = User.get_by_id(game.black_user_id).username
            white_elo_entry = EloEntry.query.filter_by(user_id=game.white_user_id, game_id=game.id).first()
            black_elo_entry = EloEntry.query.filter_by(user_id=game.black_user_id, game_id=game.id).first()
            white_elo = white_elo_entry.elo if white_elo_entry else None
            black_elo = black_elo_entry.elo if black_elo_entry else None
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

        query = User.query.filter(User.username.ilike(f"{q}%")).order_by(User.username.asc())

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        users = query.all()
        result = []
        for u in users:
            elo_entry = EloEntry.query.filter_by(user_id=u.id).order_by(EloEntry.created_at.desc()).first()
            result.append({'id': u.id, 'username': u.username, 'elo': elo_entry.elo if elo_entry else 'N/A'})

        return result, HTTPStatus.OK



