from .openrouter import OpenRouterTranslator

def create_translator(api_type, api_key):
    """
    根据API类型创建对应的翻译器实例（仅支持 OpenRouter）

    参数:
        api_type: API类型（openrouter）
        api_key: API密钥

    返回:
        翻译器实例
    """
    if api_type and api_type != 'openrouter':
        raise ValueError(f"不支持的API类型: {api_type}")
    return OpenRouterTranslator(api_key)
