import math
import statistics
import time

from config import (
    MIN_PRICE,
    MAX_PRICE,
    LAST_HISTORY_LIMIT,
    WEIGHT_LIQUIDITY,
    WEIGHT_STABILITY,
    WEIGHT_ANTI_SPIKE,
    WEIGHT_PRICE
)

# =========================
# time filter
# =========================
def filter_recent(history, days=7):
    now = int(time.time())
    cutoff = now - days * 86400

    cleaned = []

    for h in history:
        ts = h.get("timestamp", 0)

        if ts < cutoff:
            continue

        cleaned.append(h)

    return cleaned


# =========================
# basic clean
# =========================
def clean_history(history):
    cleaned = []

    for h in history:
        price = h.get("pricePerUnit", 0)
        qty = h.get("quantity", 0)

        if qty <= 2:
            continue
        if price <= 0 or price > MAX_PRICE:
            continue

        cleaned.append(h)

    return cleaned


# =========================
# outlier removal
# =========================
def remove_outliers_percentile(prices):
    if len(prices) < 8:
        return prices

    sorted_p = sorted(prices)
    p10 = sorted_p[int(len(sorted_p) * 0.1)]
    p90 = sorted_p[int(len(sorted_p) * 0.9)]

    return [p for p in prices if p10 <= p <= p90]


# =========================
# liquidity model
# =========================
def compute_liquidity(trade_count, total_qty):
    base = math.log(trade_count + 1) * math.log(total_qty + 1)

    if 5 <= trade_count <= 20:
        base *= 1.15
    elif 20 < trade_count <= 40:
        base *= 1.05
    elif trade_count < 3:
        base *= 0.6
    elif trade_count < 8:
        base *= 0.9

    if trade_count > 50:
        base *= 0.9

    return base


# =========================
# main scoring function
# =========================
def analyze_item(item_id, item_data, name):

    # 無掛單直接跳過
    if not item_data.get("listings"):
        return None

    # =========================
    # history processing
    # =========================
    recent = item_data.get("recentHistory", [])

    # 只取最近7天（關鍵修正）
    recent = filter_recent(recent, days=7)

    # 基本清理
    recent = clean_history(recent)

    # 限制長度
    recent = recent[:LAST_HISTORY_LIMIT]

    # =========================
    # HQ fallback
    # =========================
    hq_recent = [i for i in recent if i.get("hq")]

    if not hq_recent:
        hq_recent = recent

    if len(hq_recent) < 3:
        return None

    # =========================
    # price processing
    # =========================
    prices = [i["pricePerUnit"] for i in hq_recent]
    prices = remove_outliers_percentile(prices)

    if len(prices) < 3:
        return None

    avg_price = sum(prices) / len(prices)

    if avg_price < MIN_PRICE:
        return None

    # =========================
    # item penalty
    # =========================
    penalty = 0.0

    if any(k in name for k in ["Crystal", "Shard", "Cluster"]):
        penalty = 0.15
    elif any(k in name for k in ["Ore", "Log", "Skin", "Fiber"]):
        penalty = 0.25

    # =========================
    # metrics
    # =========================
    trade_count = len(hq_recent)
    total_qty = sum(i["quantity"] for i in hq_recent)

    liquidity = compute_liquidity(trade_count, total_qty)

    price_std = statistics.stdev(prices) if len(prices) > 1 else 999999
    stability = 1 / (price_std + 1)

    spike_ratio = max(prices) / (min(prices) + 1)
    anti_spike = 1 / (spike_ratio + 1)

    # =========================
    # final score
    # =========================
    score = (
        liquidity * WEIGHT_LIQUIDITY +
        stability * WEIGHT_STABILITY +
        anti_spike * WEIGHT_ANTI_SPIKE +
        math.log(avg_price + 1) * WEIGHT_PRICE
    )

    score *= (1 - penalty)

    # =========================
    # output
    # =========================
    return {
        "物品ID": item_id,
        "名稱": name,
        "穩定金策評分": score,
        "售價": avg_price
    }