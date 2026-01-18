from abc import ABC, abstractmethod

class BaseTranslator(ABC):
    def __init__(self, api_key):
        self.api_key = api_key
        
    @abstractmethod
    def translate(self, text, source_lang="英文", target_lang="中文",
                 model=None, system_prompt=None, user_prompt=None, temperature=1.0,
                 include_reasoning=False):
        """翻译文本的抽象方法"""
        pass
    
    def _is_translation_complete(self, source_text, translated_text):
        """检查翻译是否完整"""
        # 检查翻译结果是否为空
        if not translated_text or translated_text.isspace():
            return False
            
        # 检查翻译结果是否过短（可能是截断）
        if len(translated_text) < len(source_text) * 0.1:
            return False
            
        # 检查是否包含明显的截断标记
        if translated_text.endswith('...') or translated_text.endswith('…'):
            return False
            
        # 检查段落数量是否合理
        source_paragraphs = len(source_text.split('\n\n'))
        translated_paragraphs = len(translated_text.split('\n\n'))
        
        if translated_paragraphs < source_paragraphs * 0.3:
            return False
            
        # 检查翻译结果是否包含明显的错误标记
        if '[翻译失败]' in translated_text or '[ERROR]' in translated_text:
            return False
            
        return True 
