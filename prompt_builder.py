from typing import List, Dict
def build_chat_prompt(history: List[Dict[str, str]], user_input: str, context: str, citations: List[Dict]) -> str:
    """
    组合系统 Prompt + 历史对话 + 当前用户输入 + 上下文 + 引用
    :param history: 历史对话 [{"role": "user"/"assistant", "content": "..."}]
    :param user_input: 当前用户问题
    :param context: 检索到的相关上下文
    :param citations: 引用列表
    :return: 最终发送给 LLM 的 Prompt（包含对话历史）
    """
    # 只取最近的若干条历史，避免过长
    truncated = history[-10:] if len(history) > 10 else history
    history_text = "\n".join([
        f"{'【用户】' if m['role']=='user' else '【助手】'}{m['content']}"
        for m in truncated
    ])

    citation_text = "\n".join([
        f"[{c['id']}] {c['snippet']} (来源: {c['link']})"
        for c in citations
    ])

    system_prompt = """你是一个网络安全助手。请结合检索到的上下文与此前的对话历史回答用户问题。
- 如果检索结果中包含相关信息，请基于这些信息作答，并在回答末尾标注对应的引用编号（如 [1][2]）。
- 如果检索结果中没有相关信息，请结合你自身的知识进行回答，但不要编造事实。
- 回答应尽量完整、简明、逻辑清晰。
- 保持对话连续性，必要时引用此前的关键信息。"""

    final_prompt = f"""{system_prompt}

【对话历史】
{history_text or '（无）'}

【用户问题】
{user_input}

【参考上下文】
{context}

【参考文献】
{citation_text}

请回答：
"""
    return final_prompt
