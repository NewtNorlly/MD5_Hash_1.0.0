"""
MD5 Rainbow Table Builder - 精简示范版
只收录最常见的有规律密码，快速生成小型数据库
"""
import hashlib
import sqlite3
import itertools
import string
import time
from pathlib import Path

DB_PATH = "md5_rainbow.db"

def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rainbow (
            hash TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    conn.commit()

def generate_passwords():
    passwords = []

    # 1. 纯数字 4~6 位（10000 + 100000 + 1000000 条，主力）
    for length in range(4, 7):
        for combo in itertools.product(string.digits, repeat=length):
            passwords.append(''.join(combo))

    # 2. 常见弱密码词汇及变体
    base_words = [
        "password", "passwd", "pass", "admin", "root", "user", "login",
        "welcome", "hello", "world", "test", "guest", "master", "super",
        "qwerty", "asdf", "abc", "iloveyou", "monkey", "dragon", "letmein",
        "111111", "222222", "666666", "888888", "000000", "123123", "654321",
        "abc123", "abcdef", "aaaaaa", "password1", "admin123", "root123",
        "china", "beijing", "shanghai",
    ]
    suffixes = ["", "1", "12", "123", "1234", "12345", "0", "!", "2024", "2025"]
    for word in base_words:
        for suf in suffixes:
            passwords.append(word + suf)
            if suf:
                passwords.append(word.capitalize() + suf)

    # 3. 年份 1970~2025
    for year in range(1970, 2026):
        for suf in ["", "0", "123", "!"]:
            passwords.append(str(year) + suf)

    # 4. 生日格式 YYYYMMDD（常见年份 + 全月日）
    for year in range(1980, 2005):
        for month in range(1, 13):
            for day in range(1, 29):
                passwords.append(f"{year}{month:02d}{day:02d}")

    # 5. 纯小写字母 3~4 位
    for length in range(3, 5):
        for combo in itertools.product(string.ascii_lowercase, repeat=length):
            passwords.append(''.join(combo))

    # 6. 常见中国姓名拼音 + 数字
    names = ["zhang","wang","li","zhao","liu","chen","yang","huang",
             "zhou","wu","xu","sun","ma","zhu","hu","guo","lin","he"]
    for name in names:
        for suf in ["", "123", "1234", "12345", "2024", "2025", "0", "!"]:
            passwords.append(name + suf)

    return passwords

def build():
    print("[*] 初始化数据库...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=100000")
    init_db(conn)

    print("[*] 生成密码并写入...")
    t0 = time.time()
    passwords = generate_passwords()
    print(f"[*] 候选密码数量: {len(passwords):,}")

    batch, total = [], 0
    for pwd in passwords:
        batch.append((md5(pwd), pwd))
        if len(batch) >= 50000:
            conn.executemany("INSERT OR IGNORE INTO rainbow VALUES (?,?)", batch)
            conn.commit()
            total += len(batch)
            batch = []
            print(f"    已写入 {total:,} 条...", end='\r')
    if batch:
        conn.executemany("INSERT OR IGNORE INTO rainbow VALUES (?,?)", batch)
        conn.commit()
        total += len(batch)

    print(f"\n[*] 建立索引...")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON rainbow(hash)")
    conn.commit()
    conn.close()

    size_mb = Path(DB_PATH).stat().st_size / 1024 / 1024
    print(f"[+] 完成！{total:,} 条，耗时 {time.time()-t0:.1f}s，数据库 {size_mb:.1f} MB")

if __name__ == "__main__":
    build()
