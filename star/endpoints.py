from quart import Quart, Blueprint
from star.transcribe.endpoints import define_transcribe


def define(app: Quart):
    api_blueprint = Blueprint('star_api', __name__, url_prefix='/api/v1')
    # html_blueprint = Blueprint('star', __name__, url_prefix='/')
    define_transcribe(api_blueprint)
