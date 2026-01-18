import logging
import os
from typing import Optional, Union

import requests

from .base import BaseTranslator

logger = logging.getLogger(__name__)


class OpenRouterTranslator(BaseTranslator):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://openrouter.ai/api/v1"
        self.site_url = os.getenv("OPENROUTER_SITE_URL") or os.getenv("OPENROUTER_REFERRER")
        self.app_title = os.getenv("OPENROUTER_APP_NAME", "ATP")

    def _build_headers(self) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.app_title:
            headers["X-Title"] = self.app_title
        return headers

    def translate(
        self,
        text: str,
        source_lang: str = "英文",
        target_lang: str = "中文",
        model: str = "openai/gpt-4o",
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        temperature: float = 1.0,
        include_reasoning: bool = False,
    ) -> Optional[Union[str, dict]]:
        try:
            if not self.api_key:
                raise ValueError("OpenRouter API密钥不能为空")

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
            if include_reasoning:
                payload["include_reasoning"] = True

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._build_headers(),
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()

            if "choices" in result and result["choices"]:
                message = result["choices"][0].get("message", {})
                content = (message.get("content") or "").strip()
                reasoning = message.get("reasoning") or message.get("reasoning_content")
                if include_reasoning:
                    return {"text": content, "reasoning": reasoning}
                return content

            logger.error("OpenRouter 返回结果格式错误: %s", result)
            return None
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response else "unknown"
            detail = exc.response.text if exc.response else "no response body"
            if include_reasoning and detail and "reason" in detail.lower():
                logger.warning("OpenRouter 推理字段不可用，回退为普通请求: %s", detail)
                return self.translate(
                    text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    model=model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    include_reasoning=False,
                )
            logger.error("OpenRouter 翻译出错: HTTP %s - %s", status, detail)
            return None
        except Exception as exc:
            logger.error("OpenRouter 翻译出错: %s", exc)
            return None
