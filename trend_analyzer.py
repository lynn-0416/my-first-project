import time
import statistics



# 1. 時間 + 基本清理

def filter_recent_history(history, days=7):
    """
    只保留最近 N 天 + 基本資料清理
    """
    now = int(time.time())
    cutoff = now - days * 86400

    cleaned = []

    for h in history:
        price = h.get("pricePerUnit", 0)
        qty = h.get("quantity", 0)
        ts = h.get("timestamp", 0)

        # 過期資料
        if ts < cutoff:
            continue

        # 無效價格
        if price <= 0:
            continue

        # 太小交易
        if qty <= 2:
            continue

        cleaned.append(h)

    return cleaned



# 2. 趨勢分析

def analyze_trend(history):
    """
    回傳：
    上漲
    下跌
    平穩
    不穩
    資料不足
    """

    if not history or len(history) < 5:
        return "資料不足"

    # 按時間排序（保險）
    history = sorted(history, key=lambda x: x.get("timestamp", 0))

    prices = [h["pricePerUnit"] for h in history]

    
    # 切三段（前 / 中 / 後）
    
    split = max(1, len(prices) // 3)

    early = prices[:split]
    late = prices[-split:]

    early_avg = sum(early) / len(early)
    late_avg = sum(late) / len(late)

    change = (late_avg - early_avg) / early_avg


    
    # 波動率（市場穩定性）
    
    if len(prices) > 1:
        std = statistics.stdev(prices)
        avg = sum(prices) / len(prices)
        volatility = std / avg
    else:
        volatility = 0


    
    # 判斷邏輯
    

    # 高波動優先判斷
    if volatility > 0.25:
        return "不穩"

    # 穩定上升
    if change > 0.05:
        return "上漲"

    # 穩定下降
    if change < -0.05:
        return "下跌"

    # 平穩
    return "平穩"