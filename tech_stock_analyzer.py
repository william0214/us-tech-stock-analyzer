#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股科技股分析腳本
分析 AI 產業、區塊鏈、台股連動股的漲跌情況
生成包含外資目標價與台股推薦建議的專業分析報告
透過 Gmail 發送至 william0214@gmail.com
"""

import yfinance as yf
import pandas as pd
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import pytz
import traceback
import time

# ============================================================
# 設定
# ============================================================
GMAIL_USER = "william0214@gmail.com"
GMAIL_APP_PASSWORD = "mbvg fhbx axrp hwua"
RECIPIENT = "william0214@gmail.com"

# 股票清單
STOCKS = {
    "AI產業龍頭": {
        "NVDA": "輝達",
        "MSFT": "微軟",
        "GOOGL": "谷歌",
        "META": "Meta",
        "TSLA": "特斯拉",
        "AMD": "超微",
        "AVGO": "博通",
        "ORCL": "甲骨文",
        "CRM": "Salesforce",
        "PLTR": "Palantir",
    },
    "區塊鏈相關": {
        "COIN": "Coinbase",
        "MSTR": "MicroStrategy",
        "RIOT": "Riot Platforms",
        "MARA": "Marathon Digital",
        "PYPL": "PayPal",
    },
    "台股連動核心": {
        "AAPL": "蘋果",
        "QCOM": "高通",
        "INTC": "英特爾",
        "AMZN": "亞馬遜",
    },
}

# 外資目標價資料庫
FOREIGN_TARGETS = {
    "2330": {"name": "台積電", "target": "2,400元", "source": "Aletheia Capital"},
    "2317": {"name": "鴻海", "target": "400元", "source": "美系外資"},
    "2382": {"name": "廣達", "target": "400元", "source": "野村/瑞銀/群益"},
    "3711": {"name": "日月光", "target": "340元", "source": "美系外資"},
    "2449": {"name": "京元電", "target": "330元", "source": "美系外資"},
    "3231": {"name": "緯創", "target": "215元", "source": "多家法人"},
    "6223": {"name": "旺矽", "target": "2,800元", "source": "美系外資"},
}

# 台股推薦邏輯對應
TW_STOCK_MAPPING = {
    "NVDA": [
        {"code": "2330", "name": "台積電", "reason": "NVDA AI 晶片主要代工廠，直接受益"},
        {"code": "2382", "name": "廣達", "reason": "AI 伺服器組裝龍頭，NVDA 供應鏈"},
        {"code": "6223", "name": "旺矽", "reason": "NVDA 晶圓測試關鍵供應商"},
    ],
    "MSFT": [
        {"code": "2330", "name": "台積電", "reason": "Azure AI 晶片代工"},
        {"code": "2382", "name": "廣達", "reason": "Azure 伺服器供應商"},
    ],
    "GOOGL": [
        {"code": "2330", "name": "台積電", "reason": "Google TPU 晶片代工"},
        {"code": "3231", "name": "緯創", "reason": "Google 伺服器供應鏈"},
    ],
    "META": [
        {"code": "2330", "name": "台積電", "reason": "Meta AI 晶片代工"},
        {"code": "2382", "name": "廣達", "reason": "Meta 資料中心伺服器"},
    ],
    "TSLA": [
        {"code": "2317", "name": "鴻海", "reason": "電動車供應鏈合作"},
        {"code": "3711", "name": "日月光", "reason": "車用晶片封測"},
    ],
    "AMD": [
        {"code": "2330", "name": "台積電", "reason": "AMD 晶片主要代工廠"},
        {"code": "2449", "name": "京元電", "reason": "AMD 晶片測試供應商"},
    ],
    "AVGO": [
        {"code": "2330", "name": "台積電", "reason": "AVGO 網路晶片代工"},
        {"code": "3711", "name": "日月光", "reason": "AVGO 晶片封測"},
    ],
    "AAPL": [
        {"code": "2317", "name": "鴻海", "reason": "iPhone 最大組裝廠"},
        {"code": "2330", "name": "台積電", "reason": "Apple Silicon 獨家代工"},
        {"code": "3231", "name": "緯創", "reason": "Apple 供應鏈組裝"},
    ],
    "QCOM": [
        {"code": "2330", "name": "台積電", "reason": "高通 Snapdragon 代工"},
        {"code": "2449", "name": "京元電", "reason": "高通晶片測試"},
    ],
    "INTC": [
        {"code": "2330", "name": "台積電", "reason": "Intel 先進製程代工"},
        {"code": "3711", "name": "日月光", "reason": "Intel 晶片封測"},
    ],
    "AMZN": [
        {"code": "2330", "name": "台積電", "reason": "AWS Graviton 晶片代工"},
        {"code": "2382", "name": "廣達", "reason": "AWS 伺服器供應商"},
    ],
    "COIN": [
        {"code": "2330", "name": "台積電", "reason": "加密貨幣挖礦晶片代工"},
    ],
    "MSTR": [
        {"code": "2330", "name": "台積電", "reason": "比特幣概念，算力晶片需求"},
    ],
    "RIOT": [
        {"code": "2330", "name": "台積電", "reason": "挖礦晶片代工受益"},
    ],
    "MARA": [
        {"code": "2330", "name": "台積電", "reason": "挖礦晶片代工受益"},
    ],
    "PLTR": [
        {"code": "2382", "name": "廣達", "reason": "AI 資料分析伺服器需求"},
    ],
    "ORCL": [
        {"code": "2382", "name": "廣達", "reason": "Oracle 雲端伺服器供應"},
    ],
    "CRM": [
        {"code": "2382", "name": "廣達", "reason": "Salesforce AI 伺服器"},
    ],
    "PYPL": [
        {"code": "2317", "name": "鴻海", "reason": "數位支付基礎設施"},
    ],
}

# 小型活躍股推薦（依美股整體表現）
SMALL_CAP_STOCKS = [
    {"code": "6669", "name": "緯穎", "reason": "AI 伺服器小型龍頭，彈性大"},
    {"code": "3034", "name": "聯詠", "reason": "顯示驅動 IC，跟漲動能強"},
    {"code": "5274", "name": "信驊", "reason": "BMC 晶片龍頭，AI 伺服器管理"},
    {"code": "6533", "name": "晶心科", "reason": "RISC-V 架構，AI 邊緣運算"},
    {"code": "3443", "name": "創意", "reason": "台積電轉投資，IP 設計受益"},
]


def get_stock_data(ticker: str) -> dict | None:
    """從 Yahoo Finance 獲取股票數據"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist.empty or len(hist) < 2:
            print(f"  [警告] {ticker}: 數據不足")
            return None

        today = hist.iloc[-1]
        prev = hist.iloc[-2]

        current_price = today["Close"]
        prev_close = prev["Close"]
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100

        # 成交量比（今日 vs 5日均量）
        avg_volume = hist["Volume"].mean()
        volume_ratio = today["Volume"] / avg_volume if avg_volume > 0 else 1.0

        return {
            "ticker": ticker,
            "current_price": current_price,
            "prev_close": prev_close,
            "change": change,
            "change_pct": change_pct,
            "volume": today["Volume"],
            "avg_volume": avg_volume,
            "volume_ratio": volume_ratio,
            "open": today["Open"],
            "high": today["High"],
            "low": today["Low"],
        }
    except Exception as e:
        print(f"  [錯誤] {ticker}: {e}")
        return None


def format_change(pct: float) -> str:
    """格式化漲跌幅，帶顏色標記"""
    if pct > 0:
        return f'<span style="color:#00c851;font-weight:bold;">▲ {pct:.2f}%</span>'
    elif pct < 0:
        return f'<span style="color:#ff4444;font-weight:bold;">▼ {abs(pct):.2f}%</span>'
    else:
        return f'<span style="color:#aaa;">— {pct:.2f}%</span>'


def format_price(price: float) -> str:
    return f"${price:.2f}"


def generate_tw_recommendations(all_data: dict) -> list:
    """根據美股表現生成台股推薦"""
    recommendations = {}

    for ticker, data in all_data.items():
        if data is None:
            continue
        if data["change_pct"] >= 1.5:  # 漲幅 >= 1.5% 才推薦
            related = TW_STOCK_MAPPING.get(ticker, [])
            for stock in related:
                code = stock["code"]
                if code not in recommendations:
                    recommendations[code] = {
                        "code": code,
                        "name": stock["name"],
                        "reasons": [],
                        "triggers": [],
                        "max_trigger_pct": 0,
                        "has_foreign_target": code in FOREIGN_TARGETS,
                    }
                recommendations[code]["reasons"].append(stock["reason"])
                recommendations[code]["triggers"].append(
                    f"{ticker}({data['change_pct']:+.2f}%)"
                )
                if data["change_pct"] > recommendations[code]["max_trigger_pct"]:
                    recommendations[code]["max_trigger_pct"] = data["change_pct"]

    # 排序：有外資目標價優先，再依觸發漲幅排序
    result = sorted(
        recommendations.values(),
        key=lambda x: (x["has_foreign_target"], x["max_trigger_pct"]),
        reverse=True,
    )
    return result


def generate_html_report(all_data: dict, date_str: str) -> str:
    """生成 HTML 格式的分析報告"""

    # 整理所有有效數據
    valid_data = {k: v for k, v in all_data.items() if v is not None}
    all_stocks_list = list(valid_data.values())

    # 漲跌幅排名
    sorted_by_change = sorted(all_stocks_list, key=lambda x: x["change_pct"], reverse=True)
    top5_gainers = sorted_by_change[:5]
    top5_losers = sorted_by_change[-5:][::-1]

    # 成交量異常（> 1.5 倍平均）
    volume_anomalies = [s for s in all_stocks_list if s["volume_ratio"] > 1.5]
    volume_anomalies.sort(key=lambda x: x["volume_ratio"], reverse=True)

    # 台股推薦
    tw_recs = generate_tw_recommendations(valid_data)

    # 計算整體市場情緒
    gainers_count = sum(1 for s in all_stocks_list if s["change_pct"] > 0)
    losers_count = sum(1 for s in all_stocks_list if s["change_pct"] < 0)
    avg_change = sum(s["change_pct"] for s in all_stocks_list) / len(all_stocks_list) if all_stocks_list else 0

    if avg_change > 1:
        market_sentiment = "🚀 強勢上漲"
        sentiment_color = "#00c851"
    elif avg_change > 0:
        market_sentiment = "📈 溫和上漲"
        sentiment_color = "#00c851"
    elif avg_change > -1:
        market_sentiment = "📉 小幅回落"
        sentiment_color = "#ff9800"
    else:
        market_sentiment = "⚠️ 明顯下跌"
        sentiment_color = "#ff4444"

    # ---- 建立 HTML ----
    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>美股科技股分析報告 {date_str}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Microsoft JhengHei', sans-serif;
    background: #0d1117;
    color: #e6edf3;
    line-height: 1.6;
  }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
  .header {{
    background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 30px;
    margin-bottom: 24px;
    text-align: center;
  }}
  .header h1 {{ font-size: 26px; color: #58a6ff; margin-bottom: 8px; }}
  .header .subtitle {{ color: #8b949e; font-size: 14px; }}
  .market-summary {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 24px;
  }}
  .summary-card {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
  }}
  .summary-card .label {{ color: #8b949e; font-size: 12px; margin-bottom: 8px; }}
  .summary-card .value {{ font-size: 22px; font-weight: bold; }}
  .section {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
  }}
  .section h2 {{
    font-size: 16px;
    color: #58a6ff;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #30363d;
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{
    background: #21262d;
    color: #8b949e;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #21262d; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #1c2128; }}
  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: bold;
  }}
  .badge-red {{ background: #ff444420; color: #ff4444; border: 1px solid #ff444440; }}
  .badge-green {{ background: #00c85120; color: #00c851; border: 1px solid #00c85140; }}
  .badge-blue {{ background: #58a6ff20; color: #58a6ff; border: 1px solid #58a6ff40; }}
  .badge-orange {{ background: #ff980020; color: #ff9800; border: 1px solid #ff980040; }}
  .badge-gold {{ background: #ffd70020; color: #ffd700; border: 1px solid #ffd70040; }}
  .ticker {{ font-family: monospace; font-weight: bold; color: #e6edf3; }}
  .tw-code {{ font-family: monospace; color: #58a6ff; font-weight: bold; }}
  .reason-text {{ color: #8b949e; font-size: 12px; }}
  .trigger-tag {{
    display: inline-block;
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 11px;
    margin: 1px;
    color: #8b949e;
  }}
  .footer {{
    text-align: center;
    color: #484f58;
    font-size: 12px;
    margin-top: 24px;
    padding: 16px;
  }}
  .volume-bar {{
    display: inline-block;
    background: #58a6ff40;
    height: 6px;
    border-radius: 3px;
    vertical-align: middle;
    margin-left: 6px;
  }}
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="header">
    <h1>📊 美股科技股分析報告</h1>
    <div class="subtitle">分析日期：{date_str} ｜ 資料來源：Yahoo Finance ｜ 涵蓋 {len(valid_data)} 支股票</div>
  </div>

  <!-- Market Summary -->
  <div class="market-summary">
    <div class="summary-card">
      <div class="label">市場情緒</div>
      <div class="value" style="color:{sentiment_color}; font-size:18px;">{market_sentiment}</div>
    </div>
    <div class="summary-card">
      <div class="label">上漲 / 下跌</div>
      <div class="value">
        <span style="color:#00c851">{gainers_count}</span>
        <span style="color:#484f58"> / </span>
        <span style="color:#ff4444">{losers_count}</span>
      </div>
    </div>
    <div class="summary-card">
      <div class="label">平均漲跌幅</div>
      <div class="value" style="color:{'#00c851' if avg_change >= 0 else '#ff4444'}">
        {'▲' if avg_change >= 0 else '▼'} {abs(avg_change):.2f}%
      </div>
    </div>
  </div>
"""

    # ---- 漲幅前五名 ----
    html += """
  <div class="section">
    <h2>🚀 漲幅前五名</h2>
    <table>
      <thead>
        <tr>
          <th>代號</th>
          <th>名稱</th>
          <th>現價</th>
          <th>漲跌幅</th>
          <th>成交量比</th>
        </tr>
      </thead>
      <tbody>
"""
    for s in top5_gainers:
        ticker = s["ticker"]
        name = ""
        for sector_stocks in STOCKS.values():
            if ticker in sector_stocks:
                name = sector_stocks[ticker]
                break
        vol_ratio_str = f"{s['volume_ratio']:.1f}x"
        vol_badge = '<span class="badge badge-orange">量增</span>' if s["volume_ratio"] > 1.5 else ""
        html += f"""
        <tr>
          <td><span class="ticker">{ticker}</span></td>
          <td>{name}</td>
          <td>{format_price(s['current_price'])}</td>
          <td>{format_change(s['change_pct'])}</td>
          <td>{vol_ratio_str} {vol_badge}</td>
        </tr>"""
    html += """
      </tbody>
    </table>
  </div>
"""

    # ---- 跌幅前五名 ----
    html += """
  <div class="section">
    <h2>📉 跌幅前五名</h2>
    <table>
      <thead>
        <tr>
          <th>代號</th>
          <th>名稱</th>
          <th>現價</th>
          <th>漲跌幅</th>
          <th>成交量比</th>
        </tr>
      </thead>
      <tbody>
"""
    for s in top5_losers:
        ticker = s["ticker"]
        name = ""
        for sector_stocks in STOCKS.values():
            if ticker in sector_stocks:
                name = sector_stocks[ticker]
                break
        vol_ratio_str = f"{s['volume_ratio']:.1f}x"
        vol_badge = '<span class="badge badge-orange">量增</span>' if s["volume_ratio"] > 1.5 else ""
        html += f"""
        <tr>
          <td><span class="ticker">{ticker}</span></td>
          <td>{name}</td>
          <td>{format_price(s['current_price'])}</td>
          <td>{format_change(s['change_pct'])}</td>
          <td>{vol_ratio_str} {vol_badge}</td>
        </tr>"""
    html += """
      </tbody>
    </table>
  </div>
"""

    # ---- 成交量異常 ----
    if volume_anomalies:
        html += """
  <div class="section">
    <h2>⚡ 成交量異常（>1.5倍平均）</h2>
    <table>
      <thead>
        <tr>
          <th>代號</th>
          <th>名稱</th>
          <th>現價</th>
          <th>漲跌幅</th>
          <th>成交量比</th>
          <th>今日成交量</th>
        </tr>
      </thead>
      <tbody>
"""
        for s in volume_anomalies:
            ticker = s["ticker"]
            name = ""
            for sector_stocks in STOCKS.values():
                if ticker in sector_stocks:
                    name = sector_stocks[ticker]
                    break
            vol_m = s["volume"] / 1_000_000
            html += f"""
        <tr>
          <td><span class="ticker">{ticker}</span></td>
          <td>{name}</td>
          <td>{format_price(s['current_price'])}</td>
          <td>{format_change(s['change_pct'])}</td>
          <td><span class="badge badge-orange">{s['volume_ratio']:.1f}x</span></td>
          <td>{vol_m:.1f}M</td>
        </tr>"""
        html += """
      </tbody>
    </table>
  </div>
"""
    else:
        html += """
  <div class="section">
    <h2>⚡ 成交量異常</h2>
    <p style="color:#8b949e; text-align:center; padding:20px;">今日無成交量異常股票（均低於 1.5 倍平均量）</p>
  </div>
"""

    # ---- 依產業分類完整列表 ----
    for sector, sector_stocks in STOCKS.items():
        html += f"""
  <div class="section">
    <h2>📋 {sector}</h2>
    <table>
      <thead>
        <tr>
          <th>代號</th>
          <th>名稱</th>
          <th>現價</th>
          <th>前收</th>
          <th>漲跌幅</th>
          <th>最高</th>
          <th>最低</th>
          <th>成交量比</th>
        </tr>
      </thead>
      <tbody>
"""
        for ticker, name in sector_stocks.items():
            s = valid_data.get(ticker)
            if s is None:
                html += f"""
        <tr>
          <td><span class="ticker">{ticker}</span></td>
          <td>{name}</td>
          <td colspan="6" style="color:#484f58; text-align:center;">數據獲取失敗</td>
        </tr>"""
            else:
                vol_badge = '<span class="badge badge-orange">量增</span>' if s["volume_ratio"] > 1.5 else ""
                html += f"""
        <tr>
          <td><span class="ticker">{ticker}</span></td>
          <td>{name}</td>
          <td>{format_price(s['current_price'])}</td>
          <td>{format_price(s['prev_close'])}</td>
          <td>{format_change(s['change_pct'])}</td>
          <td>{format_price(s['high'])}</td>
          <td>{format_price(s['low'])}</td>
          <td>{s['volume_ratio']:.1f}x {vol_badge}</td>
        </tr>"""
        html += """
      </tbody>
    </table>
  </div>
"""

    # ---- 台股推薦 ----
    html += """
  <div class="section">
    <h2>🇹🇼 產業分析師台股投資建議</h2>
    <p style="color:#8b949e; font-size:13px; margin-bottom:16px;">
      依美股表現自動生成台股連動推薦，標註外資調升目標價（金色徽章）
    </p>
"""
    if tw_recs:
        html += """
    <table>
      <thead>
        <tr>
          <th>股票代號</th>
          <th>公司名稱</th>
          <th>外資目標價</th>
          <th>觸發美股</th>
          <th>推薦理由</th>
        </tr>
      </thead>
      <tbody>
"""
        for rec in tw_recs[:10]:  # 最多顯示 10 檔
            code = rec["code"]
            name = rec["name"]
            triggers_html = " ".join(
                [f'<span class="trigger-tag">{t}</span>' for t in rec["triggers"]]
            )
            reasons = "；".join(set(rec["reasons"]))

            if rec["has_foreign_target"]:
                ft = FOREIGN_TARGETS[code]
                target_html = f'<span class="badge badge-gold">🎯 {ft["target"]}</span><br><span style="font-size:11px;color:#8b949e;">{ft["source"]}</span>'
            else:
                target_html = '<span style="color:#484f58;">—</span>'

            html += f"""
        <tr>
          <td><span class="tw-code">{code}</span></td>
          <td><strong>{name}</strong></td>
          <td>{target_html}</td>
          <td>{triggers_html}</td>
          <td><span class="reason-text">{reasons}</span></td>
        </tr>"""
        html += """
      </tbody>
    </table>
"""
    else:
        html += """
    <p style="color:#8b949e; text-align:center; padding:20px;">
      今日美股漲幅不足，暫無強力台股推薦（需美股漲幅 ≥1.5% 才觸發）
    </p>
"""

    # ---- 小型活躍股 ----
    html += """
    <div style="margin-top:20px; padding:16px; background:#1c2128; border-radius:8px; border:1px solid #30363d;">
      <div style="color:#ffd700; font-weight:bold; margin-bottom:12px;">⚡ 小型活躍股觀察名單</div>
      <table>
        <thead>
          <tr>
            <th>代號</th>
            <th>名稱</th>
            <th>推薦理由</th>
          </tr>
        </thead>
        <tbody>
"""
    for s in SMALL_CAP_STOCKS:
        html += f"""
          <tr>
            <td><span class="tw-code">{s['code']}</span></td>
            <td><strong>{s['name']}</strong></td>
            <td><span class="reason-text">{s['reason']}</span></td>
          </tr>"""
    html += """
        </tbody>
      </table>
    </div>
  </div>
"""

    # ---- 外資目標價資料庫 ----
    html += """
  <div class="section">
    <h2>🎯 外資目標價資料庫</h2>
    <table>
      <thead>
        <tr>
          <th>股票代號</th>
          <th>公司名稱</th>
          <th>外資目標價</th>
          <th>外資機構</th>
        </tr>
      </thead>
      <tbody>
"""
    for code, info in FOREIGN_TARGETS.items():
        html += f"""
        <tr>
          <td><span class="tw-code">{code}</span></td>
          <td><strong>{info['name']}</strong></td>
          <td><span class="badge badge-gold">🎯 {info['target']}</span></td>
          <td><span class="badge badge-blue">{info['source']}</span></td>
        </tr>"""
    html += """
      </tbody>
    </table>
  </div>
"""

    # ---- 進場時機與風險提示 ----
    html += f"""
  <div class="section">
    <h2>⏰ 進場時機與風險提示</h2>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
      <div style="background:#1c2128; padding:16px; border-radius:8px; border-left:3px solid #00c851;">
        <div style="color:#00c851; font-weight:bold; margin-bottom:8px;">📈 建議進場時機</div>
        <ul style="color:#8b949e; font-size:13px; padding-left:16px; line-height:2;">
          <li>開盤後 09:15–09:30 觀察量能確認</li>
          <li>午盤 13:00–13:20 第二波進場機會</li>
          <li>尾盤前 30 分鐘佈局隔日強勢股</li>
          <li>成交量 >1.5x 平均量時優先考慮</li>
        </ul>
      </div>
      <div style="background:#1c2128; padding:16px; border-radius:8px; border-left:3px solid #ff4444;">
        <div style="color:#ff4444; font-weight:bold; margin-bottom:8px;">⚠️ 風險提示</div>
        <ul style="color:#8b949e; font-size:13px; padding-left:16px; line-height:2;">
          <li>本報告僅供參考，不構成投資建議</li>
          <li>台股與美股存在時差，隔日開盤有缺口風險</li>
          <li>已漲停股票不在推薦範圍內</li>
          <li>請設定停損點，控制單筆風險在 2% 以內</li>
        </ul>
      </div>
    </div>
  </div>
"""

    # ---- Footer ----
    html += f"""
  <div class="footer">
    <p>📊 美股科技股分析報告 ｜ 生成時間：{datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')} (台北時間)</p>
    <p>資料來源：Yahoo Finance ｜ 外資目標價資料庫 ｜ 僅供參考，不構成投資建議</p>
  </div>

</div>
</body>
</html>"""

    return html


def send_email(html_content: str, subject: str) -> bool:
    """透過 Gmail SMTP 發送 HTML 郵件"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_USER
        msg["To"] = RECIPIENT

        part = MIMEText(html_content, "html", "utf-8")
        msg.attach(part)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, RECIPIENT, msg.as_string())

        print(f"  ✅ 郵件已成功發送至 {RECIPIENT}")
        return True
    except Exception as e:
        print(f"  ❌ 郵件發送失敗: {e}")
        traceback.print_exc()
        return False


def main():
    taipei_tz = pytz.timezone("Asia/Taipei")
    now = datetime.now(taipei_tz)
    date_str = now.strftime("%Y年%m月%d日")
    weekday_names = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
    weekday = weekday_names[now.weekday()]

    print("=" * 60)
    print(f"  美股科技股分析腳本")
    print(f"  執行時間：{now.strftime('%Y-%m-%d %H:%M:%S')} ({weekday})")
    print("=" * 60)

    # 收集所有股票數據
    all_data = {}
    all_tickers = []
    for sector_stocks in STOCKS.values():
        all_tickers.extend(sector_stocks.keys())

    print(f"\n📡 開始獲取 {len(all_tickers)} 支股票數據...")
    for ticker in all_tickers:
        print(f"  獲取 {ticker}...", end=" ")
        data = get_stock_data(ticker)
        all_data[ticker] = data
        if data:
            print(f"✅ ${data['current_price']:.2f} ({data['change_pct']:+.2f}%)")
        else:
            print("❌ 失敗")
        time.sleep(0.3)  # 避免請求過快

    valid_count = sum(1 for v in all_data.values() if v is not None)
    print(f"\n📊 成功獲取 {valid_count}/{len(all_tickers)} 支股票數據")

    if valid_count < len(all_tickers) * 0.5:
        print("❌ 有效數據不足 50%，中止發送")
        return

    # 生成 HTML 報告
    print("\n📝 生成分析報告...")
    html_report = generate_html_report(all_data, date_str)

    # 儲存 HTML 報告到本地
    report_path = f"/home/ubuntu/tech_stock_report_{now.strftime('%Y%m%d_%H%M')}.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_report)
    print(f"  📄 報告已儲存至：{report_path}")

    # 發送郵件
    subject = f"📊 美股科技股分析報告 {date_str} ({weekday}) | AI產業・區塊鏈・台股連動"
    print(f"\n📧 發送郵件至 {RECIPIENT}...")
    success = send_email(html_report, subject)

    print("\n" + "=" * 60)
    if success:
        print("  ✅ 任務完成！報告已成功發送")
    else:
        print("  ⚠️ 報告生成完成，但郵件發送失敗")
    print("=" * 60)


if __name__ == "__main__":
    main()
