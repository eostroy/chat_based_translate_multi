import os
import re
import json
import requests
from typing import List, Dict, Tuple, Optional

def load_term_glossary(filepath: str) -> Dict[str, str]:
    """从外部文件加载术语库
    
    Args:
        filepath: 术语库文件路径
        
    Returns:
        包含术语对应关系的字典
    """
    glossary = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            glossary = json.load(file)
        print(f"成功从 {filepath} 加载了 {len(glossary)} 个术语")
    except Exception as e:
        print(f"加载术语库出错: {e}")
        # 提供默认术语作为备份
        glossary = {
            "鬼谷子": "Guiguzi",
            "韩": "Han",
            "魏": "Wei",
            "秦": "Qin",
            "成皋": "Chenggao",
            "荥阳": "Xingyang"
        }
        print("使用默认术语库")
    return glossary

class TranslationValidator:
    def __init__(self, api_key: str, model: str = "deepseek-chat", term_glossary_path: str = "term_glossary.json"):
        self.api_key = api_key
        self.model = model
        self.previous_translations = []
        self.term_glossary = load_term_glossary(term_glossary_path)
        self.common_mistakes = self._load_common_mistakes()
        
    def _load_common_mistakes(self) -> Dict[str, List[str]]:
        """加载常见术语错误翻译
        
        Returns:
            术语错误翻译字典
        """
        # 此函数可以修改为从文件加载，目前使用硬编码的方式
        return {
            "鬼谷子": ["Ghost Valley Master", "Guigu Zi", "Master Guigu"],
            "韩": ["Korea", "Han State"],
            "魏": ["Wei State"],
            "秦": ["Qin State", "Chin"],
            "成皋": ["Cheng Gao", "Chenggao County"],
            "荥阳": ["Xing Yang", "Xingyang County"]
        }
        
    def load_aligned_document(self, filepath: str) -> List[Dict[str, str]]:
        aligned_texts = []
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                i = 0
                while i < len(lines):
                    if not lines[i].strip():
                        i += 1
                        continue
                    
                    if i + 1 < len(lines):
                        chinese = lines[i].strip()
                        english = lines[i+1].strip()
                        aligned_texts.append({
                            "chinese": chinese,
                            "english": english
                        })
                        i += 2
                    else:
                        i += 1
            return aligned_texts
        except Exception as e:
            print(f"加载文档出错: {e}")
            return []
    
    def check_terminology(self, chinese_text: str, english_text: str) -> Tuple[int, List[str]]:
        errors = []
        for cn_term, en_term in self.term_glossary.items():
            if cn_term in chinese_text:
                if en_term not in english_text:
                    error_msg = f"'{cn_term}' 正确译文应为 '{en_term}'"
                    wrong_translations = self._find_possible_wrong_translations(cn_term, english_text)
                    if wrong_translations:
                        error_msg += f", 但被翻译为 '{wrong_translations}'"
                    else:
                        error_msg += ", 但在译文中未找到"
                    errors.append(error_msg)
        return len(errors), errors
    
    def _find_possible_wrong_translations(self, cn_term: str, english_text: str) -> str:
        if cn_term in self.common_mistakes:
            for mistake in self.common_mistakes[cn_term]:
                if mistake in english_text:
                    return mistake
        return ""
    
    def analyze_with_llm(self, chinese_text: str, english_text: str, 
                         previous_texts: Optional[List[Dict[str, str]]] = None) -> Dict[str, str]:
        try:
            prompt = self._build_llm_prompt(chinese_text, english_text, previous_texts)
            return self._call_deepseek_api(prompt)
        except Exception as e:
            print(f"LLM分析出错: {e}")
            return {
                "语法错误": f"分析过程出错: {str(e)}",
                "语义错误": "",
                "风格与前文是否一致": ""
            }
    
    def _build_llm_prompt(self, chinese_text: str, english_text: str, 
                          previous_texts: Optional[List[Dict[str, str]]]) -> str:
        prompt = "请分析以下中文原文和英文译文的质量，并按指定格式输出分析结果：\n\n"
        prompt += f"中文原文：{chinese_text}\n"
        prompt += f"英文译文：{english_text}\n\n"
        
        if previous_texts and len(previous_texts) > 0:
            prompt += "以下是之前的翻译，请参考以判断风格一致性：\n"
            for idx, prev in enumerate(previous_texts[-3:]):
                prompt += f"上文{idx+1}原文：{prev['chinese']}\n"
                prompt += f"上文{idx+1}译文：{prev['english']}\n\n"
        
        prompt += "请严格按以下JSON格式提供分析结果，不要添加任何额外的格式化标记如```json或```，直接给出JSON对象：\n"
        prompt += "{\n"
        prompt += '  "语法错误": "详细说明译文中的语法错误，如果没有则填写无",\n'
        prompt += '  "语义错误": "详细说明译文中是否无故增加、减少或篡改了原文含义，或是存在影响理解的重大语义错误（如果不是原则性的错误，请不要列出），如果没有则填写无，此过程中不得修改原文！",\n'
        prompt += '  "风格与前文是否一致": "分析译文的风格是否与之前的翻译保持一致，如果没有上文则填写无法判断"\n'
        prompt += "}\n\n"
        prompt += "重要提示：不要使用任何代码块标记，直接输出JSON对象，确保JSON格式正确，所有引号必须匹配，内容中的引号需要适当转义。"
        
        return prompt
    
    def _call_deepseek_api(self, prompt: str) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 1.3,
            "max_tokens": 1000
        }
        
        try:
            # 增加编码参数，确保UTF-8编码正确
            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                data=json_data
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                try:
                    cleaned_content = content
                    json_pattern = r'```(?:json)?\s*(.*?)\s*```'
                    match = re.search(json_pattern, cleaned_content, re.DOTALL)
                    if match:
                        cleaned_content = match.group(1)
                    else:
                        cleaned_content = re.sub(r'```.*?\n', '', cleaned_content)
                        cleaned_content = re.sub(r'```', '', cleaned_content)
                    
                    analysis = json.loads(cleaned_content.strip())
                    return {
                        "语法错误": analysis.get("语法错误", "解析错误"),
                        "语义错误": analysis.get("语义错误", "解析错误"),
                        "风格与前文是否一致": analysis.get("风格与前文是否一致", "解析错误")
                    }
                except json.JSONDecodeError:
                    return self._extract_analysis_manually(content)
            else:
                return {
                    "语法错误": f"API调用失败: {response.status_code}",
                    "语义错误": response.text[:100] + "...",
                    "风格与前文是否一致": ""
                }
                
        except Exception as e:
            return {
                "语法错误": f"API调用过程出错: {str(e)}",
                "语义错误": "",
                "风格与前文是否一致": ""
            }
    
    def _extract_analysis_manually(self, content: str) -> Dict[str, str]:
        grammar_error = "无法解析"
        semantic_error = "无法解析"
        style_consistency = "无法解析"
        
        json_pattern = r'```(?:json)?\s*(.*?)\s*```'
        match = re.search(json_pattern, content, re.DOTALL)
        if match:
            content = match.group(1).strip()
        
        try:
            grammar_match = re.search(r'"语法错误"\s*:\s*"(.*?)(?:"[\s,}]|"$)', content, re.DOTALL)
            if grammar_match:
                grammar_error = grammar_match.group(1).replace('\n', ' ').strip()
            
            if grammar_error == "无法解析":
                grammar_match = re.search(r'语法错误["\s:]*([^"]*?)(?=[,}\n]|"语义)', content, re.DOTALL)
                if grammar_match:
                    grammar_error = grammar_match.group(1).replace('\n', ' ').strip()
            
            # 匹配语义错误
            semantic_match = re.search(r'"语义错误"\s*:\s*"(.*?)(?:"[\s,}]|"$)', content, re.DOTALL)
            if semantic_match:
                semantic_error = semantic_match.group(1).replace('\n', ' ').strip()
            
            if semantic_error == "无法解析":
                semantic_match = re.search(r'语义错误["\s:]*([^"]*?)(?=[,}\n]|"风格)', content, re.DOTALL)
                if semantic_match:
                    semantic_error = semantic_match.group(1).replace('\n', ' ').strip()
            
            # 匹配风格一致性
            style_match = re.search(r'"风格与前文是否一致"\s*:\s*"(.*?)(?:"[\s,}]|"$)', content, re.DOTALL)
            if style_match:
                style_consistency = style_match.group(1).replace('\n', ' ').strip()
            
            if style_consistency == "无法解析":
                style_match = re.search(r'风格与前文是否一致["\s:]*([^"]*?)(?=[,}\n]|$)', content, re.DOTALL)
                if style_match:
                    style_consistency = style_match.group(1).replace('\n', ' ').strip()
            
        except Exception as e:
            return {
                "语法错误": "解析失败",
                "语义错误": content[:200] + "..." if len(content) > 200 else content,
                "风格与前文是否一致": f"解析出错: {str(e)}"
            }
        
        if grammar_error == "无法解析" and semantic_error == "无法解析" and style_consistency == "无法解析":
            return {
                "语法错误": "无法提取结构化分析结果",
                "语义错误": content[:200] + "..." if len(content) > 200 else content,
                "风格与前文是否一致": "无法解析"
            }
        
        return {
            "语法错误": grammar_error,
            "语义错误": semantic_error,
            "风格与前文是否一致": style_consistency
        }
    
    def validate_translation(self, chinese_text: str, english_text: str) -> Dict:
        term_error_count, term_errors = self.check_terminology(chinese_text, english_text)
        
        llm_analysis = self.analyze_with_llm(chinese_text, english_text, self.previous_translations)
        
        self.previous_translations.append({
            "chinese": chinese_text,
            "english": english_text
        })
        
        if len(self.previous_translations) > 10:
            self.previous_translations = self.previous_translations[-10:]
        
        return {
            "term_error_count": term_error_count,
            "term_errors": term_errors,
            "llm_analysis": llm_analysis
        }
    
    def validate_document(self, filepath: str) -> List[Dict]:
        results = []
        aligned_texts = self.load_aligned_document(filepath)
        
        for text_pair in aligned_texts:
            chinese = text_pair["chinese"]
            english = text_pair["english"]
            validation_result = self.validate_translation(chinese, english)
            result = {
                "chinese": chinese,
                "english": english,
                **validation_result
            }
            results.append(result)
        
        return results


def generate_report(validation_results: List[Dict]) -> str:
    report = "# 翻译验证报告\n\n"
    total_term_errors = 0
    all_term_errors = []
    
    for idx, result in enumerate(validation_results):
        chinese = result["chinese"]
        english = result["english"]
        term_error_count = result["term_error_count"]
        term_errors = result["term_errors"]
        llm_analysis = result["llm_analysis"]
        
        total_term_errors += term_error_count
        all_term_errors.extend(term_errors)
        
        report += f"## 段落 {idx+1}\n\n"
        report += f"**原文：** {chinese}\n\n"
        report += f"**译文：** {english}\n\n"
        
        report += f"**术语错误 ({term_error_count})：**\n\n"
        if term_errors:
            for error in term_errors:
                report += f"- {error}\n"
        else:
            report += "无术语错误\n"
        
        report += "\n**大语言模型分析：**\n\n"
        report += f"- 语法错误：{llm_analysis['语法错误']}\n"
        report += f"- 语义错误：{llm_analysis['语义错误']}\n"
        report += f"- 风格一致性：{llm_analysis['风格与前文是否一致']}\n\n"
        
        report += "---\n\n"
    
    report += "# 总结\n\n"
    report += f"- 总术语错误数：{total_term_errors}\n"
    
    if total_term_errors > 0:
        report += "- 所有术语错误：\n"
        for error in all_term_errors:
            report += f"  - {error}\n"
    
    return report

# 创建示例术语库文件（仅首次运行时需要）
def create_example_glossary_file(filepath: str = "term_glossary.json"):
    """创建示例术语库文件
    
    Args:
        filepath: 术语库文件保存路径
    """
    example_glossary = {
        "鬼谷子": "Guiguzi",
        "韩": "Han",
        "魏": "Wei",
        "秦": "Qin",
        "成皋": "Chenggao",
        "荥阳": "Xingyang"
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(example_glossary, file, ensure_ascii=False, indent=4)
        print(f"示例术语库已保存到 {filepath}")
    except Exception as e:
        print(f"创建术语库文件出错: {e}")

if __name__ == "__main__":
    # 如果术语库文件不存在，创建示例文件
    if not os.path.exists("term_glossary.json"):
        create_example_glossary_file()
    
    validator = TranslationValidator(api_key="sk-71ffb35e193e46d8acbb2817617e9401")
    
    # 测试文本
    chinese_text = "《鬼谷子》说韩、魏: \"大王不事秦，秦下帼赢阳，断绝韩之地，夺取成皋(今河南荥阳县)，荥阳(今河南荥阳县东北)，则 鸿台之宫，鹿台之观无缓日矣。\""
    english_text = "When persuading the State of Wei, he states: \"If Your Majesty does not submit to Qin, Qin will dispatch troops to Yingyang, sever the territory of Han, seize Chenggao (present-day Xingyang County, Henan), and Xingyang (northeast of present-day Xingyang County, Henan), then your palaces and pavilions will soon be in peril.\""
    
    result = validator.validate_translation(chinese_text, english_text)
    print(f"术语错误数: {result['term_error_count']}")
    print(f"术语错误: {result['term_errors']}")
    print(f"LLM分析: {result['llm_analysis']}")
    
    # 如果需要从文件验证整个文档，取消以下注释并提供正确的文件路径
    """
    aligned_doc_path = "aligned_document.txt"
    if os.path.exists(aligned_doc_path):
        print("\n=== 测试文档验证 ===")
        document_results = validator.validate_document(aligned_doc_path)
        report = generate_report(document_results)
        
        # 将报告保存到文件
        with open("translation_report.md", "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"报告已保存到 translation_report.md")
    else:
        print(f"文件 {aligned_doc_path} 不存在")
    """
