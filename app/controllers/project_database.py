import json
import os
from flask import current_app
from flask_restful import Resource, request
from app.schemas import ProjectDatabaseSchema
from app.models.project_database import ProjectDatabase
from app.helpers.database_service import MysqlDbService, PostgresqlDbService, generate_db_credentials
from app.models.project import Project
from flask_jwt_extended import jwt_required
from app.helpers.decorators import admin_required

# Used to return a database service

database_flavours = [
    {
        'name': 'mysql',
        'host': os.getenv('ADMIN_MYSQL_HOST'),
        'port': os.getenv('ADMIN_MYSQL_PORT'),
        'class': MysqlDbService()
    },
    {
        'name': 'postgres',
        'host': os.getenv('ADMIN_PSQL_HOST'),
        'port': os.getenv('ADMIN_PSQL_PORT'),
        'class': PostgresqlDbService()
    }
]


# def get_db_service(flavour_name=None):
#     pass


def get_db_flavour(flavour_name=None):
    if flavour_name == 'mysql':
        return database_flavours[0]
    elif flavour_name == 'postgres':
        return database_flavours[1]
    else:
        return False


class ProjectDatabaseView(Resource):

    @jwt_required
    def post(self, project_id):
        """
        """
        database_schema = ProjectDatabaseSchema()

        databases_data = request.get_json()

        credentials = generate_db_credentials()

        validated_database_data, errors = database_schema.load(databases_data)

        if errors:
            return dict(status="fail", message=errors), 400

        database_flavour_name = validated_database_data.get(
            'database_flavour_name', None)

        db_flavour = get_db_flavour(database_flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database flavour with name {database_flavour_name} is not mysql or postgres."
            ), 409

        database_name = validated_database_data.get('name', credentials.name)
        database_user = validated_database_data.get('user', credentials.user)
        database_password = validated_database_data.get(
            'password', credentials.password)

        new_database_info = dict(
            user=database_user,
            password=database_password,
            project_id=project_id,
            name=database_name,
            database_flavour_name=database_flavour_name,
            host=db_flavour['host'],
            port=db_flavour['port']
        )

        validated_database_data, errors = database_schema.load(
            new_database_info)

        if errors:
            return dict(status="fail", message=errors), 400

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        validated_database_data['project_id'] = project_id

        database_existant = ProjectDatabase.find_first(
            name=database_name)

        if database_existant:
            return dict(
                status="fail",
                message=f"Database {database_name} Already Exists."
            ), 400

        database_user_existant = ProjectDatabase.find_first(
            user=database_user)

        if database_user_existant:
            return dict(
                status="fail",
                message=f"Database user {database_user} Already Exists."
            ), 400

        # Create the database
        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        create_database = database_service.create_database(
            db_name=database_name,
            user=database_user,
            password=database_password
        )

        if not create_database:
            return dict(
                status="fail",
                message=f"Unable to create database"
            ), 500

        # Save database credentials
        database = ProjectDatabase(**validated_database_data)
        saved_database = database.save()

        if not saved_database:
            return dict(status='fail', message=f'Internal Server Error'), 500

        new_database_data, errors = database_schema.dumps(database)

        return dict(
            status='success',
            data=dict(database=json.loads(new_database_data))
        ), 201

    @jwt_required
    def get(self, project_id):
        """
        """
        database_schema = ProjectDatabaseSchema(many=True)

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        databases = ProjectDatabase.find_all(project_id=project_id)

        database_data, errors = database_schema.dumps(databases)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(databases=json.loads(database_data))), 200


class ProjectDatabaseDetailView(Resource):

    @jwt_required
    def delete(self, project_id, database_id):
        """
        """
        database_schema = ProjectDatabaseSchema()

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        database_existant = ProjectDatabase.get_by_id(database_id)

        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404

        database_flavour_name = database_existant.database_flavour_name

        db_flavour = get_db_flavour(database_flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database flavour with name {database_existant.database_flavour_name} is not mysql or postgres."
            ), 409

        # Delete the database
        database_service = db_flavour['name']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        delete_database = database_service.delete_database(
            database_existant.name)

        if not delete_database:
            return dict(
                status="fail",
                message=f"Unable to delete database"
            ), 500

        # Delete database record from database
        deleted_database = database_existant.delete()

        if not deleted_database:
            return dict(status='fail', message=f'Internal Server Error'), 500

        return dict(status='success', message="Database Successfully deleted"), 200

    @jwt_required
    def get(self, project_id, database_id):
        """
        """
        database_schema = ProjectDatabaseSchema()

        project = Project.get_by_id(project_id)

        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        database_existant = ProjectDatabase.get_by_id(database_id)

        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404

        database_data, errors = database_schema.dumps(database_existant)

        if errors:
            return dict(status='fail', message=errors), 500

        # Check the database status on host
        db_flavour = get_db_flavour(database_existant.database_flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database with flavour {database_existant.database_flavour_name} is not mysql or postgres."
            ), 409

        # Get db status
        database_service = db_flavour['name']
        try:
            database_connection = database_service.create_db_connection(
                user=database_existant.user, password=database_existant.password, db_name=database_existant.name)
            if not database_connection:
                db_status = False
            else:
                db_status = True
        except:
            db_status = False
        finally:
            if database_connection:
                if database_service == MysqlDbService():
                    if database_connection.is_connected():
                        database_connection.close()
                    else:
                        database_connection.close()

        database_data_list = json.loads(database_data)
        database_data_list['db_status'] = db_status

        return dict(status='success', data=dict(database=database_data_list)), 200


class ProjectDatabaseAdminView(Resource):
    @admin_required
    def post(self):
        """
        """
        database_schema = ProjectDatabaseSchema()

        databases_data = request.get_json()

        credentials = generate_db_credentials()

        validated_database_data, errors = database_schema.load(databases_data)

        if errors:
            return dict(status="fail", message=errors), 400

        database_flavour_name = validated_database_data.get(
            'database_flavour_name', None)

        db_flavour = get_db_flavour(database_flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database with flavour name {database_flavour_name} is not mysql or postgres."
            ), 409

        database_name = validated_database_data.get('name', credentials.name)
        database_user = validated_database_data.get('user', credentials.user)
        database_password = validated_database_data.get(
            'password', credentials.password)
        project_id = validated_database_data.get('project_id', None)

        new_database_info = dict(
            user=database_user,
            password=database_password,
            project_id=project_id,
            name=database_name,
            database_flavour_name=database_flavour_name,
            host=db_flavour['host'],
            port=db_flavour['port']
        )

        if project_id:
            project = Project.get_by_id(project_id)
            if not project:
                return dict(status='fail', message=f'Project with id {project_id} not found'), 404
        else:
            del new_database_info["project_id"]

        validated_database_data, errors = database_schema.load(
            new_database_info)

        if errors:
            return dict(status="fail", message=errors), 400

        database_existant = ProjectDatabase.find_first(
            name=database_name)

        if database_existant:
            return dict(
                status="fail",
                message=f"Database {database_name} Already Exists."
            ), 400

        database_user_existant = ProjectDatabase.find_first(
            user=database_user)

        if database_user_existant:
            return dict(
                status="fail",
                message=f"Database user {database_user} Already Exists."
            ), 400

        # Create the database
        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        create_database = database_service.create_database(
            db_name=database_name,
            user=database_user,
            password=database_password
        )

        if not create_database:
            return dict(
                status="fail",
                message=f"Unable to create database"
            ), 500

        # Save database credentials
        database = ProjectDatabase(**validated_database_data)
        saved_database = database.save()

        if not saved_database:
            return dict(status='fail', message=f'Internal Server Error'), 500

        new_database_data, errors = database_schema.dumps(database)

        return dict(
            status='success',
            data=dict(database=json.loads(new_database_data))
        ), 201

    @admin_required
    def get(self):
        """
        """
        database_schema = ProjectDatabaseSchema(many=True)

        databases = ProjectDatabase.find_all()

        database_data, errors = database_schema.dumps(databases)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(databases=json.loads(database_data))), 200


class ProjectDatabaseAdminDetailView(Resource):

    @admin_required
    def delete(self, database_id):
        """
        """
        database_schema = ProjectDatabaseSchema()

        database_existant = ProjectDatabase.get_by_id(database_id)

        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404

        db_flavour = get_db_flavour(database_existant.database_flavour_name)
        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database with flavour name {database_existant.database_flavour_name} is not mysql or postgres."
            ), 409

        # Delete the database
        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        delete_database = database_service.delete_database(
            database_existant.name)

        if not delete_database:
            return dict(
                status="fail",
                message=f"Unable to delete database"
            ), 500

        # Delete database record from database
        deleted_database = database_existant.delete()

        if not deleted_database:
            return dict(status='fail', message=f'Internal Server Error'), 500

        return dict(status='success', message="Database Successfully deleted"), 200

    @admin_required
    def get(self, database_id):
        """
        """
        database_schema = ProjectDatabaseSchema()

        database_existant = ProjectDatabase.get_by_id(database_id)

        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404

        database_data, errors = database_schema.dumps(database_existant)

        if errors:
            return dict(status='fail', message=errors), 500

        # Check the database status on host
        db_flavour = get_db_flavour(database_existant.database_flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database with flavour name {database_existant.database_flavour_name} is not mysql or postgres."
            ), 409

        # Get db status
        database_service = db_flavour['class']
        try:
            database_connection = database_service.create_db_connection(
                user=database_existant.user, password=database_existant.password, db_name=database_existant.name)
            if not database_connection:
                db_status = False
            else:
                db_status = True
        except:
            db_status = False
        finally:
            if database_connection:
                if database_service == MysqlDbService():
                    if database_connection.is_connected():
                        database_connection.close()
                else:
                    database_connection.close()

        database_data_list = json.loads(database_data)
        database_data_list['db_status'] = db_status

        return dict(status='success', data=dict(database=database_data_list)), 200


class ProjectDatabaseResetView(Resource):

    @jwt_required
    def post(self, project_id, database_id):
        """
        Reset Database
        """
        database_schema = ProjectDatabaseSchema()

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        database_existant = ProjectDatabase.get_by_id(database_id)

        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404

        # Reset the database
        db_flavour = get_db_flavour(database_existant.database_flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database with flavour name {database_existant.database_flavour_name} is not mysql or postgres."
            ), 409

        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        reset_database = database_service.reset_database(
            db_name=database_existant.name,
            user=database_existant.user,
            password=database_existant.password
        )

        if not reset_database:
            return dict(
                status="fail",
                message=f"Unable to reset database"
            ), 500

        return dict(status='success', message="Database Reset Successfully"), 200


class ProjectDatabaseAdminResetView(Resource):

    @admin_required
    def post(self, database_id):
        """
        Reset Database
        """
        database_schema = ProjectDatabaseSchema()

        database_existant = ProjectDatabase.get_by_id(database_id)

        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404

        # Reset the database
        db_flavour = get_db_flavour(database_existant.database_flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database with flavour name {database_existant.database_flavour_name} is not mysql or postgres."
            ), 409

        database_service = db_flavour['class']

        database_connection = database_service.check_db_connection()

        if not database_connection:
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        reset_database = database_service.reset_database(
            db_name=database_existant.name,
            user=database_existant.user,
            password=database_existant.password
        )

        if not reset_database:
            return dict(
                status="fail",
                message=f"Unable to reset database"
            ), 500

        return dict(status='success', message="Database Reset Successfully"), 200
