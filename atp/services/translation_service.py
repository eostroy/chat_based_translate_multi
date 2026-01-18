import asyncio
import logging
import os
import time
import traceback
from typing import Optional

from atp.services.text_processing import TextProcessor
from atp.translators import create_translator

logger = logging.getLogger(__name__)


async def process_translation(
    file_path: str,
    api_type: str,
    api_key: str,
    model: str,
    source_lang: str,
    target_lang: str,
    system_prompt: Optional[str],
    user_prompt: Optional[str],
    temperature: float,
    output_folder: str,
    max_tokens: int = 2000,
) -> dict:
    try:
        processor = TextProcessor(max_tokens=max_tokens)
        translator = create_translator(api_type, api_key)

        logger.info("开始提取文本内容")
        text = processor.extract_from_file(file_path)

        if not text or len(text.strip()) == 0:
            logger.error("提取的文本内容为空")
            return {'error': '提取的文本内容为空，请检查文件是否有效'}

        logger.info("文本提取完成，长度：%s 字符", len(text))

        logger.info("开始处理文本")
        chunks = processor.process_text(text)

        logger.info("文本处理完成，共分为 %s 个文本块", len(chunks))

        for i, (prev_text, current_text) in enumerate(chunks):
            logger.info("块 %s: %s 字符", i + 1, len(current_text))

        logger.info("开始翻译，共 %s 个块", len(chunks))
        translated_chunks = []

        for i, (prev_text, current_text) in enumerate(chunks):
            logger.info("正在翻译第 %s/%s 块...", i + 1, len(chunks))
            translated_chunk = translator.translate(
                current_text,
                source_lang=source_lang,
                target_lang=target_lang,
                model=model,
                system_prompt=system_prompt if system_prompt else None,
                user_prompt=user_prompt if user_prompt else None,
                temperature=temperature,
            )

            if translated_chunk:
                translated_chunks.append(translated_chunk)
                logger.info("块 %s 翻译完成", i + 1)
            else:
                logger.warning("块 %s 翻译失败，将重试...", i + 1)
                await asyncio.sleep(2)
                translated_chunk = translator.translate(
                    current_text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    model=model,
                    system_prompt=system_prompt if system_prompt else None,
                    user_prompt=user_prompt if user_prompt else None,
                    temperature=temperature,
                )

                if translated_chunk:
                    translated_chunks.append(translated_chunk)
                    logger.info("块 %s 重试翻译成功", i + 1)
                else:
                    logger.error("块 %s 翻译失败", i + 1)
                    translated_chunks.append(f"[翻译失败] {current_text[:100]}...")

            if i < len(chunks) - 1:
                await asyncio.sleep(2)

        translated_text = '\n\n'.join(translated_chunks)

        timestamp = int(time.time())
        output_filename = f"translated_{timestamp}_{os.path.basename(file_path)}.txt"
        output_path = os.path.join(output_folder, output_filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_text)

        logger.info("翻译完成，结果已保存至 %s", output_path)

        return {
            'success': True,
            'message': '翻译完成',
            'output_file': output_filename,
        }

    except Exception as e:
        logger.error("处理文件时出错: %s", str(e))
        logger.error(traceback.format_exc())
        return {'error': f'处理失败: {str(e)}'}
