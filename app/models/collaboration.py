from .. import db
from .linguistic import AllowedLemma, AllowedMorph, AllowedPOS
from .user import User


class ControlListModification(db.model):
    """ Database model for adding information to modifications request

    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    control_list_id = db.Column(db.Integer, db.ForeignKey('control_lists.id'))
    title = db.Column(db.String(128), nullable=False)
    message = db.Column(db.Text, nullable=True)

    allowed_lemma = db.Column(db.Integer, db.ForeignKey("allowed_lemma.id"), nullable=True)
    allowed_POS = db.Column(db.Integer, db.ForeignKey("allowed_POS.id"), nullable=True)
    allowed_morph = db.Column(db.Integer, db.ForeignKey("allowed_morph.id"), nullable=True)
    # The other way around might me better ?