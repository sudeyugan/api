from flask import Flask, request, jsonify
from flask_cors import CORS
from api_client import APIClient
from data_processor import extract_context, files_to_citations
from prompt_builder import build_chat_prompt
from guard import validate_user_input, validate_prompt
from response_evaluator import integrate_with_rag_flow
from config import config
import time
import requests
from typing import List, Dict
import logging

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局变量存储对话历史和数据库名
history: List[Dict[str, str]] = []
db_name = None

logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为 INFO。DEBUG日志将不显示，INFO, WARNING, ERROR 都会记录。
    filename='app_security.log',  # 指定日志输出到的文件名
    filemode='a',  # 'a' = append (追加模式), 'w' = write (覆盖模式)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # 定义日志行的格式
    encoding='utf-8' # 确保中文日志（如敏感词）不会乱码
)


client = APIClient()

def initialize_database():
    """初始化数据库"""
    global db_name
    db_name = f"student_{config.USER_NAME}_{int(time.time())}"
    
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
            return False
            
        print(f"数据库创建成功: {db_name}")
        
        # 上传测试数据
        files = [
            {"file": "hello world, 网络安全测试", "metadata": {"description": "测试文件1"}},
            {"file": "第二条测试文本", "metadata": {"description": "测试文件2"}},
            {"file": "网络安全是指保护网络系统及其数据免受攻击、损坏或未经授权访问的过程。",
                "metadata": {"description": "网络安全定义"}},
            {"file": "防火墙是一种网络安全系统,用于监控和控制传入和传出的网络流量。",
                "metadata": {"description": "防火墙定义"}}
        ]
        
        payload = {
            "files": files,
            "token": config.TOKEN
        }
        
        resp = requests.post(
            f"{config.BASE_URL}/databases/{db_name}/files", json=payload)
            
        if resp.status_code == 200:
            print(f"测试数据上传成功")
            time.sleep(config.WAIT_TIME)
            return True
        else:
            print(f"数据上传失败: {resp.text}")
            return False
            
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        return False

@app.route('/chat', methods=['POST'])
def chat():
    """处理聊天请求 - 完整版本"""
    global history
    
    # ========== 1. 接收和验证输入 ==========
    data = request.json
    user_input = data.get('message', '').strip()
    enable_evaluation = data.get('enable_evaluation', False)
    
    if not user_input:
        return jsonify({'error': '消息不能为空'}), 400
    
    # ✅ 调用 guard.py 中的函数
    if not validate_user_input(user_input):
        return jsonify({'error': '您的输入包含敏感内容或过长，请修改后重试'}), 400
    
    try:
        # ========== 2. 检索相关文档 ==========
        # ✅ 调用 api_client.py 中的函数
        search_result = client.search(db_name, user_input)
        
        # ========== 3. 提取上下文和引用 ==========
        # ✅ 调用 data_processor.py 中的函数
        context = extract_context(search_result)
        citations = files_to_citations(search_result)
        
        # ========== 4. 构建包含历史的 Prompt ==========
        # ✅ 调用 prompt_builder.py 中的函数
        prompt = build_chat_prompt(history, user_input, context, citations)
        
        # ========== 5. Prompt 安全检测 ==========
        # ✅ 调用 guard.py 中的函数
        if not validate_prompt(prompt):
            return jsonify({'error': '生成的提示词存在安全风险'}), 400
        
        # ========== 6. 生成回答 ==========
        # ✅ 调用 api_client.py 中的函数
        response = client.dialogue(prompt)
        
        # ========== 7. 更新对话历史 ==========
        # ✅ 这部分是 app.py 自己管理的
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})
        
        # ========== 8. 准备响应数据 ==========
        response_data = {
            'response': response,
            'citations': citations
        }
        
        # ========== 9. 可选：回答质量评估 ==========
        if enable_evaluation:
            # ✅ 调用 response_evaluator.py 中的函数
            _, evaluation_report = integrate_with_rag_flow(
                response, user_input, context
            )
            response_data['evaluation'] = evaluation_report
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"处理请求时出错: {e}")
        return jsonify({'error': f'处理请求失败: {str(e)}'}), 500

@app.route('/clear', methods=['POST'])
def clear_history():
    """清空对话历史"""
    global history
    history = []
    return jsonify({'status': 'success'})

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'database': db_name})

if __name__ == '__main__':
    print("正在初始化数据库...")
    if initialize_database():
        print("✅ 数据库初始化成功")
        print("🚀 启动 Flask 服务器...")
        app.run(host='127.0.0.1', port=5000, debug=True)
    else:
        print("❌ 数据库初始化失败，请检查配置")