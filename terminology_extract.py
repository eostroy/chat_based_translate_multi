from openai import OpenAI

client = OpenAI(
    api_key="",
    base_url="https://api.deepseek.com"
)

def terminology_extract(text):
    
    prompt = f"请提取文本中的地理术语：{text}"

    messages = [
        {"role": "system", "content": "你是一个术语专家，擅长识别文本中的专业术语。"},
        {"role": "user", "content": prompt}
    ]
    
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=messages,
    )
        
    result = response.choices[0].message.content.strip()
    
    print(result)

with open (r"file_path", 'r', encoding="utf-8") as f:
    text = f.read()
    terminology_extract(text)