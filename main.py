import os
import logging
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
import time
import traceback
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

from text_processor import TextProcessor
from translators import create_translator

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'doc', 'docx'}
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 限制上传文件大小为50MB
app.config['JSON_AS_ASCII'] = False  # 允许JSON响应包含非ASCII字符
# app.json.ensure_ascii = False

# 创建必要的文件夹
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def detect_language(text: str) -> str:
    if not text:
        return "英文"

    counts = {
        "日文": 0,
        "韩文": 0,
        "中文": 0,
        "俄文": 0,
    }

    for char in text:
        code_point = ord(char)
        if 0x3040 <= code_point <= 0x30FF or 0x31F0 <= code_point <= 0x31FF:
            counts["日文"] += 1
        elif 0xAC00 <= code_point <= 0xD7AF:
            counts["韩文"] += 1
        elif 0x4E00 <= code_point <= 0x9FFF:
            counts["中文"] += 1
        elif 0x0400 <= code_point <= 0x04FF:
            counts["俄文"] += 1

    if counts["日文"] > 0:
        return "日文"
    if counts["韩文"] > 0:
        return "韩文"
    if counts["中文"] > 0:
        return "中文"
    if counts["俄文"] > 0:
        return "俄文"
    return "英文"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

async def process_translation(file_path: str, api_type: str, api_key: str, model: str,
                            source_lang: str, target_lang: str,
                            system_prompt: str, user_prompt: str,
                            temperature: float) -> dict:
    try:
        # 处理文本
        processor = TextProcessor(max_tokens=2000)
        translator = create_translator(api_type, api_key)
        
        # 提取文本
        logger.info("开始提取文本内容")
        text = processor.extract_from_file(file_path)
        
        if not text or len(text.strip()) == 0:
            logger.error("提取的文本内容为空")
            return {'error': '提取的文本内容为空，请检查文件是否有效'}

        if source_lang == "auto":
            detected_lang = detect_language(text)
            logger.info(f"自动匹配源语言: {detected_lang}")
            source_lang = detected_lang
            
        logger.info(f"文本提取完成，长度：{len(text)} 字符")
        
        # 处理文本
        logger.info("开始处理文本")
        chunks = processor.process_text(text)
        
        logger.info(f"文本处理完成，共分为 {len(chunks)} 个文本块")
        
        # 记录每个文本块的大小
        for i, (prev_text, current_text) in enumerate(chunks):
            logger.info(f"块 {i+1}: {len(current_text)} 字符")
            
        # 翻译文本
        logger.info(f"开始翻译，共 {len(chunks)} 个块")
        translated_chunks = []
        
        for i, (prev_text, current_text) in enumerate(chunks):
            logger.info(f"正在翻译第 {i+1}/{len(chunks)} 块...")
            translated_chunk = translator.translate(
                current_text, 
                source_lang=source_lang, 
                target_lang=target_lang,
                model=model,
                system_prompt=system_prompt if system_prompt else None,
                user_prompt=user_prompt if user_prompt else None,
                temperature=temperature
            )
            
            if translated_chunk:
                translated_chunks.append(translated_chunk)
                logger.info(f"块 {i+1} 翻译完成")
            else:
                logger.warning(f"块 {i+1} 翻译失败，将重试...")
                # 重试一次
                await asyncio.sleep(2)
                translated_chunk = translator.translate(
                    current_text, 
                    source_lang=source_lang, 
                    target_lang=target_lang,
                    model=model,
                    system_prompt=system_prompt if system_prompt else None,
                    user_prompt=user_prompt if user_prompt else None,
                    temperature=temperature
                )
                
                if translated_chunk:
                    translated_chunks.append(translated_chunk)
                    logger.info(f"块 {i+1} 重试翻译成功")
                else:
                    logger.error(f"块 {i+1} 翻译失败")
                    translated_chunks.append(f"[翻译失败] {current_text[:100]}...")
            
            # 防止API速率限制
            if i < len(chunks) - 1:
                await asyncio.sleep(2)
        
        # 合并翻译结果
        translated_text = '\n\n'.join(translated_chunks)
        
        # 生成输出文件名
        timestamp = int(time.time())
        output_filename = f"translated_{timestamp}_{os.path.basename(file_path)}.txt"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # 保存翻译结果
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        
        logger.info(f"翻译完成，结果已保存至 {output_path}")
        
        return {
            'success': True,
            'message': '翻译完成',
            'output_file': output_filename
        }
        
    except Exception as e:
        logger.error(f"处理文件时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return {'error': f'处理失败: {str(e)}'}

@app.route('/upload', methods=['POST'])
async def upload_file():
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            logger.warning("没有文件被上传")
            return jsonify({'error': '没有文件被上传'}), 400
        
        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            logger.warning("没有选择文件")
            return jsonify({'error': '没有选择文件'}), 400
        
        # 检查文件类型
        if not allowed_file(file.filename):
            logger.warning(f"不支持的文件类型: {file.filename}")
            return jsonify({'error': '不支持的文件类型'}), 400
        
        # 安全地保存文件
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        filename_with_timestamp = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename_with_timestamp)
        file.save(file_path)
        
        logger.info(f"文件已保存: {file_path}")
        
        # 获取API类型和密钥
        api_type = request.form.get('api_type', 'openrouter')
        api_key = request.form.get('api_key', '')
        if not api_key:
            logger.warning("API密钥不能为空")
            return jsonify({'error': 'API密钥不能为空'}), 400
            
        # 获取模型
        model = request.form.get('model', '')
        if not model:
            logger.warning("未选择模型")
            return jsonify({'error': '请选择要使用的模型'}), 400
        
        # 获取温度参数
        temperature = float(request.form.get('temperature', 1.0))
        
        # 获取翻译方向
        source_lang = request.form.get('source_lang', '英文')
        target_lang = request.form.get('target_lang', '中文')
        
        # 获取自定义提示词
        system_prompt = request.form.get('system_prompt', '')
        user_prompt = request.form.get('user_prompt', '')
        
        logger.info(f"开始处理文件: {filename}, API类型: {api_type}, 模型: {model}, 温度: {temperature}")
        logger.info(f"源语言: {source_lang}, 目标语言: {target_lang}")
        
        # 处理翻译
        result = await process_translation(
            file_path, api_type, api_key, model,
            source_lang, target_lang,
            system_prompt, user_prompt,
            temperature
        )
        
        if 'error' in result:
            return jsonify(result), 500
        return jsonify(result)
            
    except Exception as e:
        logger.error(f"上传文件时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename),
                     as_attachment=True)

@app.route('/translate', methods=['POST'])
async def interactive_translate():
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证必要的参数
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
            
        # 获取其他参数
        temperature = float(data.get('temperature', 1.0))
        source_lang = data.get('source_lang', '英文')
        target_lang = data.get('target_lang', '中文')
        system_prompt = data.get('system_prompt', '')

        if source_lang == "auto":
            source_lang = detect_language(user_message)
            logger.info(f"自动匹配源语言: {source_lang}")
        
        logger.info(f"交互翻译请求: API类型: {api_type}, 模型: {model}, 温度: {temperature}")
        logger.info(f"源语言: {source_lang}, 目标语言: {target_lang}")
        
        # 创建翻译器
        translator = create_translator(api_type, api_key)
        
        # 执行翻译
        translated_text = translator.translate(
            user_message, 
            source_lang=source_lang, 
            target_lang=target_lang,
            model=model,
            system_prompt=system_prompt if system_prompt else None,
            user_prompt=None,  # 在交互模式中，用户消息直接作为内容
            temperature=temperature
        )
        
        if translated_text:
            return jsonify({
                'success': True,
                'translation': translated_text
            })
        else:
            return jsonify({'error': '翻译失败'}), 500
            
    except Exception as e:
        logger.error(f"交互翻译时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'翻译失败: {str(e)}'}), 500

@app.route('/review', methods=['POST'])
async def ai_review():
    """AI译审接口，支持单模型、双模型对比、双阶段协同、模型议会"""
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

        if source_lang == "auto":
            source_lang = detect_language(source_text)
            logger.info(f"自动匹配源语言: {source_lang}")

        if target_lang == "auto":
            target_lang = detect_language(target_text)
            logger.info(f"自动匹配目标语言: {target_lang}")

        logger.info(f"AI译审请求: 模式: {mode}, 源语言: {source_lang}, 目标语言: {target_lang}")

        if mode == 'single':
            return await perform_single_review(data, source_text, target_text, source_lang, target_lang)
        elif mode == 'dual':
            return await perform_dual_review(data, source_text, target_text, source_lang, target_lang)
        elif mode == 'two-stage':
            return await perform_two_stage_review(data, source_text, target_text, source_lang, target_lang)
        elif mode == 'meeting':
            return await perform_meeting_review(data, source_text, target_text, source_lang, target_lang)
        else:
            return jsonify({'error': f'不支持的模式: {mode}'}), 400

    except Exception as e:
        logger.error(f"AI译审时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'译审失败: {str(e)}'}), 500

async def perform_single_review(data, source_text, target_text, source_lang, target_lang):
    """单模型译审"""
    try:
        config = data.get('config', {})
        api_key = config.get('api_key', '')
        model = config.get('model', '')

        if not api_key or not model:
            return jsonify({'error': 'API密钥和模型不能为空'}), 400

        translator = create_translator('openrouter', api_key)

        # 构建译审提示词
        review_prompt = f"""请对以下翻译质量进行专业评估：

原文（{source_lang}）：
{source_text}

译文（{target_lang}）：
{target_text}

请从以下几个方面进行评估：
1. 准确性：译文是否准确传达了原文的意思
2. 流畅度：译文是否自然流畅，符合目标语言习惯
3. 术语使用：专业术语是否翻译准确
4. 文化适应性：是否考虑了文化差异
5. 完整性：是否有遗漏或增添的内容

请给出评分（0-100分）和详细的评估意见，并提供改进建议。

请按以下格式输出：
评分：[分数]
评估：[详细评估内容]
建议：[改进建议]"""

        response = translator.translate(
            review_prompt,
            source_lang='中文',
            target_lang='中文',
            model=model,
            system_prompt="你是专业的翻译质量评审员，请客观评估译文质量。",
            user_prompt=review_prompt,
            temperature=0.3
        )

        if not response:
            return jsonify({'error': '译审失败'}), 500

        # 解析响应
        score = 'N/A'
        review = response
        suggestions = ''

        if '评分：' in response or '评分:' in response:
            parts = response.split('\n')
            for i, part in enumerate(parts):
                if '评分' in part:
                    score = part.split('：')[-1].split(':')[-1].strip()
                elif '评估' in part:
                    review_start = i
                    for j in range(review_start + 1, len(parts)):
                        if '建议' in parts[j]:
                            review = '\n'.join(parts[review_start+1:j])
                            suggestions = '\n'.join(parts[j+1:])
                            break

        return jsonify({
            'success': True,
            'score': score,
            'review': review if review else response,
            'suggestions': suggestions
        })

    except Exception as e:
        logger.error(f"单模型译审失败: {str(e)}")
        return jsonify({'error': f'译审失败: {str(e)}'}), 500

async def perform_dual_review(data, source_text, target_text, source_lang, target_lang):
    """双模型对比译审"""
    try:
        config1 = data.get('config1', {})
        config2 = data.get('config2', {})

        # 并发调用两个模型
        tasks = []

        # 模型1
        translator1 = create_translator('openrouter', config1.get('api_key', ''))
        review_prompt = f"""请对以下翻译质量进行专业评估：

原文（{source_lang}）：
{source_text}

译文（{target_lang}）：
{target_text}

请从以下几个方面进行评估：
1. 准确性：译文是否准确传达了原文的意思
2. 流畅度：译文是否自然流畅，符合目标语言习惯
3. 术语使用：专业术语是否翻译准确
4. 文化适应性：是否考虑了文化差异
5. 完整性：是否有遗漏或增添的内容

请给出评分（0-100分）和详细的评估意见，并提供改进建议。

请按以下格式输出：
评分：[分数]
评估：[详细评估内容]
建议：[改进建议]"""

        response1 = translator1.translate(
            review_prompt,
            source_lang='中文',
            target_lang='中文',
            model=config1.get('model', ''),
            system_prompt="你是专业的翻译质量评审员，请客观评估译文质量。",
            user_prompt=review_prompt,
            temperature=0.3
        )

        # 模型2
        translator2 = create_translator('openrouter', config2.get('api_key', ''))
        response2 = translator2.translate(
            review_prompt,
            source_lang='中文',
            target_lang='中文',
            model=config2.get('model', ''),
            system_prompt="你是专业的翻译质量评审员，请客观评估译文质量。",
            user_prompt=review_prompt,
            temperature=0.3
        )

        if not response1 or not response2:
            return jsonify({'error': '译审失败'}), 500

        # 解析两个模型的响应
        def parse_review(response):
            score = 'N/A'
            review = response
            suggestions = ''

            if '评分：' in response or '评分:' in response:
                parts = response.split('\n')
                for i, part in enumerate(parts):
                    if '评分' in part:
                        score = part.split('：')[-1].split(':')[-1].strip()
                    elif '评估' in part:
                        review_start = i
                        for j in range(review_start + 1, len(parts)):
                            if '建议' in parts[j]:
                                review = '\n'.join(parts[review_start+1:j])
                                suggestions = '\n'.join(parts[j+1:])
                                break

            return {
                'score': score,
                'review': review if review else response,
                'suggestions': suggestions
            }

        review1 = parse_review(response1)
        review2 = parse_review(response2)

        # 对比分析
        comparison_prompt = f"""你需要对两个AI模型的译审结果进行对比分析：

模型1的评估：
{response1}

模型2的评估：
{response2}

请分析：
1. 两个模型的评估有哪些共同点？
2. 两个模型的评估有哪些不同之处？
3. 哪个模型的评估更全面、更准确？
4. 综合两个模型的意见，给出最终建议。"""

        comparison = translator1.translate(
            comparison_prompt,
            source_lang='中文',
            target_lang='中文',
            model=config1.get('model', ''),
            system_prompt="你是译审结果对比分析员，请提炼关键差异并给出综合结论。",
            user_prompt=comparison_prompt,
            temperature=0.5
        )

        return jsonify({
            'success': True,
            'review1': review1,
            'review2': review2,
            'comparison': comparison
        })

    except Exception as e:
        logger.error(f"双模型对比译审失败: {str(e)}")
        return jsonify({'error': f'译审失败: {str(e)}'}), 500

async def perform_two_stage_review(data, source_text, target_text, source_lang, target_lang):
    """双阶段推理与人机协同译审"""
    try:
        scan_config = data.get('scan_config', {})
        calibration_config = data.get('calibration_config', {})

        genre = data.get('genre', '通用')
        few_shot = data.get('few_shot', '')
        human_notes = data.get('human_notes', '')

        if not scan_config.get('api_key') or not scan_config.get('model'):
            return jsonify({'error': '初筛扫描的API密钥和模型不能为空'}), 400

        if not calibration_config.get('api_key') or not calibration_config.get('model'):
            return jsonify({'error': '深度校准的API密钥和模型不能为空'}), 400

        logger.info("双阶段译审启动: 初筛扫描 -> 深度校准")
        logger.info(f"体裁: {genre}")

        scan_translator = create_translator('openrouter', scan_config.get('api_key', ''))

        scan_prompt = f"""你是译文质量初筛扫描器，请快速识别译文中的显性错误片段。
只需标注明显的问题（如漏译、错译、术语误用、语法错误、数字/时间/专名错误）。
请输出标准化JSON数组，每一项必须包含：
- error_text: 译文中的错误片段原文
- index: 错误在译文中的起始索引（从0开始）
- category: 错误类别（accuracy/fluency/terminology/style/logic/consistency/omission/addition）
- suggestion: 修正建议

原文（{source_lang}）：
{source_text}

译文（{target_lang}）：
{target_text}

只输出JSON数组，不要输出其他文字。"""

        scan_output = scan_translator.translate(
            scan_prompt,
            source_lang='中文',
            target_lang='中文',
            model=scan_config.get('model', ''),
            system_prompt="你是译文质量初筛扫描器，请仅输出JSON数组。",
            user_prompt=scan_prompt,
            temperature=0.2
        )

        calibration_translator = create_translator('openrouter', calibration_config.get('api_key', ''))

        calibration_prompt = f"""你是强推理译审专家，请结合初筛扫描结果进行深度校准。
目标：解决逻辑疑点、篇章一致性问题，并输出可追溯的结构化JSON。

体裁：{genre}
人类关注点（可选）：{human_notes or '无'}

初筛扫描结果（JSON数组）：
{scan_output}

Few-shot 示例（如果有）： 
{few_shot or '无'}

原文（{source_lang}）：
{source_text}

译文（{target_lang}）：
{target_text}

输出要求（只输出JSON对象）：
{{
  "summary": "整体结论与质量概述",
  "errors": [
    {{
      "error_text": "译文错误片段",
      "index": 0,
      "category": "accuracy/fluency/terminology/style/logic/consistency/omission/addition",
      "suggestion": "修正建议",
      "reason": "判定原因"
    }}
  ],
  "consistency_notes": "跨段落一致性/逻辑链条的说明",
  "final_suggestion": "最终改进建议"
}}

请确保JSON合法，不包含额外解释性文本。"""

        calibration_output = calibration_translator.translate(
            calibration_prompt,
            source_lang='中文',
            target_lang='中文',
            model=calibration_config.get('model', ''),
            system_prompt="你是强推理译审专家，请输出结构化JSON对象。",
            user_prompt=calibration_prompt,
            temperature=0.3
        )

        if not scan_output or not calibration_output:
            return jsonify({'error': '双阶段译审失败'}), 500

        return jsonify({
            'success': True,
            'genre': genre,
            'scan_output': scan_output,
            'calibration_output': calibration_output
        })

    except Exception as e:
        logger.error(f"双阶段译审失败: {str(e)}")
        return jsonify({'error': f'译审失败: {str(e)}'}), 500

async def perform_meeting_review(data, source_text, target_text, source_lang, target_lang):
    """模型议会译审 - 多专家民主表决"""
    try:
        experts = data.get('experts', [])

        if len(experts) < 3:
            return jsonify({'error': '模型议会模式至少需要3个专家'}), 400

        # 收集每个专家的意见
        opinions = []

        for expert in experts:
            role = expert.get('role', '专家')
            config = expert.get('config', {})
            icon = expert.get('icon', 'fa-user')

            api_key = config.get('api_key', '')
            model = config.get('model', '')

            if not api_key or not model:
                continue

            translator = create_translator('openrouter', api_key)

            # 根据专家角色构建专门的提示词
            role_prompts = {
                '术语专家': '请以术语专家的身份，重点评估专业术语的翻译准确性和一致性。',
                '流畅度专家': '请以流畅度专家的身份，重点评估译文的自然度和可读性。',
                '文化适应性专家': '请以文化适应性专家的身份，重点评估译文是否考虑了文化差异和本地化需求。',
                '准确性专家': '请以准确性专家的身份，重点评估译文是否完整准确地传达了原文的意思。',
                '风格专家': '请以风格专家的身份，重点评估译文的写作风格和语言风格是否恰当。',
                '语法专家': '请以语法专家的身份，重点评估译文的语法正确性和语言规范性。'
            }

            role_instruction = role_prompts.get(role, f'请以{role}的身份进行评估。')

            expert_prompt = f"""{role_instruction}

原文（{source_lang}）：
{source_text}

译文（{target_lang}）：
{target_text}

请从你的专业角度给出评分（0-100分）和详细意见。"""

            response = translator.translate(
                expert_prompt,
                source_lang='中文',
                target_lang='中文',
                model=model,
                system_prompt=f"你是{role}，请从专业角度给出译审意见。",
                user_prompt=expert_prompt,
                temperature=0.4
            )

            if response:
                opinions.append({
                    'role': role,
                    'icon': icon,
                    'opinion': response
                })

            # 防止API速率限制
            await asyncio.sleep(1)

        if len(opinions) == 0:
            return jsonify({'error': '所有专家评审均失败'}), 500

        # 民主表决 - 综合所有专家意见
        consensus_prompt = f"""你是译审会议的主持人。以下是{len(opinions)}位专家的评审意见：

"""
        for i, opinion in enumerate(opinions, 1):
            consensus_prompt += f"\n【{opinion['role']}】的意见：\n{opinion['opinion']}\n"

        consensus_prompt += f"""

请你作为主持人：
1. 总结各位专家的共识
2. 指出专家们的分歧点
3. 综合所有意见，给出最终评分（0-100分）
4. 提供最终的改进建议

这是一个民主表决的过程，请综合多数专家的意见，给出公正客观的最终结论。"""

        # 使用第一个专家的配置来生成最终共识
        first_expert_config = experts[0].get('config', {})
        final_translator = create_translator(
            'openrouter',
            first_expert_config.get('api_key', '')
        )

        consensus = final_translator.translate(
            consensus_prompt,
            source_lang='中文',
            target_lang='中文',
            model=first_expert_config.get('model', ''),
            system_prompt="你是译审会议主持人，请综合专家意见形成最终结论。",
            user_prompt=consensus_prompt,
            temperature=0.3
        )

        # 提取最终评分
        final_score = 'N/A'
        if consensus and ('评分' in consensus or '分数' in consensus):
            import re
            score_match = re.search(r'(\d+)分', consensus)
            if score_match:
                final_score = score_match.group(1)

        return jsonify({
            'success': True,
            'opinions': opinions,
            'consensus': consensus,
            'final_score': final_score
        })

    except Exception as e:
        logger.error(f"模型议会译审失败: {str(e)}")
        return jsonify({'error': f'译审失败: {str(e)}'}), 500

if __name__ == '__main__':
    import sys

    logger.info("=" * 60)
    logger.info("ATP: AI-driven Translation Platform 启动中...")
    logger.info("=" * 60)

    # 检查是否使用开发模式
    dev_mode = '--dev' in sys.argv or True  # 默认开发模式

    if dev_mode:
        logger.info("🚀 开发模式：启用热重载和自动刷新")
        logger.info("📝 修改代码后会自动重启，无需手动重启！")
        logger.info("🌐 访问地址: http://localhost:5000")
        logger.info("=" * 60)

        # 使用 Flask 内置开发服务器（支持异步）
        # Flask 2.3+ 原生支持异步视图
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,  # 开启调试模式，自动重载
            use_reloader=True,  # 启用重载器
            threaded=True,  # 使用线程模式处理请求
        )
    else:
        logger.info("🚀 生产模式：使用 Hypercorn ASGI 服务器")
        logger.info("🌐 访问地址: http://localhost:5000")
        logger.info("=" * 60)

        # 生产环境使用 hypercorn
        import hypercorn.asyncio
        import hypercorn.config

        config = hypercorn.config.Config()
        config.bind = ["0.0.0.0:5000"]
        config.workers = 2  # 使用多进程

        asyncio.run(hypercorn.asyncio.serve(app, config)) 
