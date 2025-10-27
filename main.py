from api_client import APIClient
from data_processor import extract_context, files_to_citations
from prompt_builder import build_chat_prompt
from guard import validate_user_input, validate_prompt
from config import config
import time
import requests
from response_evaluator import integrate_with_rag_flow, format_evaluation_report
from typing import List, Dict  # 实现多行对话需要

# 初始化客户端
client = APIClient()

def run_multi_turn_chat(db_name: str = None, enable_evaluation: bool = False):
    """
    多轮对话：循环读取用户输入，将历史对话与检索上下文拼接到 Prompt
    指令：
    - 输入 'exit' 结束对话
    - 输入 'clear' 清空历史
    """
    import requests
    history: List[Dict[str, str]] = []

    # 若未提供数据库名，则自动创建并上传测试数据
    if not db_name:
        db_name = f"student_{config.USER_NAME}_{int(time.time())}"
        print(f"创建新数据库: {db_name}")
        try:
            create_resp = requests.post(
                f"{config.BASE_URL}/databases",
                json={
                    "database_name": db_name,
                    "token": config.TOKEN,
                    "metric_type": config.DEFAULT_METRIC_TYPE
                }
            )
            if create_resp.status_code != 200:
                print(f"创建数据库失败: {create_resp.text}")
                return
            print(f"数据库创建成功: {db_name}")
            upload_test_data(db_name)
        except Exception as e:
            print(f"创建数据库时出错: {e}")
            return

    print("进入多轮对话模式（输入 'exit' 退出，'clear' 清空历史）")
    while True:
        user_input = input("你：").strip()
        if user_input.lower() == "exit":
            print("已退出。")
            break
        if user_input.lower() == "clear":
            history.clear()
            print("对话历史已清空。")
            continue

        if not validate_user_input(user_input):
            print("您的输入包含敏感内容或过长，请修改后重试。")
            continue

        # 检索与上下文
        search_result = client.search(db_name, user_input)
        context = extract_context(search_result)
        citations = files_to_citations(search_result)

        # 构建包含历史的 Prompt
        prompt = build_chat_prompt(history, user_input, context, citations)

        if not validate_prompt(prompt):
            print("生成的提示词存在安全风险，请联系管理员。")
            continue

        # 生成回答
        response = client.dialogue(prompt)
        print(f"助手：{response}")

        # 记录历史
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})

        # 可选：回答质量评估
        if enable_evaluation:
            _, evaluation_report = integrate_with_rag_flow(
                response, user_input, context)
            print(evaluation_report)


def upload_test_data(db_name: str):
    """上传测试数据到数据库"""
    import requests
    files = [
        {"file": "hello world, 网络安全测试", "metadata": {"description": "测试文件1"}},
        {"file": "第二条测试文本", "metadata": {"description": "测试文件2"}},
        {"file": "网络安全是指保护网络系统及其数据免受攻击、损坏或未经授权访问的过程。",
            "metadata": {"description": "网络安全定义"}},
        {"file": "防火墙是一种网络安全系统，用于监控和控制传入和传出的网络流量。",
            "metadata": {"description": "防火墙定义"}}
    ]

    payload = {
        "files": files,
        "token": config.TOKEN
    }

    resp = requests.post(
        f"{config.BASE_URL}/databases/{db_name}/files", json=payload)
    if resp.status_code == 200:
        print(f"测试数据上传成功到数据库: {db_name}")
        # 等待索引完成
        time.sleep(config.WAIT_TIME)
        return resp.json()
    else:
        print(f"数据上传失败: {resp.text}")
        return None


if __name__ == "__main__":
    # 创建数据库
    db_name = f"student_{config.USER_NAME}_{int(time.time())}"

    # 创建数据库
    print(f"🔧 创建数据库: {db_name}")
    import requests
    create_resp = requests.post(
        f"{config.BASE_URL}/databases",
        json={
            "database_name": db_name,
            "token": config.TOKEN,
            "metric_type": config.DEFAULT_METRIC_TYPE
        }
    )
    if create_resp.status_code != 200:
        print(f"❌ 创建数据库失败: {create_resp.text}")
    else:
        print(f"✅ 数据库创建成功: {db_name}")

        # 上传测试数据
        upload_test_data(db_name)

        print("=== 进入多轮对话示例 ===")
        run_multi_turn_chat(db_name, enable_evaluation=True)
