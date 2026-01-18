import asyncio
import logging
import re
from typing import Dict, Tuple

from atp.translators import create_translator

logger = logging.getLogger(__name__)


def _parse_review_response(response: str) -> Dict[str, str]:
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
                        review = '\n'.join(parts[review_start + 1:j])
                        suggestions = '\n'.join(parts[j + 1:])
                        break

    return {
        'score': score,
        'review': review if review else response,
        'suggestions': suggestions,
    }


async def perform_single_review(
    data: dict,
    source_text: str,
    target_text: str,
    source_lang: str,
    target_lang: str,
) -> Tuple[dict, int]:
    try:
        config = data.get('config', {})
        api_key = config.get('api_key', '')
        model = config.get('model', '')

        if not api_key or not model:
            return {'error': 'API密钥和模型不能为空'}, 400

        translator = create_translator('openrouter', api_key)

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
            temperature=0.3,
        )

        if not response:
            return {'error': '译审失败'}, 500

        parsed = _parse_review_response(response)

        return {
            'success': True,
            'score': parsed['score'],
            'review': parsed['review'],
            'suggestions': parsed['suggestions'],
        }, 200

    except Exception as e:
        logger.error("单模型译审失败: %s", str(e))
        return {'error': f'译审失败: {str(e)}'}, 500


async def perform_dual_review(
    data: dict,
    source_text: str,
    target_text: str,
    source_lang: str,
    target_lang: str,
) -> Tuple[dict, int]:
    try:
        config1 = data.get('config1', {})
        config2 = data.get('config2', {})

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

        translator1 = create_translator('openrouter', config1.get('api_key', ''))
        response1 = translator1.translate(
            review_prompt,
            source_lang='中文',
            target_lang='中文',
            model=config1.get('model', ''),
            system_prompt="你是专业的翻译质量评审员，请客观评估译文质量。",
            user_prompt=review_prompt,
            temperature=0.3,
        )

        translator2 = create_translator('openrouter', config2.get('api_key', ''))
        response2 = translator2.translate(
            review_prompt,
            source_lang='中文',
            target_lang='中文',
            model=config2.get('model', ''),
            system_prompt="你是专业的翻译质量评审员，请客观评估译文质量。",
            user_prompt=review_prompt,
            temperature=0.3,
        )

        if not response1 or not response2:
            return {'error': '译审失败'}, 500

        review1 = _parse_review_response(response1)
        review2 = _parse_review_response(response2)

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
            temperature=0.5,
        )

        return {
            'success': True,
            'review1': review1,
            'review2': review2,
            'comparison': comparison,
        }, 200

    except Exception as e:
        logger.error("双模型对比译审失败: %s", str(e))
        return {'error': f'译审失败: {str(e)}'}, 500


async def perform_two_stage_review(
    data: dict,
    source_text: str,
    target_text: str,
    source_lang: str,
    target_lang: str,
) -> Tuple[dict, int]:
    try:
        scan_config = data.get('scan_config', {})
        calibration_config = data.get('calibration_config', {})

        genre = data.get('genre', '通用')
        few_shot = data.get('few_shot', '')
        human_notes = data.get('human_notes', '')

        if not scan_config.get('api_key') or not scan_config.get('model'):
            return {'error': '初筛扫描的API密钥和模型不能为空'}, 400

        if not calibration_config.get('api_key') or not calibration_config.get('model'):
            return {'error': '深度校准的API密钥和模型不能为空'}, 400

        logger.info("双阶段译审启动: 初筛扫描 -> 深度校准")
        logger.info("体裁: %s", genre)

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
            temperature=0.2,
        )

        calibration_translator = create_translator(
            'openrouter',
            calibration_config.get('api_key', ''),
        )

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
            temperature=0.3,
        )

        if not scan_output or not calibration_output:
            return {'error': '双阶段译审失败'}, 500

        return {
            'success': True,
            'genre': genre,
            'scan_output': scan_output,
            'calibration_output': calibration_output,
        }, 200

    except Exception as e:
        logger.error("双阶段译审失败: %s", str(e))
        return {'error': f'译审失败: {str(e)}'}, 500


async def perform_meeting_review(
    data: dict,
    source_text: str,
    target_text: str,
    source_lang: str,
    target_lang: str,
) -> Tuple[dict, int]:
    try:
        experts = data.get('experts', [])

        if len(experts) < 3:
            return {'error': '模型开会模式至少需要3个专家'}, 400

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

            role_prompts = {
                '术语专家': '请以术语专家的身份，重点评估专业术语的翻译准确性和一致性。',
                '流畅度专家': '请以流畅度专家的身份，重点评估译文的自然度和可读性。',
                '文化适应性专家': '请以文化适应性专家的身份，重点评估译文是否考虑了文化差异和本地化需求。',
                '准确性专家': '请以准确性专家的身份，重点评估译文是否完整准确地传达了原文的意思。',
                '风格专家': '请以风格专家的身份，重点评估译文的写作风格和语言风格是否恰当。',
                '语法专家': '请以语法专家的身份，重点评估译文的语法正确性和语言规范性。',
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
                temperature=0.4,
            )

            if response:
                opinions.append({
                    'role': role,
                    'icon': icon,
                    'opinion': response,
                })

            await asyncio.sleep(1)

        if len(opinions) == 0:
            return {'error': '所有专家评审均失败'}, 500

        consensus_prompt = f"""你是译审会议的主持人。以下是{len(opinions)}位专家的评审意见：

"""
        for opinion in opinions:
            consensus_prompt += f"\n【{opinion['role']}】的意见：\n{opinion['opinion']}\n"

        consensus_prompt += """

请你作为主持人：
1. 总结各位专家的共识
2. 指出专家们的分歧点
3. 综合所有意见，给出最终评分（0-100分）
4. 提供最终的改进建议

这是一个民主表决的过程，请综合多数专家的意见，给出公正客观的最终结论。"""

        first_expert_config = experts[0].get('config', {})
        final_translator = create_translator(
            'openrouter',
            first_expert_config.get('api_key', ''),
        )

        consensus = final_translator.translate(
            consensus_prompt,
            source_lang='中文',
            target_lang='中文',
            model=first_expert_config.get('model', ''),
            system_prompt="你是译审会议主持人，请综合专家意见形成最终结论。",
            user_prompt=consensus_prompt,
            temperature=0.3,
        )

        final_score = 'N/A'
        if consensus and ('评分' in consensus or '分数' in consensus):
            score_match = re.search(r'(\d+)分', consensus)
            if score_match:
                final_score = score_match.group(1)

        return {
            'success': True,
            'opinions': opinions,
            'consensus': consensus,
            'final_score': final_score,
        }, 200

    except Exception as e:
        logger.error("模型开会译审失败: %s", str(e))
        return {'error': f'译审失败: {str(e)}'}, 500
