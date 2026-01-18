import logging
import os
from pathlib import Path

from flask import Flask

from atp.web.routes import routes


def _configure_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('translation.log', encoding='utf-8'),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)


def create_app() -> Flask:
    _configure_logging()
    base_dir = Path(__file__).resolve().parents[2]
    template_folder = Path(__file__).resolve().parent / 'templates'

    app = Flask(__name__, template_folder=str(template_folder))
    app.config['UPLOAD_FOLDER'] = base_dir / 'uploads'
    app.config['OUTPUT_FOLDER'] = base_dir / 'outputs'
    app.config['ALLOWED_EXTENSIONS'] = {'txt', 'doc', 'docx'}
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
    app.config['JSON_AS_ASCII'] = False

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

    app.register_blueprint(routes)
    return app


app = create_app()
