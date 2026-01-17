from .deepseek import DeepseekTranslator
from .openai import OpenAITranslator
from .anthropic import AnthropicTranslator
from .google import GoogleTranslator
from .openrouter import OpenRouterTranslator

def create_translator(api_type, api_key):
    """
    根据API类型创建对应的翻译器实例
    
    参数:
        api_type: API类型（deepseek/openai/anthropic/google/openrouter）
        api_key: API密钥
    
    返回:
        翻译器实例
    """
    translators = {
        'deepseek': DeepseekTranslator,
        'openai': OpenAITranslator,
        'anthropic': AnthropicTranslator,
        'google': GoogleTranslator,
        'openrouter': OpenRouterTranslator,
    }
    
    if api_type not in translators:
        raise ValueError(f"不支持的API类型: {api_type}")
        
    return translators[api_type](api_key) 
