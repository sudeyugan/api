import re
from typing import List

# 敏感词列表（可从外部加载或配置）
SENSITIVE_WORDS = ["密码", "密钥", "root", "admin", "删除数据库"]

def validate_user_input(user_input: str) -> bool:
    """
    检测用户输入中的敏感词、长度等
    :param user_input: 用户原始输入
    :return: True 表示安全，False 表示不安全
    """
    if len(user_input) > 500:
        return False
    if any(word in user_input for word in SENSITIVE_WORDS):
        return False
    # 更复杂的正则检测（如SQL注入特征）
    sql_patterns = [
        r"(?i)select.*from",
        r"(?i)drop\s+table",
        r"(?i)insert\s+into",
        r"(?i)union\s+select"
    ]
    for pattern in sql_patterns:
        if re.search(pattern, user_input):
            return False
    return True

def validate_prompt(prompt: str) -> bool:
    """
    检测拼接后 Prompt 的安全性（防止 Prompt 注入）
    :param prompt: 最终构建的 Prompt
    :return: True 表示安全，False 表示不安全
    """
    injection_patterns = [
        r"(?i)ignore\s+next",
        r"(?i)system\s+prompt",
        r"(?i)you\s+are\s+now",
        r"(?i)forget\s+previous",
        r"(?i)output\s+only"
    ]
    for pattern in injection_patterns:
        if re.search(pattern, prompt):
            return False
    return True