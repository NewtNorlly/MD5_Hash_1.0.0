"""
MD5 Cracker - 通过彩虹表数据库查找MD5对应的明文密码
用法:
    python crack_md5.py <md5hash>
    python crack_md5.py  (交互模式)
"""
import sqlite3
import sys
import hashlib
import time
from pathlib import Path

DB_PATH = "md5_rainbow.db"

def lookup(hash_val: str) -> str | None:
    hash_val = hash_val.strip().lower()
    if len(hash_val) != 32:
        print("[-] 无效的MD5哈希（应为32位十六进制字符串）")
        return None

    if not Path(DB_PATH).exists():
        print(f"[-] 数据库 {DB_PATH} 不存在，请先运行 build_db.py")
        return None

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA query_only=1")
    t0 = time.time()
    row = conn.execute(
        "SELECT password FROM rainbow WHERE hash = ?", (hash_val,)
    ).fetchone()
    conn.close()
    elapsed = (time.time() - t0) * 1000

    if row:
        print(f"[+] 破解成功！({elapsed:.2f}ms)")
        print(f"    MD5   : {hash_val}")
        print(f"    密码  : {row[0]}")
        return row[0]
    else:
        print(f"[-] 未找到（{elapsed:.2f}ms）- 该密码不在彩虹表中")
        return None

def verify(password: str, hash_val: str) -> bool:
    return hashlib.md5(password.encode()).hexdigest() == hash_val.lower()

def db_stats():
    if not Path(DB_PATH).exists():
        print(f"[-] 数据库不存在")
        return
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM rainbow").fetchone()[0]
    conn.close()
    size_mb = Path(DB_PATH).stat().st_size / 1024 / 1024
    print(f"[*] 数据库统计: {count:,} 条记录，{size_mb:.1f} MB")

if __name__ == "__main__":
    db_stats()
    print()

    if len(sys.argv) > 1:
        # 命令行模式
        for h in sys.argv[1:]:
            lookup(h)
    else:
        # 交互模式
        print("输入MD5哈希值进行查找（输入 q 退出）")
        while True:
            h = input("\nMD5> ").strip()
            if h.lower() in ('q', 'quit', 'exit'):
                break
            if h:
                lookup(h)
