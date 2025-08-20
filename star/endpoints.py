from pathlib import Path
from quart import Quart, Blueprint, send_from_directory, render_template_string
from star.web_utils import html_endpoint, ServerEvent
from star.transcribe.endpoints import define_transcribe
from star.response import Ok


def define(app: Quart):
    api_blueprint = Blueprint('star_api', __name__, url_prefix='/api/v1')
    sse_blueprint = Blueprint('star_sse', __name__, url_prefix='/sse')

    define_transcribe(api_blueprint, sse_blueprint, app)

    @api_blueprint.get('/healthcheck')
    async def healthcheck():
        return Ok()

    @app.get('/static/css/style.css')
    async def static_css():
        return await send_from_directory('static/css', 'style.css')

    @app.get('/static/webp/<resource>')
    async def static_webp(resource: str):
        path = Path('static/') / resource
        return await send_from_directory('static/webp', path.name)

    @app.get('/')
    @html_endpoint(template_path='home.html', title='Fungal Nebula')
    async def index(html: str):
        return await render_template_string(
            html,
        )

    app.register_blueprint(api_blueprint)
    app.register_blueprint(sse_blueprint)
