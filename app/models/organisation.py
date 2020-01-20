import jwt
from datetime import datetime, timedelta
from app.models.user import User

from app.models import db

from app.models.model_mixin import ModelMixin


class Organisation(ModelMixin):
    """ Organisation table definition """

    _tablename_ = 'organisations'
    __table_args__ = (db.UniqueConstraint('name', name='organisation_unique_name'),)

    # fields of the Organisation table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, name):
        """ initialize with name, member and namespace """
        self.name = name