import requests
import json
import time
import re

class DeepseekTranslator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        # 默认提示词
        self.default_system_prompt = "你是一个专业翻译，擅长从{source_lang}到{target_lang}的翻译。"
        self.default_user_prompt = "请将以下内容翻译为{target_lang}: {text}"
    
    def translate(self, text, source_lang="英文", target_lang="中文", model="deepseek-chat", 
                 system_prompt=None, user_prompt=None):
        
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
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            text_length = len(text)
            max_tokens = min(4000, text_length * 2)
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 1.0,
                "max_tokens": max_tokens,
                "top_p": 0.95,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }
            
            # 增加编码参数，确保UTF-8编码正确
            json_data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            
            # 同时明确指定Content-Type包含charset=utf-8
            headers = self.headers.copy()
            headers["Content-Type"] = "application/json; charset=utf-8"
            
            response = requests.post(self.api_url, headers=headers, data=json_data)
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result["choices"][0]["message"]["content"]
                
                if self._is_translation_complete(text, translated_text):
                    return translated_text
                else:
                    print("警告：翻译结果可能不完整，将重试...")
                    time.sleep(2)
                    return self.translate(text, source_lang, target_lang, model, 
                                        system_prompt, user_prompt)
                    
            elif response.status_code == 429:  # 速率限制
                print("遇到速率限制，等待后重试...")
                time.sleep(5)
                return self.translate(text, source_lang, target_lang, model, 
                                    system_prompt, user_prompt)
            else:
                raise Exception(f"API调用失败: {response.status_code}, {response.text}")
        
        except Exception as e:
            print(f"翻译过程中出现错误: {str(e)}")
            return None
    
    def _is_translation_complete(self, source_text, translated_text):
        """
        检查翻译是否完整
        """
        # 检查翻译结果是否为空
        if not translated_text or translated_text.isspace():
            return False
            
        # 检查翻译结果是否过短（可能是截断）
        # 对于中文到英文的翻译，翻译结果可能会比原文短
        # 对于英文到中文的翻译，翻译结果可能会比原文长
        # 所以这里放宽检查条件
        if len(translated_text) < len(source_text) * 0.1:  # 降低到10%
            return False
            
        # 检查是否包含明显的截断标记
        if translated_text.endswith('...') or translated_text.endswith('…'):
            return False
            
        # 检查段落数量是否合理
        source_paragraphs = len(source_text.split('\n\n'))
        translated_paragraphs = len(translated_text.split('\n\n'))
        
        # 放宽段落数量的检查条件
        if translated_paragraphs < source_paragraphs * 0.3:  # 降低到30%
            return False
            
        # 检查翻译结果是否包含明显的错误标记
        if '[翻译失败]' in translated_text or '[ERROR]' in translated_text:
            return False
            
        return True
    
    def batch_translate(self, text_chunks, source_lang="英文", target_lang="中文",
                       system_prompt=None, user_prompt=None):
        """
        批量翻译文本块
        
        参数:
            text_chunks: 文本块列表
            source_lang: 源语言
            target_lang: 目标语言
            system_prompt: 自定义系统提示词
            user_prompt: 自定义用户提示词
        
        返回:
            翻译后的文本块列表
        """
        translated_chunks = []
        
        for i, (prev_text, current_text) in enumerate(text_chunks):
            print(f"正在翻译第 {i+1}/{len(text_chunks)} 段...")
            
            # 尝试翻译，最多重试3次
            max_retries = 3
            for attempt in range(max_retries):
                translated = self.translate(current_text, source_lang, target_lang,
                                         system_prompt=system_prompt,
                                         user_prompt=user_prompt)
                if translated:
                    translated_chunks.append(translated)
                    break
                elif attempt < max_retries - 1:
                    print(f"第 {attempt + 1} 次翻译失败，等待后重试...")
                    time.sleep(2)
            
            if not translated:
                print(f"错误：第 {i+1} 段翻译失败，跳过此段")
                translated_chunks.append(f"[翻译失败] {current_text}")
            
            # 防止API速率限制
            if i < len(text_chunks) - 1:
                time.sleep(2)
        
        return translated_chunks 