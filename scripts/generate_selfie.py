#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色自拍生成器 - 基于阿里云百炼 WAN 2.7 图生图 API
通过参考图保持角色一致性的自拍照片生成

使用方法:
    python3 generate_selfie.py "场景描述" [--ref_image PATH] [--size 1280*1280]

环境变量:
    SELFIE_API_KEY: 阿里云百炼 API Key（从.env 文件读取）
    REF_IMAGE_PATH：参考图本地路径（从.env 文件读取）
"""

import requests
import json
import argparse
import os
import base64
import time
from datetime import datetime

# 默认配置
DEFAULT_SIZE = "1280*1280"
DEFAULT_OUTPUT_DIR = os.path.expanduser("~/.hermes/selfie")

# 支持的分辨率（必须是 16 的倍数，范围 [768*768, 2048*2048]）
SUPPORTED_SIZES = [
    "1280*1280",  # 1:1 正方形（默认）
    "1280*720",   # 16:9 横版
    "720*1280",   # 9:16 竖版（自拍推荐）
    "1280*853",   # 3:2 横版
    "853*1280",   # 2:3 竖版
    "1536*1024",  # 3:2 横版
    "1024*1536",  # 2:3 竖版
    "1920*1080",  # 16:9 全高清横版
    "1080*1920",  # 9:16 全高清竖版
    "2048*2048",  # 1:1 超高清正方形
]

# 百炼 API 端点
# 同步调用：直接返回图片
SYNC_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
# 异步调用：返回 task_id，需要轮询
ASYNC_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation"
# 任务查询端点
TASK_QUERY_URL = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"


def get_api_key():
    """从 ~/.hermes/.env 文件或环境变量获取 API Key"""
    env_file_path = os.path.expanduser("~/.hermes/.env")
    
    if os.path.exists(env_file_path):
        try:
            with open(env_file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key.strip() == "SELFIE_API_KEY":
                            api_key = value.strip()
                            if api_key:
                                print(f"✅ 从 ~/.hermes/.env 加载 API Key")
                                return api_key
        except Exception as e:
            print(f"⚠️ 读取 ~/.hermes/.env 失败：{e}")
    
    api_key = os.getenv("SELFIE_API_KEY")
    if not api_key:
        raise ValueError("未找到 SELFIE_API_KEY 环境变量或 ~/.hermes/.env 配置，请先配置")
    return api_key


def get_ref_image_path():
    """从 ~/.hermes/.env 文件获取角色参考图本地路径"""
    env_file_path = os.path.expanduser("~/.hermes/.env")
    
    if os.path.exists(env_file_path):
        try:
            with open(env_file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key.strip() == "REF_IMAGE_PATH":
                            return value.strip()
        except Exception as e:
            print(f"⚠️ 读取 REF_IMAGE_PATH 失败：{e}")
    
    return os.getenv("REF_IMAGE_PATH", "")


MODELS_API_URL = "https://dashscope.aliyuncs.com/api/v1/models"


def validate_api_key(api_key):
    """预检 API Key 有效性——调用百炼模型列表接口轻量验证"""
    if not api_key or not api_key.startswith("sk-"):
        raise ValueError("API Key 格式异常：应以 sk- 开头，请检查 ~/.hermes/.env 中的 SELFIE_API_KEY")

    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get(MODELS_API_URL, headers=headers, timeout=10)
        if resp.status_code == 401:
            raise ValueError("API Key 无效（401 Unauthorized），请检查 SELFIE_API_KEY 是否正确")
        resp.raise_for_status()
        print("✅ API Key 验证通过")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"API Key 验证请求失败：{e}")


def load_config():
    """从技能根目录加载 config.json，不存在则从 .example 拷贝"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.dirname(script_dir)
    config_path = os.path.join(skill_dir, "config.json")
    example_path = os.path.join(skill_dir, "config.json.example")

    if not os.path.exists(config_path):
        if os.path.exists(example_path):
            import shutil
            shutil.copy2(example_path, config_path)
            print(f"📄 从 config.json.example 初始化 {config_path}")
            print(f"⚠️ 请修改 {config_path} 中的 reference_image 配置你的角色参考图")
        else:
            print(f"⚠️ config.json 和 config.json.example 均不存在，使用纯场景 prompt")
            return {}

    with open(config_path, "r") as f:
        cfg = json.load(f)

    print(f"✅ 加载配置：{config_path}")
    return cfg


def build_prompt(scene_prompt, config):
    """拼接完整 prompt：character + 场景描述 + style + quality_fixes"""
    parts = []

    character = config.get("character", [])
    if character:
        parts.append("。".join(character))

    parts.append(scene_prompt)

    style = config.get("style", [])
    if style:
        parts.append("。".join(style))

    quality_fixes = config.get("quality_fixes", [])
    if quality_fixes:
        parts.append("。".join(quality_fixes))

    return "。".join(parts)


def image_to_base64(image_path):
    """将本地图片转换为 base64 编码"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"参考图文件不存在：{image_path}")
    
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    # 检测图片格式
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }.get(ext, "image/jpeg")
    
    base64_data = base64.b64encode(image_data).decode("utf-8")
    return f"data:{mime_type};base64,{base64_data}"


def submit_async_task(prompt, ref_image_base64=None, size=DEFAULT_SIZE, api_key=None):
    """
    提交异步图像生成任务
    
    参数:
        prompt: 场景描述提示词
        ref_image_base64: 参考图 base64 编码（可选）
        size: 分辨率
        api_key: API Key
    
    返回:
        task_id: 任务 ID
    """
    messages_content = [{"text": prompt}]
    
    if ref_image_base64:
        messages_content.append({"image": ref_image_base64})
    
    payload = {
        "model": "wan2.7-image",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": messages_content
                }
            ]
        },
        "parameters": {
            "thinking_mode": True,
            "watermark": False,
            "n": 1,
            "enable_sequential": False,
            "size": size
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-DashScope-Async": "enable"
    }
    
    print(f"📤 提交异步任务...")
    response = requests.post(ASYNC_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()
    
    if "output" in result and "task_id" in result["output"]:
        task_id = result["output"]["task_id"]
        task_status = result["output"].get("task_status", "UNKNOWN")
        print(f"✅ 任务提交成功，task_id: {task_id}, 状态：{task_status}")
        return task_id
    else:
        raise Exception(f"任务提交失败：{result}")


def query_async_task(task_id, api_key):
    """
    查询异步任务状态
    
    参数:
        task_id: 任务 ID
        api_key: API Key
    
    返回:
        dict: 任务查询结果
    """
    url = TASK_QUERY_URL.format(task_id=task_id)
    headers = {"Authorization": f"Bearer {api_key}"}
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def wait_for_async_task(task_id, api_key, timeout=300, interval=5):
    """
    轮询等待异步任务完成
    
    状态流转：PENDING → RUNNING → SUCCEEDED / FAILED
    
    参数:
        task_id: 任务 ID
        api_key: API Key
        timeout: 超时时间（秒）
        interval: 轮询间隔（秒）
    
    返回:
        dict: 任务完成后的响应结果
    """
    print(f"⏳ 等待任务完成...")
    start_time = datetime.now()
    last_status = ""
    
    while (datetime.now() - start_time).total_seconds() < timeout:
        result = query_async_task(task_id, api_key)
        task_status = result.get("output", {}).get("task_status", "UNKNOWN")
        
        # 状态变化时打印提示
        if task_status != last_status:
            status_desc = {
                "PENDING": "排队中",
                "RUNNING": "处理中",
                "SUCCEEDED": "成功",
                "FAILED": "失败",
                "CANCELED": "已取消",
                "UNKNOWN": "未知状态"
            }
            print(f"  状态：{task_status} ({status_desc.get(task_status, '未知')})")
            last_status = task_status
        
        if task_status == "SUCCEEDED":
            print(f"✅ 任务执行成功！")
            return result
        elif task_status == "FAILED":
            error_msg = result.get("output", {}).get("message", "未知错误")
            raise Exception(f"任务执行失败：{error_msg}")
        elif task_status == "CANCELED":
            raise Exception("任务已被取消")
        elif task_status in ["PENDING", "RUNNING"]:
            # 继续轮询
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"  已等待 {elapsed:.0f} 秒...")
            time.sleep(interval)
        elif task_status == "UNKNOWN":
            # 任务不存在或状态未知，继续尝试
            print(f"  ⚠️ 任务状态未知，继续查询...")
            time.sleep(interval)
        else:
            # 其他未知状态
            print(f"  ⚠️ 未预期的状态：{task_status}")
            time.sleep(interval)
    
    raise Exception(f"任务超时（{timeout}秒），可能仍在处理中")


def generate_selfie_async(scene_prompt, ref_image_path=None, size=DEFAULT_SIZE, output_path=None, timeout=300):
    """
    生成角色自拍照片（异步调用）
    
    参数:
        scene_prompt: 场景描述提示词
        ref_image_path: 角色参考图本地路径（可选）
        size: 分辨率，如 "1024*1024"
        output_path: 输出文件路径（可选）
        timeout: 超时时间（秒）
    
    返回:
        dict: {"success": bool, "url": str, "path": str, "time": float} 或 {"success": False, "error": str}
    """
    api_key = get_api_key()
    validate_api_key(api_key)

    config = load_config()
    scene_prompt = build_prompt(scene_prompt, config)

    if not ref_image_path:
        ref_image_path = os.path.expanduser(config.get("reference_image") or get_ref_image_path())

    start_time = datetime.now()

    try:
        # 加载参考图并转 base64
        ref_image_base64 = None
        if ref_image_path:
            print(f"📷 加载参考图：{ref_image_path}")
            try:
                ref_image_base64 = image_to_base64(ref_image_path)
                print(f"✅ 参考图已转换为 base64")
            except Exception as e:
                print(f"⚠️ 加载参考图失败：{e}，将使用纯文生图模式")
        
        # 提交异步任务
        task_id = submit_async_task(scene_prompt, ref_image_base64, size, api_key)
        
        # 轮询等待完成
        result = wait_for_async_task(task_id, api_key, timeout)
        
        # 解析响应 - 异步响应路径：output.choices[0].message.content[0].image
        choices = result.get("output", {}).get("choices", [])
        if not choices:
            raise Exception("响应中没有 choices")
        
        image_url = choices[0].get("message", {}).get("content", [{}])[0].get("image")
        if not image_url:
            raise Exception("未找到生成的图片 URL")
        
        print(f"🔗 图片 URL: {image_url}")
        
        # 下载图片
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(DEFAULT_OUTPUT_DIR, f"luna_selfie_{timestamp}.png")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print(f"📥 下载图片到：{output_path}")
        img_response = requests.get(image_url, timeout=60)
        img_response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(img_response.content)
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        print(f"⏱️  总耗时：{elapsed_time:.2f}秒")
        
        return {
            "success": True,
            "url": image_url,
            "path": output_path,
            "time": elapsed_time
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败：{e}")
        return {"success": False, "error": f"网络请求失败：{e}"}
    except Exception as e:
        print(f"❌ 生成失败：{e}")
        return {"success": False, "error": str(e)}


def generate_selfie(scene_prompt, ref_image_path=None, size=DEFAULT_SIZE, output_path=None):
    """
    生成角色自拍照片（同步调用）
    
    参数:
        scene_prompt: 场景描述提示词
        ref_image_path: 角色参考图本地路径（可选）
        size: 分辨率，如 "1024*1024"
        output_path: 输出文件路径（可选）
    
    返回:
        dict: {"success": bool, "url": str, "path": str, "time": float} 或 {"success": False, "error": str}
    """
    api_key = get_api_key()
    validate_api_key(api_key)

    config = load_config()
    scene_prompt = build_prompt(scene_prompt, config)

    # 如果没有提供参考图，优先从 config.json 读取，fallback 到 .env
    if not ref_image_path:
        ref_image_path = os.path.expanduser(config.get("reference_image") or get_ref_image_path())

    start_time = datetime.now()
    
    # 构造请求体
    messages_content = [
        {
            "text": scene_prompt
        }
    ]
    
    # 如果有参考图，添加到 messages 中
    if ref_image_path:
        print(f"📷 加载参考图：{ref_image_path}")
        try:
            ref_image_base64 = image_to_base64(ref_image_path)
            messages_content.append({
                "image": ref_image_base64
            })
            print(f"✅ 参考图已转换为 base64")
        except Exception as e:
            print(f"⚠️ 加载参考图失败：{e}，将使用纯文生图模式")
    
    payload = {
        "model": "wan2.7-image",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": messages_content
                }
            ]
        },
        "parameters": {
            "thinking_mode": True,
            "watermark": False,
            "n": 1,
            "enable_sequential": False,
            "size": size
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    print(f"📤 提交生成任务...")
    print(f"提示词：{scene_prompt}")
    print(f"分辨率：{size}")
    if ref_image_path:
        print(f"参考图：{ref_image_path}")
    
    try:
        # 同步调用 API
        response = requests.post(SYNC_API_URL, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()
        
        # 检查响应
        if "output" not in result:
            raise Exception(f"API 响应格式异常：{result}")
        
        # 解析响应 - 正确的路径：output.choices[0].message.content[0].image
        choices = result.get("output", {}).get("choices", [])
        if not choices:
            raise Exception("响应中没有 choices")
        
        image_url = choices[0].get("message", {}).get("content", [{}])[0].get("image")
        if not image_url:
            raise Exception("未找到生成的图片 URL")
        
        print(f"✅ 生成成功！")
        print(f"🔗 图片 URL: {image_url}")
        
        # 下载图片
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(DEFAULT_OUTPUT_DIR, f"luna_selfie_{timestamp}.png")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print(f"📥 下载图片到：{output_path}")
        img_response = requests.get(image_url, timeout=60)
        img_response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(img_response.content)
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        print(f"⏱️  总耗时：{elapsed_time:.2f}秒")
        
        return {
            "success": True,
            "url": image_url,
            "path": output_path,
            "time": elapsed_time
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败：{e}")
        return {"success": False, "error": f"网络请求失败：{e}"}
    except Exception as e:
        print(f"❌ 生成失败：{e}")
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="角色自拍生成器 - 阿里云百炼 WAN 2.7")
    parser.add_argument("prompt", type=str, help="场景描述提示词")
    parser.add_argument("--ref_image", type=str, default=None, help="角色参考图本地路径")
    parser.add_argument("--size", type=str, default=DEFAULT_SIZE, choices=SUPPORTED_SIZES, help="分辨率")
    parser.add_argument("--output", type=str, default=None, help="输出文件路径")
    parser.add_argument("--async", dest="use_async", action="store_true", help="使用异步调用模式（适合大批量或耗时任务）")
    parser.add_argument("--timeout", type=int, default=300, help="异步任务超时时间（秒），默认 300 秒")
    
    args = parser.parse_args()
    
    # 根据参数选择同步或异步模式
    if args.use_async:
        print("🔄 使用异步调用模式")
        result = generate_selfie_async(args.prompt, args.ref_image, args.size, args.output, args.timeout)
    else:
        print("⚡ 使用同步调用模式")
        result = generate_selfie(args.prompt, args.ref_image, args.size, args.output)
    
    print("\n" + "=" * 60)
    if result["success"]:
        print("✅ 生成成功！")
        print(f"⏱️  耗时：{result['time']:.2f}秒")
        print(f"📁 保存：{result['path']}")
    else:
        print("❌ 生成失败！")
        print(f"❌ 错误：{result['error']}")
    print("=" * 60)
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit(main())
