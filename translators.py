import os
import time
import logging
from typing import Optional, Dict, Any
import requests
import anthropic
import google.generativeai as genai
from openai import OpenAI
import json

logger = logging.getLogger(__name__)

class BaseTranslator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def translate(self, text: str, source_lang: str = "英文", target_lang: str = "中文", 
                 model: str = "deepseek-chat", system_prompt: Optional[str] = None,
                 user_prompt: Optional[str] = None, temperature: float = 1.0) -> Optional[str]:
        raise NotImplementedError

class DeepseekTranslator(BaseTranslator):
    def translate(self, text: str, source_lang: str = "英文", target_lang: str = "中文", 
                 model: str = "deepseek-chat", system_prompt: Optional[str] = None,
                 user_prompt: Optional[str] = None, temperature: float = 1.0) -> Optional[str]:
        try:
            # 根据模型选择不同的端点
            if model == "deepseek-chat":
                endpoint = f"{self.base_url}/chat/completions"
            elif model == "deepseek-reasoner":
                endpoint = f"{self.base_url}/chat/completions"
            else:
                raise ValueError(f"不支持的模型: {model}")

            # 构建系统提示词
            if not system_prompt:
                system_prompt = f"你是一个专业翻译，擅长从{source_lang}到{target_lang}的翻译。请保持原文的语气和风格，确保翻译准确、流畅。"

            # 构建用户提示词
            if not user_prompt:
                user_prompt = f"请将以下内容翻译为{target_lang}:\n\n{text}"

            # 根据模型设置不同的参数
            if model == "deepseek-chat":
                data = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": temperature,
                    "top_p": 0.95,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0,
                    "max_tokens": 2000
                }
            else:  # deepseek-reasoner
                data = {
                    "model": "deepseek-reasoner",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": temperature,
                    "top_p": 0.95,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0,
                    "max_tokens": 2000
                }

            # 增加编码参数，确保UTF-8编码正确
            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            headers = self.headers.copy()
            headers["Content-Type"] = "application/json; charset=utf-8"
            
            response = requests.post(endpoint, headers=headers, data=json_data)
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                translated_text = result["choices"][0]["message"]["content"].strip()
                return translated_text
            else:
                logger.error(f"API返回结果格式错误: {result}")
                return None
                
        except Exception as e:
            logger.error(f"翻译出错: {str(e)}")
            return None

class OpenAITranslator(BaseTranslator):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = OpenAI(api_key=api_key)
        
    def translate(self, text: str, source_lang: str = "英文", target_lang: str = "中文", 
                 model: str = "gpt-4o", system_prompt: Optional[str] = None,
                 user_prompt: Optional[str] = None, temperature: float = 1.0) -> Optional[str]:
        try:
            # 验证模型名称
            if model not in ["gpt-4o", "gpt-4.5-preview"]:
                raise ValueError(f"不支持的模型: {model}")

            # 构建系统提示词
            if not system_prompt:
                system_prompt = f"你是一个专业翻译，擅长从{source_lang}到{target_lang}的翻译。请保持原文的语气和风格，确保翻译准确、流畅。"

            # 构建用户提示词
            if not user_prompt:
                user_prompt = f"请将以下内容翻译为{target_lang}:\n\n{text}"

            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                top_p=0.95,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                max_tokens=2000
            )
            
            translated_text = response.choices[0].message.content.strip()
            return translated_text
                
        except Exception as e:
            logger.error(f"翻译出错: {str(e)}")
            return None

class AnthropicTranslator(BaseTranslator):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = anthropic.Anthropic(
            api_key=api_key,
            # 使用最新的 API 版本
            default_headers={
                "anthropic-version": "2023-06-01"
            }
        )
        
    def translate(self, text: str, source_lang: str = "英文", target_lang: str = "中文", 
                 model: str = "claude-3.7-sonnet-20250219", system_prompt: Optional[str] = None,
                 user_prompt: Optional[str] = None, temperature: float = 1.0) -> Optional[str]:
        try:
            # 验证模型名称
            if model not in ["claude-3.7-sonnet-20250219"]:
                raise ValueError(f"不支持的模型: {model}")

            # 构建系统提示词
            if not system_prompt:
                system_prompt = f"你是一个专业翻译，擅长从{source_lang}到{target_lang}的翻译。请保持原文的语气和风格，确保翻译准确、流畅。"

            # 构建用户提示词
            if not user_prompt:
                user_prompt = f"请将以下内容翻译为{target_lang}:\n\n{text}"

            # 调用 Anthropic API
            response = self.client.messages.create(
                model=model,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=temperature,
                max_tokens=2000
            )
            
            # 获取翻译结果
            if response.content and len(response.content) > 0:
                translated_text = response.content[0].text.strip()
                return translated_text
            else:
                logger.error("API返回结果为空")
                return None
                
        except Exception as e:
            logger.error(f"翻译出错: {str(e)}")
            return None

def create_translator(api_type: str, api_key: str) -> BaseTranslator:
    """
    根据API类型创建相应的翻译器实例
    """
    if api_type == "deepseek":
        return DeepseekTranslator(api_key)
    elif api_type == "openai":
        return OpenAITranslator(api_key)
    elif api_type == "anthropic":
        return AnthropicTranslator(api_key)
    elif api_type == "google":
        return GoogleTranslator(api_key)
    else:
        raise ValueError(f"不支持的API类型: {api_type}")

# ... existing code ... 