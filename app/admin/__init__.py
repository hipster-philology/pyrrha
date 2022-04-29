from app.admin.views import admin  # noqa

# Monkeypatch QuerySelectField to work with sqla 1.2
# https://github.com/indico/indico/commit/c79c562866e5efdbeb5a3101cccc97df57906f76
# monkeypatch for https://github.com/wtforms/wtforms/issues/373
def _patch_wtforms_sqlalchemy():
    from wtforms_sqlalchemy import fields
    from sqlalchemy.orm.util import identity_key

    def get_pk_from_identity(obj):
        key = identity_key(instance=obj)[1]
        return u':'.join(map(str, key))

    fields.get_pk_from_identity = get_pk_from_identity

_patch_wtforms_sqlalchemy()
del _patch_wtforms_sqlalchemy