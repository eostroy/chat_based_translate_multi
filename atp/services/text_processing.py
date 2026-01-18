import os
import re
import docx2txt
from docx import Document
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextProcessor:
    def __init__(self, max_tokens=2000):
        self.max_tokens = max_tokens
    
    def extract_from_file(self, file_path):
        """从文件中提取文本内容"""
        _, file_extension = os.path.splitext(file_path)
        
        logger.info(f"开始提取文件: {file_path}")
        
        if file_extension.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
        elif file_extension.lower() in ['.docx', '.doc']:
            try:
                text = docx2txt.process(file_path)
            except Exception as e:
                logger.error(f"使用docx2txt处理文件时出错: {str(e)}")
                logger.info("尝试使用python-docx替代...")
                doc = Document(file_path)
                text = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        else:
            raise ValueError(f"不支持的文件格式: {file_extension}")
        
        logger.info(f"文本提取完成，共 {len(text)} 字符")
        return text
    
    def clean_text(self, text):
        """清理文本，保留基本格式"""
        # 替换多个空行为单个空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 统一换行符
        text = re.sub(r'\r\n', '\n', text)
        # 去除控制字符
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        return text.strip()
    
    def split_paragraphs(self, text):
        """将文本分割为段落"""
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        logger.info(f"文本分段完成，共 {len(paragraphs)} 段")
        return paragraphs
    
    def count_tokens(self, text):
        """估算文本的token数量"""
        words = len(text.split())
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        return int(words * 1.3 + chinese_chars * 2)
    
    def chunk_text(self, paragraphs):
        """将文本分块，确保每块不超过最大token数"""
        chunks = []
        current_batch = []
        current_tokens = 0
        previous_batch = ""
        
        for para in paragraphs:
            para_tokens = self.count_tokens(para)
            
            if current_tokens + para_tokens > self.max_tokens:
                if current_batch:
                    current_text = '\n'.join(current_batch)
                    chunks.append((previous_batch, current_text))
                    previous_batch = current_text
                    current_batch = [para]
                    current_tokens = para_tokens
                else:
                    chunks.append((previous_batch, para))
                    previous_batch = para
                    current_batch = []
                    current_tokens = 0
            else:
                current_batch.append(para)
                current_tokens += para_tokens
        
        if current_batch:
            chunks.append((previous_batch, '\n'.join(current_batch)))
        
        logger.info(f"文本分块完成，共 {len(chunks)} 块")
        return chunks
    
    def process_text(self, text):
        """处理文本的主函数"""
        logger.info("开始处理文本...")
        cleaned_text = self.clean_text(text)
        
        if not cleaned_text:
            logger.error("清理后的文本为空")
            raise ValueError("清理后的文本为空")
            
        paragraphs = self.split_paragraphs(cleaned_text)
        
        if not paragraphs:
            logger.error("分段后没有内容")
            paragraphs = [cleaned_text]
            
        chunks = self.chunk_text(paragraphs)
        
        if not chunks:
            logger.error("分块后没有内容")
            chunks = [(cleaned_text, cleaned_text)]
        
        logger.info(f"文本处理完成，共生成 {len(chunks)} 个文本块")
        return chunks 