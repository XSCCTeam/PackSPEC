#!/usr/bin/python3
"""
钉钉 Markdown 消息发送脚本

通过自定义消息服务 API 发送 Markdown 格式的测试结果消息，
支持 @指定用户。消息内容和标题通过命令行参数指定。

用法:
    send_md_message.py --api_key <key> --title <title> --text <text> --md_path <path> [--at_mobiles <mobiles>]

参数:
    --api_key:     API 密钥（通过环境变量 BOSC_API_KEY 传递更安全）
    --title:       消息标题
    --text:        消息正文摘要
    --md_path:     要发送的 Markdown 文件路径（内容会嵌入消息中）
    --at_mobiles:  要 @ 的手机号（可选）

环境变量:
    BOSC_MESSAGE_URL: 消息服务基础 URL，默认 http://172.38.8.102:8848
"""

import requests
import json
import argparse
import os

def send_md_message(api_key, title, text, md_path, at_mobiles=None):
    """
    发送Markdown格式消息到指定API
    
    Args:
        api_key: API密钥
        title: 消息标题
        text: 消息内容
        md_path: Markdown文件路径
        at_mobiles: 要@的手机号列表(可选)
    """
    url = os.getenv('BOSC_MESSAGE_URL', 'http://172.38.8.102:8848') + '/custom-send'
    
    at_content = {"isAtAll": False, "atUserIds": None}
    if at_mobiles:
        at_content["atMobiles"] = [at_mobiles]

    with open(md_path, 'r', encoding='utf-8') as file:
        markdown_text = file.read()
    
    payload_text = f"## {title}\n\n{text}\n\n```bash\n{markdown_text}\n```"

    payload = {
        "content": json.dumps({
            "at": at_content,
            "markdown": {
                "text": payload_text,
                "title": title
            },
            "msgtype": "markdown"
        })
    }
    
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response_data = response.json()
        
        if response_data.get("status") == "success":
            print(f"消息发送成功！响应内容：{response_data}")
        else:
            print(f"消息发送失败！成功状态：{response_data.get('status')}, 响应内容：{response_data}")
    except Exception as e:
        print(f"请求发生错误: {str(e)}")

if __name__ == "__main__":
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='发送Markdown格式消息到指定API')
    # 添加api_key参数
    parser.add_argument('--api_key', required=True, help='API密钥')
    # 添加title参数
    parser.add_argument('--title', required=True, help='消息标题')
    # 添加text参数
    parser.add_argument('--text', required=True, help='消息内容')
    # 添加md_path参数
    parser.add_argument('--md_path', required=True, help='Markdown消息内容')
    # 添加at_mobiles参数
    parser.add_argument('--at_mobiles', help='要@的手机号列表(可选)')

    # 解析命令行参数
    args = parser.parse_args()
    api_key = args.api_key
    title = args.title
    text = args.text
    md_path = args.md_path
    at_mobiles = args.at_mobiles
    
    send_md_message(api_key, title, text, md_path, at_mobiles)