from flask import Flask, request, Response, stream_with_context
app = Flask("fixture")


@app.route("/lemma", methods=["POST"])
def lemmatizing():
    r = Response(
        "\n".join(
            ["token\tlemma"] +
            ["\t".join([tok, f"{idx}"]) for idx, tok in enumerate(request.form.get("data").split())]
        ),
        200,
        headers={
            'Content-Type': 'text/plain; charset=utf-8',
            'Access-Control-Allow-Origin': "*"
        }
    )
    return r

app.run(port="4567")
