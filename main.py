import json
import random
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

from crawler import (
    fetch_market_data,
    fetch_marketable_items,
    fetch_item_history
)
from analyzer import analyze_item
from config import BATCH_SIZE, MAX_WORKERS
from trend_analyzer import analyze_trend

print("開始分析市場資料...")

# =========================
# item data
# =========================
with open("xiv_items.json", "r", encoding="utf-8") as f:
    all_items = json.load(f)

name_map = {i["ID"]: i["Name_en"].strip() for i in all_items}

# =========================
# fetch items
# =========================
item_ids = fetch_marketable_items()
random.shuffle(item_ids)

results = []
index = 0

pbar = tqdm(total=len(item_ids), desc="分析中")

# =========================
# batch process
# =========================
def process_batch(batch):
    data = fetch_market_data(batch)
    res = []

    for item_id in batch:
        item_data = data.get("items", {}).get(str(item_id), {})
        name = name_map.get(item_id, "")

        result = analyze_item(item_id, item_data, name)
        if result:
            res.append(result)

    return res


# =========================
# main loop
# =========================
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

    while index < len(item_ids):

        batch = item_ids[index:index + BATCH_SIZE]
        index += BATCH_SIZE

        sub_batches = [batch[i:i+50] for i in range(0, len(batch), 50)]

        for batch_result in executor.map(process_batch, sub_batches):
            results.extend(batch_result)

        pbar.update(len(batch))

pbar.close()

# =========================
# safety check
# =========================
if not results:
    print("沒有資料")
    exit()

# =========================
# normalize score
# =========================
max_score = max(r["穩定金策評分"] for r in results)

for r in results:
    r["raw_score"] = r["穩定金策評分"]
    r["穩定金策評分"] = (r["穩定金策評分"] / max_score) * 100

# =========================
# sort
# =========================
results.sort(key=lambda x: x["穩定金策評分"], reverse=True)

# =========================
# TOP 20 with trend
# =========================
print("\n=== FF14 穩定金策 Top 20 ===\n")

history_cache = {}

for rank, r in enumerate(results[:20], start=1):

    item_id = r["物品ID"]
    name = r["名稱"]

    # =========================
    # fetch history (cached)
    # =========================
    if item_id in history_cache:
        history = history_cache[item_id]
    else:
        history = fetch_item_history(item_id)
        history_cache[item_id] = history

    # =========================
    # trend analysis
    # =========================
    if history and len(history) >= 5:
        trend = analyze_trend(history)
        history_count = len(history)
    else:
        trend = "資料不足"
        history_count = len(history) if history else 0

    # =========================
    # output
    # =========================
    print(f"{rank}. {name} ({item_id})")
    print(f"評分: {r['穩定金策評分']:.4f}")
    print(f"售價: {r['售價']:.2f}")
    print(f"價格趨勢：{trend}")
    print(f"成交筆數：{history_count}")
    print(f"🔗 https://universalis.app/market/{item_id}\n")