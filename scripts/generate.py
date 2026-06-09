"""搜狐热帖生成器 — AI 生成短文 + 自动配图"""
import argparse
import json
import os
import random
import string
from datetime import datetime, timezone, timedelta

import anthropic
import requests

CST = timezone(timedelta(hours=8))

SYSTEM_PROMPT = """你是搜狐新闻自媒体作者"江"，每天发布有营养的原创短内容，不标题党，不博眼球。

你的写作风格由 style 参数决定：
- style=chatty：轻松闲聊型。像跟朋友聊天一样分享一个热点话题。口语化、自然、有个人感受。可使用适当的 emoji。字数控制在150-200字。必须原创，不要以"//@某人"的形式转发。
- style=newsflash：一句话快讯型。用一句简洁的话说清楚一个热点事件的要点。纯事实陈述，不带观点和情绪。字数控制在50-80字。

话题选择：从最近的社会、科技、财经、文娱、生活等领域的广泛热点中选取。不局限于单一领域。

除了文字内容，你还需要输出1-3个英文图片搜索关键词（image_keywords），用于从免费图库为帖子匹配一张相关配图。关键词应该具体、视觉化（如"electric car charging station"而不是"car"）。

输出格式必须是严格的 JSON，不要输出其他内容：
{"content": "帖子正文", "image_keywords": ["keyword1", "keyword2", "keyword3"]}"""


def generate_post_text(style: str) -> dict:
    """调用 Claude API 生成帖子文字和图片关键词"""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"请生成一篇 style={style} 的帖子。"
        }]
    )

    raw = message.content[0].text.strip()
    # 提取 JSON（处理可能的 markdown 代码块）
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    return json.loads(raw)


def search_image(keywords: list[str]) -> tuple[str | None, str | None]:
    """用关键词搜索 Unsplash，返回 (image_url, image_credit)"""
    for keyword in keywords:
        url = "https://api.unsplash.com/search/photos"
        params = {
            "query": keyword,
            "per_page": 1,
            "orientation": "landscape"
        }
        resp = requests.get(
            url,
            params=params,
            headers={"Accept-Version": "v1"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                photo = results[0]
                image_url = photo["urls"]["regular"]
                credit = f"Photo by {photo['user']['name']} / Unsplash"
                return image_url, credit

    return None, None


POSTS_FILE = "data/posts.json"
MAX_POSTS = 200


def load_posts() -> list[dict]:
    """读取现有帖子"""
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_posts(posts: list[dict]):
    """写入帖子，保留最近 MAX_POSTS 条"""
    trimmed = posts[:MAX_POSTS]
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)


def append_post(post: dict):
    """将新帖子插入到数组头部"""
    posts = load_posts()
    posts.insert(0, post)
    save_posts(posts)


def make_post_id() -> str:
    """生成唯一 ID: YYYYMMDD-HHMMSS-随机6位"""
    now = datetime.now(CST)
    ts = now.strftime("%Y%m%d-%H%M%S")
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{ts}-{rand}"


def main():
    parser = argparse.ArgumentParser(description="生成一篇搜狐热帖")
    parser.add_argument(
        "--style",
        choices=["chatty", "newsflash"],
        default="chatty",
        help="帖子风格"
    )
    args = parser.parse_args()

    # 1. 生成文字
    result = generate_post_text(args.style)
    content = result["content"]
    keywords = result["image_keywords"]

    # 2. 搜索配图
    image_url, image_credit = search_image(keywords)

    # 3. 组装帖子
    post = {
        "id": make_post_id(),
        "content": content,
        "style": args.style,
        "image_url": image_url,
        "image_credit": image_credit,
        "created_at": datetime.now(CST).isoformat()
    }

    # 4. 写入 JSON
    append_post(post)
    print(f"Generated post: {post['id']}")
    print(f"  style: {args.style}")
    print(f"  content: {content[:60]}...")
    print(f"  image: {image_url or 'none'}")


if __name__ == "__main__":
    main()
