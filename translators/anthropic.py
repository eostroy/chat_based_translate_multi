import requests
import json
import time
from .base import BaseTranslator

class AnthropicTranslator(BaseTranslator):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key
        }
        self.default_system_prompt = "你是一个专业翻译，擅长从{source_lang}到{target_lang}的翻译。"
        self.default_user_prompt = "请将以下内容翻译为{target_lang}: {text}"
    
    def translate(self, text, source_lang="英文", target_lang="中文", model="claude-3.7-sonnet-20250219",
                 system_prompt=None, user_prompt=None, temperature=1.0,
                 include_reasoning=False):
        try:
            system_prompt = system_prompt or self.default_system_prompt
            user_prompt = user_prompt or self.default_user_prompt
            
            system_prompt = system_prompt.format(
                source_lang=source_lang,
                target_lang=target_lang
            )
            user_prompt = user_prompt.format(
                target_lang=target_lang,
                text=text
            )
            
            messages = [
                {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}
            ]
            
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 4000,
                "temperature": temperature
            }
            
            json_data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            
            headers = self.headers.copy()
            headers["Content-Type"] = "application/json; charset=utf-8"
            
            response = requests.post(self.api_url, headers=headers, data=json_data)
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result["content"][0]["text"]
                
                if self._is_translation_complete(text, translated_text):
                    return translated_text
                else:
                    print("警告：翻译结果可能不完整，将重试...")
                    time.sleep(2)
                    return self.translate(text, source_lang, target_lang, model,
                                        system_prompt, user_prompt, temperature,
                                        include_reasoning)
                    
            elif response.status_code == 429:
                print("遇到速率限制，等待后重试...")
                time.sleep(5)
                return self.translate(text, source_lang, target_lang, model,
                                    system_prompt, user_prompt, temperature,
                                    include_reasoning)
            else:
                raise Exception(f"API调用失败: {response.status_code}, {response.text}")
        
        except Exception as e:
            print(f"翻译过程中出现错误: {str(e)}")
            return None 
