

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
