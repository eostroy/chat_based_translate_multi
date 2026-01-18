import logging
import time
import traceback

from flask import Blueprint, current_app, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from atp.services.review_service import (
    perform_dual_review,
    perform_meeting_review,
    perform_single_review,
    perform_two_stage_review,
)
from atp.services.translation_service import process_translation
from atp.translators import create_translator

logger = logging.getLogger(__name__)

routes = Blueprint('routes', __name__)


def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@routes.route('/')
def index():
    return render_template('index.html')


@routes.route('/upload', methods=['POST'])
async def upload_file():
    try:
        if 'file' not in request.files:
            logger.warning("没有文件被上传")
            return jsonify({'error': '没有文件被上传'}), 400

        file = request.files['file']

        if file.filename == '':
            logger.warning("没有选择文件")
            return jsonify({'error': '没有选择文件'}), 400

        if not _allowed_file(file.filename):
            logger.warning("不支持的文件类型: %s", file.filename)
            return jsonify({'error': '不支持的文件类型'}), 400

        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        filename_with_timestamp = f"{timestamp}_{filename}"
        file_path = current_app.config['UPLOAD_FOLDER'] / filename_with_timestamp
        file.save(file_path)

        logger.info("文件已保存: %s", file_path)

        api_type = request.form.get('api_type', 'openrouter')
        api_key = request.form.get('api_key', '')
        if not api_key:
            logger.warning("API密钥不能为空")
            return jsonify({'error': 'API密钥不能为空'}), 400

        model = request.form.get('model', '')
        if not model:
            logger.warning("未选择模型")
            return jsonify({'error': '请选择要使用的模型'}), 400

        temperature = float(request.form.get('temperature', 1.0))

        source_lang = request.form.get('source_lang', '英文')
        target_lang = request.form.get('target_lang', '中文')

        system_prompt = request.form.get('system_prompt', '')
        user_prompt = request.form.get('user_prompt', '')

        logger.info(
            "开始处理文件: %s, API类型: %s, 模型: %s, 温度: %s",
            filename,
            api_type,
            model,
            temperature,
        )
        logger.info("源语言: %s, 目标语言: %s", source_lang, target_lang)

        result = await process_translation(
            str(file_path),
            api_type,
            api_key,
            model,
            source_lang,
            target_lang,
            system_prompt,
            user_prompt,
            temperature,
            output_folder=str(current_app.config['OUTPUT_FOLDER']),
        )

        if 'error' in result:
            return jsonify(result), 500
        return jsonify(result)

    except Exception as e:
        logger.error("上传文件时出错: %s", str(e))
        logger.error(traceback.format_exc())
        return jsonify({'error': f'上传失败: {str(e)}'}), 500


@routes.route('/download/<filename>')
def download_file(filename):
    return send_file(current_app.config['OUTPUT_FOLDER'] / filename, as_attachment=True)


@routes.route('/translate', methods=['POST'])
async def interactive_translate():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': '未提供数据'}), 400

        user_message = data.get('user_message', '')
        if not user_message:
            return jsonify({'error': '翻译内容不能为空'}), 400

        api_type = data.get('api_type', 'openrouter')
        api_key = data.get('api_key', '')
        if not api_key:
            return jsonify({'error': 'API密钥不能为空'}), 400

        model = data.get('model', '')
        if not model:
            return jsonify({'error': '请选择要使用的模型'}), 400

        temperature = float(data.get('temperature', 1.0))
        source_lang = data.get('source_lang', '英文')
        target_lang = data.get('target_lang', '中文')
        system_prompt = data.get('system_prompt', '')

        logger.info(
            "交互翻译请求: API类型: %s, 模型: %s, 温度: %s",
            api_type,
            model,
            temperature,
        )
        logger.info("源语言: %s, 目标语言: %s", source_lang, target_lang)

        translator = create_translator(api_type, api_key)

        translated_text = translator.translate(
            user_message,
            source_lang=source_lang,
            target_lang=target_lang,
            model=model,
            system_prompt=system_prompt if system_prompt else None,
            user_prompt=None,
            temperature=temperature,
        )

        if translated_text:
            return jsonify({'success': True, 'translation': translated_text})
        return jsonify({'error': '翻译失败'}), 500

    except Exception as e:
        logger.error("交互翻译时出错: %s", str(e))
        logger.error(traceback.format_exc())
        return jsonify({'error': f'翻译失败: {str(e)}'}), 500


@routes.route('/review', methods=['POST'])
async def ai_review():
    """AI译审接口，支持单模型、双模型对比、双阶段协同、模型开会"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': '未提供数据'}), 400

        mode = data.get('mode', 'single')
        source_text = data.get('source_text', '')
        target_text = data.get('target_text', '')
        source_lang = data.get('source_lang', '英文')
        target_lang = data.get('target_lang', '中文')

        if not source_text or not target_text:
            return jsonify({'error': '原文和译文不能为空'}), 400

        logger.info("AI译审请求: 模式: %s, 源语言: %s, 目标语言: %s", mode, source_lang, target_lang)

        if mode == 'single':
            payload, status = await perform_single_review(data, source_text, target_text, source_lang, target_lang)
            return jsonify(payload), status
        if mode == 'dual':
            payload, status = await perform_dual_review(data, source_text, target_text, source_lang, target_lang)
            return jsonify(payload), status
        if mode == 'two-stage':
            payload, status = await perform_two_stage_review(data, source_text, target_text, source_lang, target_lang)
            return jsonify(payload), status
        if mode == 'meeting':
            payload, status = await perform_meeting_review(data, source_text, target_text, source_lang, target_lang)
            return jsonify(payload), status

        return jsonify({'error': f'不支持的模式: {mode}'}), 400

    except Exception as e:
        logger.error("AI译审时出错: %s", str(e))
        logger.error(traceback.format_exc())
        return jsonify({'error': f'译审失败: {str(e)}'}), 500
