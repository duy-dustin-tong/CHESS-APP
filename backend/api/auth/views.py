# backend/api/auth/views.py
from flask_restx import Resource, Namespace, fields
from http import HTTPStatus
from ..models.users import User
from ..models.elo import EloEntry
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import Conflict, BadRequest
from flask import request
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

auth_namespace = Namespace('auth', description = "auth namespace")

signup_model = auth_namespace.model('SignUp', {
    'username': fields.String(required=True, description='Username'),
    'email': fields.String(required=True, description='Email'),
    'password': fields.String(required=True, description='Password')
})

login_model = auth_namespace.model('Login', {
    'email': fields.String(required=True, description='Email'),
    'password': fields.String(required=True, description='Password')
})

user_model = auth_namespace.model('User', {
    'id': fields.Integer(description='User ID'),        
    'username': fields.String(description='Username'),
    'email': fields.String(description='Email'),
    'elo': fields.Integer(description='ELO Rating'),
    'created_at': fields.DateTime(description='Account Creation Time')
})

@auth_namespace.route('/signup')
class SignUp(Resource):

    @auth_namespace.expect(signup_model)
    @auth_namespace.marshal_with(user_model)    
    def post(self):
        """user sign up"""
        data = request.get_json()

        # validate JSON payload
        if not isinstance(data, dict):
            raise BadRequest('Invalid JSON payload.')

        required_fields = ['username', 'email', 'password']
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            raise BadRequest(f"Missing or empty fields: {', '.join(missing)}")

        try:
            new_user = User(
                username=data['username'],
                email=data['email'],
                password_hash=generate_password_hash(data['password'])
            )
            new_user.save()

            new_elo_entry = EloEntry(
                user_id=new_user.id
            )
            new_elo_entry.save()
            return new_user, HTTPStatus.CREATED
        except IntegrityError as ie:
            logger.exception('IntegrityError during signup')
            raise Conflict('User with provided email or username already exists.')
        except Exception as e:
            logger.exception('Unexpected error during signup')
            return {'message': 'Internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR

@auth_namespace.route('/login')
class LogIn(Resource):
    @auth_namespace.expect(login_model)
    def post(self):
        """user log in"""
        data = request.get_json()

        # validate JSON payload
        if not isinstance(data, dict):
            raise BadRequest('Invalid JSON payload.')

        required_fields = ['email', 'password']
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            raise BadRequest(f"Missing or empty fields: {', '.join(missing)}")

        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()

        if user is not None and check_password_hash(user.password_hash, password):
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))

            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'username': user.username,
                'user_id': user.id
            }, HTTPStatus.OK
        
        raise BadRequest("Invalid email or password.")
    
@auth_namespace.route('/refresh')
class Refresh(Resource):

    @jwt_required(refresh=True)
    def post(self):
        """ refreshes token"""
        user_id=get_jwt_identity()

        access_token = create_access_token(identity=user_id)
        
        user = User.query.filter_by(id=int(user_id)).first()
        if not user:
            raise BadRequest('User not found.')
        
        return {
            "username": user.username,
            "access_token": access_token,
        }, HTTPStatus.OK
        

