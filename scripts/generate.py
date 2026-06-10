"""搜狐热帖生成器 — 豆包 AI 生成短文 + 联网搜索多源改写"""
import argparse
import json
import os
import random
import string
from datetime import datetime, timezone, timedelta

from openai import OpenAI

CST = timezone(timedelta(hours=8))

# ============================================================
# Prompt 架构：PERSONA → TONE → GENRE_GUIDE（三层）
# ============================================================

PERSONA = """你是"江"，一个有思考深度的内容创作者，在搜狐新闻时间线发布原创短内容。

你的内容风格：
- 有信息增量——读者看完能学到东西或获得新视角
- 有自己的判断和观点，不人云亦云
- 语言干净利落，不啰嗦、不套话
- 尊重事实，不确定的事情会说明

发布平台：搜狐新闻时间线（类似微博的社交信息流）
- 字数上限 2000 字
- 需要附带相关的 #话题# 标签（1-2个）
- 短段落排版，每段不超过3行，方便手机阅读
- 目标：让读者愿意转发分享"""

TONE_FORMAL = """## 语气要求（正式-可读型）
- 保持正式但不僵硬：用清晰的逻辑组织内容，语言流畅易懂
- 有深度但不学究：可以用数据和研究支撑观点，但用普通人能懂的方式表达
- 避免：过度口语化（"哈哈""绝了""太那个了"）、随意省略、网络流行语滥用
- 允许：适度使用成语、设问句、排比句增强说服力
- 像一个有见识的朋友在认真分享观点，不是写学术论文"""

TONE_CASUAL = """## 语气要求（轻松-个人型）
- 像给朋友发消息分享好东西，自然、真诚、有温度
- 可以有个人化的表达："我最近发现…""说实话…""你别说…"
- 避免：写成广告文案、过度使用感叹号、虚假热情
- 允许：适度口语词、emoji（每篇1-3个）、个人经历引用
- 像朋友间的推荐，不端着、不忽悠"""

# 类型配置：(语气类型, 写作指导)
GENRE_CONFIGS = {
    # ======== 观点态度（正式-可读型）========
    "时事短评": ("formal", """【时事短评 · 写作指导】
- 基于联网搜索找到的热点新闻事件，一句话概括事件核心
- 给出1-2个分析角度（原因分析/影响分析/趋势判断），不是简单表态
- 论点要有依据，可以引用搜索到的数据或背景知识
- 结尾给出一个值得思考的方向，不强行下结论
- 自动打上事件相关的 #话题# 标签（1-2个）
- 参考格式：正文（2-4个短段落）+ #话题# 标签
- 字数：{word_count}"""),

    "国家政策": ("formal", """【国家政策 · 写作指导】
- 基于联网搜索找到的最新政策或民生新规，用一句话说清楚"什么变了"
- 重点讲"对普通人有什么影响"，列出2-3个具体影响点
- 不要念文件原文，用自己的话转译成通俗表达
- 政策内容要准确，不确定的细节不要编造
- 推荐话题：#政策解读# 或政策相关热门话题
- 字数：{word_count}"""),

    "历史感悟": ("formal", """【历史感悟 · 写作指导】
- 从联网搜索找到的历史事件或人物入手，确保史实准确
- 用生动的叙述还原历史场景，但要基于事实不戏说
- 自然引出对现代生活的启发，不强行拔高、不说教
- 启发要有共鸣感，让人读完后有所思考
- 推荐话题：#历史故事# #读史明智#
- 字数：{word_count}"""),

    # ======== 知识科普（正式-可读型）========
    "认知笔记": ("formal", """【认知笔记 · 写作指导】
- 介绍一个思维模型、心理学效应或认知偏误
- 先讲清楚概念（用一句话下定义），再用生活中的例子解释
- 说明这个认知工具可以在什么场景下使用
- 例子要通俗但不媚俗，让人觉得"确实是这样"
- 推荐话题：#思维模型# #认知升级#
- 字数：{word_count}"""),

    "医学健康科普": ("formal", """【医学健康科普 · 写作指导】
- 科普一个医学或健康知识（养生/疾病防治/用药/急救/心理）
- 信息要科学准确，优先引用权威医学机构的建议
- 用通俗语言解释专业概念，但不要牺牲准确性
- 给出具体可操作的建议，不说"多喝水""注意休息"等空话
- 不要制造健康焦虑，不要夸大疗效
- 推荐话题：#健康科普# #健康养生小百科#
- 字数：{word_count}"""),

    "生活常识科普": ("formal", """【生活常识科普 · 写作指导】
- 科普一个日常生活实用知识（饮食/家居/安全/礼仪/消费）
- 讲清楚"为什么"——不只是告诉读者怎么做，更要解释原理
- 可以指出常见误区，让读者有"原来我一直搞错了"的感觉
- 内容要实用、靠谱，不要传播未经证实的生活偏方
- 推荐话题：#生活常识# #涨知识#
- 字数：{word_count}"""),

    "人文社科科普": ("formal", """【人文社科科普 · 写作指导】
- 科普一个人文社科知识点（历史/考古/语言/法律/民俗/哲学）
- 内容要有趣有料，让人读完有谈资
- 可以联系当下的社会现象或热点，让知识点更贴近现实
- 避免过于学术化，不要堆砌专业术语
- 推荐话题：#人文科普# #社科知识#
- 字数：{word_count}"""),

    "冷知识": ("formal", """【冷知识 · 写作指导】
- 第一句用反常识的事实抓住眼球："你知道吗？其实……"
- 解释背后的科学原理或历史缘由，简短准确
- 联系日常生活，让读者感到"原来如此"
- 短小精悍，不展开成科普长文
- 推荐话题：#冷知识# #涨知识#
- 字数：{word_count}"""),

    # ======== 实用生活（轻松-个人型）========
    "财经小课": ("casual", """【财经小课 · 写作指导】
- 用通俗语言讲一个个人理财知识或经济概念
- 从身边的现象切入："最近发现一个有意思的事…"
- 给出实在的建议，帮读者避坑或省钱
- 不要推荐具体理财产品，不要制造财富焦虑
- 推荐话题：#理财知识# #财经小课#
- 字数：{word_count}"""),

    "科技新知": ("casual", """【科技新知 · 写作指导】
- 介绍一个新产品、AI 工具或数码技巧
- 基于真实体验或可靠评测来写，不要写软文
- 说清楚"这东西能干什么""适合什么人用""有什么坑"
- 避免过度吹捧，保持客观
- 推荐话题：#科技新知# #数码好物#
- 字数：{word_count}"""),

    "好物安利": ("casual", """【好物安利 · 写作指导】
- 推荐一本书/电影/播客/工具，真诚不浮夸
- 讲清楚"为什么推荐""适合什么人""我的个人感受"
- 有一两个具体的细节或片段，让推荐有说服力
- 不写商业软文口吻，像朋友间的真诚分享
- 推荐话题：#好书推荐# #好物分享# 或相关话题
- 字数：{word_count}"""),

    "美食札记": ("casual", """【美食札记 · 写作指导】
- 从一道具体的菜或一个食材切入，不要泛泛而谈
- 写做法要有个人实操经验（"关键一步是…""我试过…"）
- 写食材可以讲有趣来历或挑选技巧
- 语言生动，让人看了有食欲或想动手试试
- 推荐话题：#美食分享# #晒晒我的一日三餐#
- 字数：{word_count}"""),
}

WORD_COUNT_MAP = {
    "极短": "30-60字（约2-3句话，适合快速浏览）",
    "短": "60-120字（约4-6句话，一个紧凑的段落）",
    "中": "120-200字（约2-3个短段落，标准时间线帖子长度）",
    "长": "200-300字（约3-4个段落，适合有深度的内容）",
    "超长": "300-450字（约4-5个段落，适合深度解读类内容）",
}

SYSTEM_PROMPT_TEMPLATE = """{persona}

{tone}

{genre_guide}

## 输出格式
返回严格的 JSON（不要包含在```json```代码块中）：
{{"content": "帖子正文（含#话题#标签）", "source_title": "主要参考来源文章标题", "source_url": "主要参考来源文章URL"}}

## 工作流程
1. 首先联网搜索与类型相关的近期主流媒体文章（微信公众号、今日头条、网易新闻、搜狐新闻、腾讯新闻、微博等）
2. 阅读至多5篇相关文章，了解该话题的不同角度和报道方式
3. 基于这些文章的内容进行改写，用自己的话重新组织，转化为搜狐新闻时间线发布形式
4. 附上其中一篇参考文章的标题和URL作为来源引用
5. 不要直接复制原文，不要写"据XX媒体报道"等新闻腔"""


def build_system_prompt(genre: str, word_count: str) -> str:
    """组装三层 Prompt：人设 + 语气 + 类型指导"""
    tone_type, guide_template = GENRE_CONFIGS.get(
        genre, GENRE_CONFIGS["时事短评"]
    )
    word_range = WORD_COUNT_MAP.get(word_count, WORD_COUNT_MAP["中"])
    genre_guide = guide_template.format(word_count=word_range)
    tone = TONE_FORMAL if tone_type == "formal" else TONE_CASUAL

    return SYSTEM_PROMPT_TEMPLATE.format(
        persona=PERSONA,
        tone=tone,
        genre_guide=genre_guide,
    )


DOUBAO_BASE = "https://ark.cn-beijing.volces.com/api/v3"
DOUBAO_MODEL = "doubao-seed-1-8-251228"


def generate_post_text(genre: str, word_count: str, source_url: str) -> dict:
    """调用豆包 Chat Completions API 生成帖子（含联网搜索多源改写）"""
    client = OpenAI(
        api_key=os.environ["DOUBAO_API_KEY"],
        base_url=DOUBAO_BASE,
    )

    system_prompt = build_system_prompt(genre, word_count)

    if source_url:
        user_text = (
            f"请优先参考这个链接的内容：{source_url}\n"
            f"同时搜索其他相关的主流媒体文章（至多5篇），综合改写为搜狐新闻时间线帖子。"
        )
    else:
        user_text = (
            f"请搜索与「{genre}」相关的近期热门话题和主流媒体文章（至多5篇），"
            f"综合改写为搜狐新闻时间线帖子。"
        )

    response = client.chat.completions.create(
        model=DOUBAO_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        extra_body={"web_search": True},
        temperature=0.75,
        max_tokens=1200,
    )

    raw = response.choices[0].message.content.strip()

    # 解析 JSON（处理可能的 markdown 包裹）
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    return json.loads(raw)


# ============================================================
# 帖子存储
# ============================================================

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


# ============================================================
# 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="生成一篇搜狐时间线热帖")
    parser.add_argument("--genre", default="时事短评", help="内容类型")
    parser.add_argument("--word-count", default="中", help="字数档位")
    parser.add_argument("--source-url", default="", help="参考链接（可选）")
    args = parser.parse_args()

    result = generate_post_text(args.genre, args.word_count, args.source_url)

    post = {
        "id": make_post_id(),
        "content": result.get("content", ""),
        "source_title": result.get("source_title", ""),
        "source_url": result.get("source_url", ""),
        "genre": args.genre,
        "word_count": args.word_count,
        "created_at": datetime.now(CST).isoformat(),
    }

    append_post(post)
    print(f"Generated post: {post['id']}")
    print(f"  genre: {args.genre}")
    print(f"  word_count: {args.word_count}")
    print(f"  source_url: {args.source_url or 'none'}")
    print(f"  ref_source: {post['source_title']} ({post['source_url']})")
    print(f"  content: {post['content'][:80]}...")


if __name__ == "__main__":
    main()
