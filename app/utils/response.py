from flask import current_app


def format_api_like_reply(result, mode="lemma"):
    """ Format autocomplete result for frontend

    :param result: A tuple of result out of the SQL Query
    :return: A jsonify-compliant value that will show on the front end
    """
    result = list(result)
    if mode == "morph" and len(result) == 1:
        return {"value": result[0], "label": result[0]}
    elif len(result) == 1:
        return result[0]
    elif len(result) == 2:
        return {"value": result[0], "label": result[1]}


def stream_template(template_name, **context):
    """ Stream a template

    Needs to be used with Response(stream_template(...))
    """
    current_app.update_template_context(context)
    t = current_app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    rv.disable_buffering()
    return rv
