from flask_restx import Resource, Namespace, fields
from http import HTTPStatus

users_namespace = Namespace('users', description = "namespace for users")


@users_namespace.route('/users/<int: user_id>')
class UserInfoAndStatus(Resource):

    def get(self):
        """ get user info and status """
        pass

    def put(self):
        """ update user info and status """
        pass

    def delete(self):
        """delete user with user_id"""

@users_namespace.route('/users/<int: user_id>/friends')
class GetFriendsOfUser(Resource):
    
    def get(self):
        """ get ids of friends of user with user_id"""
        pass

@users_namespace.route('/users/<int: user_id>/history')
class GetGameHistoryOfUser(Resource):

    def get(self):
        """get completed game history of user with user_id"""
        pass
    


