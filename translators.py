import json
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class BaseTranslator:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def translate(
        self,
        text: str,
        source_lang: str = "英文",
        target_lang: str = "中文",
        model: str = "openai/gpt-4o",
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        temperature: float = 1.0,
    ) -> Optional[str]:
        raise NotImplementedError


class OpenRouterTranslator(BaseTranslator):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://openrouter.ai/api/v1"

    def translate(
        self,
        text: str,
        source_lang: str = "英文",
        target_lang: str = "中文",
        model: str = "openai/gpt-4o",
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        temperature: float = 1.0,
    ) -> Optional[str]:
        try:
            if not model:
                raise ValueError("模型名称不能为空")

            if not system_prompt:
                system_prompt = (
                    f"你是一个专业翻译，擅长从{source_lang}到{target_lang}的翻译。"
                    "请保持原文的语气和风格，确保翻译准确、流畅。"
                )

            if not user_prompt:
                user_prompt = f"请将以下内容翻译为{target_lang}:\n\n{text}"

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "top_p": 0.95,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "max_tokens": 2000,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()

            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"].strip()

            logger.error("OpenRouter 返回结果格式错误: %s", result)
            return None
        except Exception as exc:
            logger.error("OpenRouter 翻译出错: %s", exc)
            return None


def create_translator(api_type: str, api_key: str) -> BaseTranslator:
    """
    统一使用 OpenRouter API 进行模型调用。
    """
    return OpenRouterTranslator(api_key)
