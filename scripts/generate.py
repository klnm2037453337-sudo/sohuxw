"""搜狐热帖生成器 — AI 生成短文 + URL 参考"""
import argparse
import json
import os
import random
import string
from datetime import datetime, timezone, timedelta

from openai import OpenAI
import trafilatura

CST = timezone(timedelta(hours=8))

GENRE_PROMPTS = {
    "时事短评": "你是自媒体作者"江"。针对参考新闻写一篇小篇幅评论（无参考链接时自行选题）。有观点但不偏激，不标题党。口语化、自然、有个人感受。字数：{word_count}。",
    "国家政策": "你是自媒体作者"江"。用通俗易懂的语言解读一项国家政策或民生新规，让普通人能看懂。说人话，不念文件。字数：{word_count}。",
    "历史感悟": "你是自媒体作者"江"。讲一个历史故事，并从中提炼出对现代生活的启发。故事要生动，启发要有共鸣。字数：{word_count}。",
    "认知笔记": "你是自媒体作者"江"。介绍一个思维模型、心理学效应或认知偏误，用生活化的例子解释它。字数：{word_count}。",
    "医学健康科普": "你是自媒体作者"江"。科普一个医学健康知识（养生/疾病防治/用药/急救/心理）。科学准确但语言通俗。字数：{word_count}。",
    "生活常识科普": "你是自媒体作者"江"。科普一个日常生活实用知识（饮食/家居/安全/礼仪/消费）。实用、接地气。字数：{word_count}。",
    "人文社科科普": "你是自媒体作者"江"。科普一个人文社科知识点（历史/考古/语言/法律/经济/民俗/哲学）。有趣有料。字数：{word_count}。",
    "冷知识": "你是自媒体作者"江"。分享一个有趣的反常识冷知识，让人看完觉得"原来如此"。简短有力。字数：{word_count}。",
    "财经小课": "你是自媒体作者"江"。用通俗语言讲一个个人理财知识或经济概念，帮助读者避坑或省钱。字数：{word_count}。",
    "科技新知": "你是自媒体作者"江"。介绍一个新产品、AI工具或数码技巧，让读者了解科技前沿。字数：{word_count}。",
    "好物安利": "你是自媒体作者"江"。推荐一本书/电影/播客/工具，说明推荐理由和个人感受。真诚不浮夸。字数：{word_count}。",
    "美食札记": "你是自媒体作者"江"。介绍一道美食的做法或科普一个食材知识。让人看了有食欲或学到东西。字数：{word_count}。",
}

WORD_COUNT_MAP = {
    "极短": "30-60字",
    "短": "60-120字",
    "中": "120-200字",
    "长": "200-300字",
    "超长": "300-450字",
}

SYSTEM_PROMPT_TEMPLATE = """你是搜狐新闻自媒体作者"江"，每天发布有营养的原创短内容。

{genre_instruction}

输出格式必须是严格的 JSON：
{{"content": "帖子正文（纯文本，不包含标题）"}}

注意：
- 输出纯文本正文，不要加"标题："等前缀
- 不要使用 markdown 格式
- 如果有参考链接内容，基于它来写，但不要直接复制
- 如果没有参考链接，自行选择一个相关话题"""


def fetch_url_content(url: str) -> str | None:
    """抓取网页正文，失败返回 None"""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_links=False,
                                       include_images=False, include_tables=False)
            if text:
                return text[:3000]
    except Exception:
        pass
    return None


def generate_post_text(genre: str, word_count: str, source_url: str) -> dict:
    """调用 DeepSeek API 生成帖子"""
    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com"
    )

    word_range = WORD_COUNT_MAP.get(word_count, "120-200字")
    genre_instruction = GENRE_PROMPTS.get(genre, GENRE_PROMPTS["时事短评"]).format(word_count=word_range)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(genre_instruction=genre_instruction)

    user_message = ""
    if source_url:
        article_text = fetch_url_content(source_url)
        if article_text:
            user_message = f"请基于以下参考文章的内容写一篇帖子：\n\n{article_text}"
        else:
            user_message = f"请自行选择一个与「{genre}」相关的热点话题写一篇帖子。（参考链接抓取失败，请自由选题）"
    else:
        user_message = f"请自行选择一个与「{genre}」相关的热门话题写一篇帖子。"

    message = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=800,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    raw = message.choices[0].message.content.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    return json.loads(raw)


POSTS_FILE = "data/posts.json"
MAX_POSTS = 200


def load_posts() -> list[dict]:
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_posts(posts: list[dict]):
    trimmed = posts[:MAX_POSTS]
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)


def append_post(post: dict):
    posts = load_posts()
    posts.insert(0, post)
    save_posts(posts)


def make_post_id() -> str:
    now = datetime.now(CST)
    ts = now.strftime("%Y%m%d-%H%M%S")
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{ts}-{rand}"


def main():
    parser = argparse.ArgumentParser(description="生成一篇搜狐热帖")
    parser.add_argument("--genre", default="时事短评", help="内容类型")
    parser.add_argument("--word-count", default="中", help="字数档位")
    parser.add_argument("--source-url", default="", help="参考链接（可选）")
    args = parser.parse_args()

    result = generate_post_text(args.genre, args.word_count, args.source_url)

    post = {
        "id": make_post_id(),
        "content": result["content"],
        "genre": args.genre,
        "word_count": args.word_count,
        "created_at": datetime.now(CST).isoformat()
    }

    append_post(post)
    print(f"Generated post: {post['id']}")
    print(f"  genre: {args.genre}")
    print(f"  word_count: {args.word_count}")
    print(f"  source_url: {args.source_url or 'none'}")
    print(f"  content: {post['content'][:80]}...")


if __name__ == "__main__":
    main()
