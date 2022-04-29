# Base Python
import datetime
import csv
import enum
import os.path
import io
import glob
from collections import Counter
# PIP Packages
import unidecode
import yaml
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref
from sqlalchemy import literal, case
from werkzeug.exceptions import BadRequest
# APP Logic
from .. import db
from ..utils import PyrrhaError
from ..utils.forms import prepare_search_string, column_search_filter, read_input_POS, read_input_morph, \
    read_input_lemma
# Models
from .user import User
# Session
from flask_login import current_user


class PublicationStatus(enum.Enum):
    public = 1
    submitted = 0
    private = -1


_PublicationStatusOrder = dict(public = -1, submitted = -1, private = 1)


class ControlLists(db.Model):
    __tablename__ = "control_lists"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), default="Control List")
    public = db.Column(db.Enum(PublicationStatus), default=PublicationStatus.private)
    parent_id = db.Column(db.Integer, db.ForeignKey("control_lists.id"), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    bibliography = db.Column(db.Text, nullable=True)
    language = db.Column(db.String(10), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # For caching purposes, we record the last time these fields were edited
    #last_lemma_edit = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    #last_morph_edit = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    #last_POS_edit = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    users = association_proxy('control_lists_user', 'user')

    sort_logic = case(value=public, whens=_PublicationStatusOrder).label("priority")

    @property
    def str_public(self):
        return self.public.name

    @property
    def owners(self):
        return db.session.query(User.first_name, User.last_name, User.id, User.email).filter(
            ControlListsUser.user_id == User.id,
            ControlListsUser.control_lists_id == self.id,
            ControlListsUser.is_owner == True
        ).all()

    @staticmethod
    def link(control_list_id: int, user_id: int, is_owner=False):
        if db.session.query(ControlListsUser.user_id).filter(
            db.and_(
                ControlListsUser.user_id == user_id,
                ControlListsUser.control_lists_id == control_list_id
            )
        ).count() == 0:
            db.session.add(ControlListsUser(
                user_id=user_id,
                control_lists_id=control_list_id,
                is_owner=is_owner
            ))

    @staticmethod
    def get_linked_or_404(control_list_id: int, user: User):
        if not user:
            raise BadRequest(description="You have no right to access the Control List")
        if user.is_admin():
            cl = ControlLists.query.get_or_404(control_list_id)
            return cl, cl.is_owned_by(user)
        data = db.session.query(ControlLists, ControlListsUser.is_owner).filter(
            db.and_(
                ControlLists.id == control_list_id,
                ControlListsUser.control_lists_id == ControlLists.id,
                ControlListsUser.user_id == user.id
            )
        ).first()
        if data is None:
            raise BadRequest(description="You have no right to access the Control List")

        control_list, is_owner = data
        if control_list is None:
            raise BadRequest(description="You have no right to access the Control List")
        return control_list, is_owner

    @staticmethod
    def for_user(user):
        return db.session.query(ControlLists).filter(
            db.and_(
                ControlListsUser.user_id == user.id,
                ControlListsUser.control_lists_id == ControlLists.id
            )
        ).all()

    def can_edit(self):
        return self.is_owned_by(current_user)

    @staticmethod
    def get_available(user):
        """ Get available ControlLists a corpus creation for a given user.
        This includes public and privately accessible lists.

        Note : Admin status does not change this.

        :param user: User to check for
        :return: List of available control lists
        """

        return db.session.query(ControlLists).outerjoin(
            ControlListsUser,
            ControlListsUser.control_lists_id == ControlLists.id
        ).filter(
            db.or_(
                ControlLists.public == PublicationStatus.public,
                ControlListsUser.user_id == user.id
            )
        ).order_by(ControlLists.sort_logic, ControlLists.name).all()

    def get_allowed_values(self, allowed_type="lemma", order_by="label", kw=None):
        """ List values that are allowed (without label) or checks that given label is part
        of the existing corpus

        :param allowed_type: A value from the set "lemma", "POS", "morph"
        :param order_by: Column to use for ordering
        :param kw: Search keyword
        :return: Flask SQL Alchemy Query
        :rtype: BaseQuery
        """
        filters = []
        if allowed_type == "lemma":
            cls = AllowedLemma
            order_by = getattr(cls, order_by)
        elif allowed_type == "POS":
            cls = AllowedPOS
            order_by = getattr(cls, order_by)
        elif allowed_type == "morph":
            cls = AllowedMorph
            order_by = getattr(cls, order_by)
        else:
            raise ValueError("Get Allowed value had %s and it's not from the lemma, POS, morph set" % allowed_type)

        filters = cls.control_list == self.id
        if kw:
            filters = db.and_(
                filters,
                db.or_(
                    *(
                        db.and_(*tuple(column_search_filter(AllowedLemma.label_uniform, unidecode.unidecode(search_string))))
                        for search_string in prepare_search_string(kw)
                    )
                )
            )
        return db.session.query(cls).filter(filters).order_by(order_by)

    def has_access(self, user):
        """
        Can this corpus be accessed by the given user ?
        :param user:
        :return: True or False
        """
        # Todo:
        #if self.public:
        #   return True
        if not user.is_admin():
            return db.session.query(literal(True)).filter(
                ControlListsUser.query.filter(
                    ControlListsUser.user_id == user.id,
                    ControlListsUser.control_lists_id == self.id
                ).exists()
            ).scalar()
        return True

    def is_owned_by(self, user):
        return db.session.query(literal(True)).filter(
            ControlListsUser.query.filter(
                ControlListsUser.user_id == user.id,
                ControlListsUser.control_lists_id == self.id,
                ControlListsUser.is_owner == True
            ).exists()
        ).scalar()

    def update_allowed_values(self, allowed_type, allowed_values):
        """ Update allowed values of the current corpus

        :param allowed_type: Allowed Value Type (lemma, morph, POS)
        :param allowed_values: New values
        :return: Bool of success
        """
        if allowed_type == "lemma":
            cls = AllowedLemma
        elif allowed_type == "POS":
            cls = AllowedPOS
        elif allowed_type == "morph":
            cls = AllowedMorph
        else:
            raise BadRequest("The type is not of lemma, morph or POS")

        try:
            data = db.session.query(cls).filter_by(control_list=self.id).delete()
            cls.add_batch(allowed_values, self.id, _commit=True)
        except Exception as E:
            print(E)
            db.session.rollback()
            raise

    def has_list(self, allowed_type):
        """ Check if the Control List has the specific allowed_type

        :param allowed_type: A string in the lemma, morph, POS list that targets linked models
        :return: Whether the control list has a set of values for this allowed type
        """
        if allowed_type == "POS":
            cls = AllowedPOS
        elif allowed_type == "lemma":
            cls = AllowedLemma
        else:
            cls = AllowedMorph

        return db.session.query(literal(True)).filter(
            cls.query.filter(
                cls.control_list == self.id
            ).exists()
        ).scalar()

    @staticmethod
    def add_default_lists(path=None):
        """ Loads the default lists from the config folder

        """
        if not path:
            current = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(current, "..", "configurations", "langs", "**")

        for directory in glob.glob(path):
            with open(os.path.join(directory, "metadata.yaml")) as f:
                data = yaml.safe_load(f)
            print("[ControlLists] Adding %s " % data["name"])
            cl = ControlLists(**data, public=PublicationStatus.public)
            db.session.add(cl)
            db.session.flush()  # Get the AutoIncrement ID
            configs = [
                ("lemma.txt", AllowedLemma, read_input_lemma),
                ("POS.txt", AllowedPOS, read_input_POS),
                ("morph.txt", AllowedMorph, read_input_morph)
            ]
            for file, model, parser in configs:
                filepath = os.path.join(directory, file)
                if os.path.exists(filepath):
                    with open(filepath, encoding='utf-8') as f:
                        model.add_batch(parser(f.read()), control_lists_id=cl.id)

                    print("[ControlLists] [%s] Loading %s " % (data["name"], os.path.basename(filepath)))
            db.session.commit()


class ControlListsUser(db.Model):
    """ Association proxy that link users to ControlLists

    :param control: a control list object
    :param user: a User
    """
    control_lists_id = db.Column(db.Integer, db.ForeignKey("control_lists.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), primary_key=True)
    is_owner = db.Column(db.Boolean, default=False)

    control = db.relationship("ControlLists", backref=backref("control_lists_user", cascade="all, delete-orphan"))
    user = db.relationship(User, backref=backref("control_lists_user", cascade="all, delete-orphan"))


class AllowedLemma(db.Model):
    """ An allowed lemma is a lemma that is accepted

    :param id: ID of the Allowed Lemma (Optional)
    :param label: Allowed Lemma Value
    :param label_uniform: Normalized value of label, which allows for plaintext search
    :param corpus: ID of the corpus this AllowedLemma is related to
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(64), nullable=False)
    label_uniform = db.Column(db.String(64))
    control_list = db.Column(db.Integer, db.ForeignKey('control_lists.id'))

    __table_args__ = (
        db.Index('unique_label_per_control', 'label', 'control_list', unique=True),
    )

    @staticmethod
    def add_batch(allowed_values, control_lists_id, _commit=False):
        """ Add a batch of allowed values

        :param allowed_values: List of dictionary with label and readable keys
        :param control_lists_id: Id of the Control List
        :param _commit: Force commit (Default: false)
        """
        if len(allowed_values) != len(set(allowed_values)):
            raise PyrrhaError("Following values are duplicated: " + ", ".join(
                [
                    lemma
                    for lemma, cnt in Counter(allowed_values).items()
                    if cnt > 1
                ]
            ))
        db.session.bulk_insert_mappings(
            AllowedLemma,
            [
                dict(label=item, control_list=control_lists_id, label_uniform=unidecode.unidecode(item))
                for item in allowed_values
            ]
        )
        if _commit:
            db.session.commit()

    @staticmethod
    def to_input_format(query):
        """ Transforms query results into the input format

        .. note:: OrderBy is done inside the function

        :param query: Query on AllowedLemma
        :type query: AllowedLemma.query
        :return: String representation of the data
        """
        return "\n".join(
            [
                allowed.label
                for allowed in query.order_by(AllowedLemma.id).all()
            ]
        )


class AllowedPOS(db.Model):
    """ An allowed POS is a POS that is accepted

    :param id: ID of the Allowed POS (Optional)
    :param label: Allowed POS Value
    :param corpus: ID of the corpus this AllowedPOS is related to
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(64))
    control_list = db.Column(db.Integer, db.ForeignKey('control_lists.id'))

    @staticmethod
    def add_batch(allowed_values, control_lists_id: int, _commit: bool=False):
        """ Add a batch of allowed values

        :param allowed_values: List of dictionary with label and readable keys
        :param control_lists_id: Id of the ControlLists
        :param _commit: Force commit (Default: false)
        """
        db.session.bulk_insert_mappings(
            AllowedPOS,
            [
                dict(label=item, control_list=control_lists_id)
                for item in allowed_values
            ]
        )
        if _commit:
            db.session.commit()

    @staticmethod
    def to_input_format(query):
        """ Transforms query results into the input format

        .. note:: OrderBy is done inside the function

        :param query: Query on AllowedPOS
        :type query: AllowedPOS.query
        :return: String representation of the data
        """
        return ",".join(
            [
                allowed.label
                for allowed in query.order_by(AllowedPOS.id).all()
            ]
        )


class AllowedMorph(db.Model):
    """ An allowed Morph is a Morph that is accepted

    :param id: ID of the Allowed Morph (Optional)
    :param label: Allowed Morph Value
    :param readable: Human Readable value of the label. *iei* v--1s-pi becomes Verb, 1st Singular Present Indicative
    :param control_list: ID of the ControlLists this AllowedMorph is related to
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(64))
    readable = db.Column(db.String(256))
    control_list = db.Column(db.Integer, db.ForeignKey('control_lists.id'))

    @staticmethod
    def add_batch(allowed_values, control_lists_id, _commit=False):
        """ Add a batch of allowed values

        :param allowed_values: List of dictionary with label and readable keys
        :param control_lists_id: Id of the control list
        :param _commit: Force commit (Default: false)
        """
        db.session.bulk_insert_mappings(
            AllowedMorph,
            [
                dict(
                    label=item.get("label"),
                    readable=item.get("readable", item["label"]),
                    control_list=control_lists_id
                )
                for item in allowed_values
            ]
        )
        if _commit:
            db.session.commit()

    @staticmethod
    def to_input_format(query):
        """ Transforms query results into the input format

        .. note:: OrderBy is done inside the function

        :param query: Query on AllowedMorph
        :type query: AllowedMorph.query
        :return: String representation of the data
        """
        csv_file = io.StringIO()
        writer = csv.writer(csv_file, dialect="excel-tab")
        writer.writerow(["label", "readable"])
        for morph in query.order_by(AllowedMorph.id).all():
            writer.writerow([morph.label, morph.readable])

        return csv_file.getvalue()
