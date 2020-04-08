from marshmallow import Schema, fields, validate


class AppSchema(Schema):

    id = fields.String(dump_only=True)

    name = fields.String(required=True, error_messgae={
        "required": "name is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='name should be a valid string'
            ),
        ])
    image = fields.String(required=True, error_message={
        "required": "image is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='image should be a valid string'
            ),
        ])
    project_id = fields.String(required=True, error_message={
        "required": "project_id is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='project_id should be a valid string'
            ),
        ])
    url = fields.Url(dump_only=True)
    env_vars = fields.Dict()
    port = fields.Int()
