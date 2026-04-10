import os
import sqlite3
import time
from pathlib import Path
from flask import Flask, request, jsonify, render_template
import anthropic

app = Flask(__name__)
DB_PATH = Path(__file__).parent / "md5_rainbow.db"

# API Key 优先从环境变量读取，其次用启动时传入的值
AI_CLIENT = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY", "sk-66cabcc54db44e5e98245c5f214532c5")
)


def query_db(hash_val: str):
    conn = sqlite3.connect(DB_PATH)
    t0 = time.time()
    row = conn.execute(
        "SELECT password FROM rainbow WHERE hash = ?", (hash_val.lower(),)
    ).fetchone()
    conn.close()
    return row[0] if row else None, (time.time() - t0) * 1000


def query_ai(hash_val: str):
    """让 AI 尝试推测 MD5 对应的常见密码"""
    t0 = time.time()
    try:
        resp = AI_CLIENT.messages.create(
            model="claude-haiku-4-5",
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": (
                    f"这是一个MD5哈希值：{hash_val}\n"
                    "请判断它是否可能对应某个常见的弱密码（如纯数字、常见单词、键盘模式等）。\n"
                    "如果你能推测出明文，只回答明文密码本身，不要任何解释。\n"
                    "如果无法推测，只回答：无法确定"
                )
            }]
        )
        ms = (time.time() - t0) * 1000
        answer = resp.content[0].text.strip()
        if answer == "无法确定" or len(answer) > 64:
            return None, ms
        return answer, ms
    except Exception as e:
        return None, (time.time() - t0) * 1000


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/crack")
def crack():
    data = request.get_json(silent=True) or {}
    h = (data.get("hash") or "").strip().lower()
    if len(h) != 32 or not all(c in "0123456789abcdef" for c in h):
        return jsonify({"error": "无效的MD5（需32位十六进制）"}), 400

    # 第一步：查彩虹表
    password, ms = query_db(h)
    if password:
        return jsonify({"found": True, "source": "database", "password": password, "time_ms": round(ms, 2)})

    # 第二步：AI 兜底
    ai_password, ai_ms = query_ai(h)
    if ai_password:
        return jsonify({"found": True, "source": "ai", "password": ai_password, "time_ms": round(ms + ai_ms, 2)})

    return jsonify({"found": False, "time_ms": round(ms + ai_ms, 2)})


@app.get("/stats")
def stats():
    if not DB_PATH.exists():
        return jsonify({"error": "数据库不存在"}), 404
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM rainbow").fetchone()[0]
    conn.close()
    size_mb = round(DB_PATH.stat().st_size / 1024 / 1024, 1)
    return jsonify({"count": count, "size_mb": size_mb})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
