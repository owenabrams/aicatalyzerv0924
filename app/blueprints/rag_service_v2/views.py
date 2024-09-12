from flask import render_template, Blueprint

rag_blueprint_v2 = Blueprint('rag_v2', __name__)

@rag_blueprint_v2.route('/rag_v2')
def rag_v2_landing():
    return render_template('rag_v2.html')
