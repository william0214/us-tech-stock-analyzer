#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股科技股分析系統
分析 AI 產業、區塊鏈、台股連動股的漲跌情況
生成專業分析報告並透過 Gmail 發送
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pytz

# ============ 配置參數 ============
GMAIL_USER = "william0214@gmail.com"
GMAIL_APP_PASSWORD = "mbvg fhbx axrp hwua"
RECIPIENT_EMAIL = "william0214@gmail.com"

# ============ 股票列表 ============
STOCK_CATEGORIES = {
    "AI產業龍頭": ["NVDA", "MSFT", "GOOGL", "META", "TSLA", "AMD", "AVGO", "ORCL", "CRM", "PLTR"],
    "區塊鏈相關": ["COIN", "MSTR", "RIOT", "MARA", "PYPL"],
    "台股連動核心": ["AAPL", "QCOM", "INTC", "AMZN"]
}

# ============ 外資目標價資料庫 ============
FOREIGN_TARGETS = {
    "2330": {"name": "台積電", "target": 2400, "source": "Aletheia Capital"},
    "2317": {"name": "鴻海", "target": 400, "source": "美系外資"},
    "2382": {"name": "廣達", "target": 400, "source": "野村/瑞銀/群益"},
    "3711": {"name": "日月光", "target": 340, "source": "美系外資"},
    "2449": {"name": "京元電", "target": 330, "source": "美系外資"},
    "3231": {"name": "緯創", "target": 215, "source": "多家法人"},
    "6223": {"name": "旺矽", "target": 2800, "source": "美系外資"}
}

# ============ 台股推薦邏輯 ============
TAIWAN_STOCK_RECOMMENDATIONS = {
    "AI產業龍頭": {
        "大型股": ["2330 台積電", "2317 鴻海", "2382 廣達"],
        "小型活躍股": ["6223 旺矽", "3231 緯創"]
    },
    "區塊鏈相關": {
        "大型股": ["2330 台積電"],
        "小型活躍股": ["6223 旺矽"]
    },
    "台股連動核心": {
        "大型股": ["2330 台積電", "2317 鴻海", "3711 日月光"],
        "小型活躍股": ["2449 京元電", "3231 緯創"]
    }
}


def get_stock_data(ticker):
    """獲取單一股票數據"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        
        if len(hist) < 2:
            print(f"⚠️  {ticker}: 數據不足")
            return None
        
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change_pct = ((current_price - prev_price) / prev_price) * 100
        
        current_volume = hist['Volume'].iloc[-1]
        avg_volume = hist['Volume'].iloc[:-1].mean()
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        return {
            "ticker": ticker,
            "price": round(current_price, 2),
            "change_pct": round(change_pct, 2),
            "volume": int(current_volume),
            "volume_ratio": round(volume_ratio, 2)
        }
    except Exception as e:
        print(f"❌ {ticker}: {str(e)}")
        return None


def analyze_stocks():
    """分析所有股票"""
    all_stocks = []
    stock_data_by_category = {}
    
    print("=" * 60)
    print("🚀 開始分析美股科技股...")
    print("=" * 60)
    
    for category, tickers in STOCK_CATEGORIES.items():
        print(f"\n📊 分析 {category}...")
        category_data = []
        
        for ticker in tickers:
            data = get_stock_data(ticker)
            if data:
                data['category'] = category
                all_stocks.append(data)
                category_data.append(data)
                print(f"✅ {ticker}: {data['change_pct']:+.2f}%")
        
        stock_data_by_category[category] = category_data
    
    if not all_stocks:
        print("❌ 無法獲取任何股票數據")
        return None, None
    
    print(f"\n✅ 成功獲取 {len(all_stocks)} 支股票數據")
    return all_stocks, stock_data_by_category


def generate_html_report(all_stocks, stock_data_by_category):
    """生成 HTML 格式報告"""
    
    # 排序數據
    top_gainers = sorted(all_stocks, key=lambda x: x['change_pct'], reverse=True)[:5]
    top_losers = sorted(all_stocks, key=lambda x: x['change_pct'])[:5]
    high_volume = [s for s in all_stocks if s['volume_ratio'] > 1.5]
    
    # 台股推薦
    taiwan_recommendations = generate_taiwan_recommendations(all_stocks)
    
    # 生成 HTML
    html = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>美股科技股分析報告 - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            padding-left: 10px;
            border-left: 5px solid #3498db;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .positive {{
            color: #27ae60;
            font-weight: bold;
        }}
        .negative {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            margin-left: 5px;
        }}
        .badge-target {{
            background-color: #e74c3c;
            color: white;
        }}
        .badge-volume {{
            background-color: #f39c12;
            color: white;
        }}
        .summary {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .category-section {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 美股科技股分析報告</h1>
        <div class="summary">
            <p><strong>報告時間：</strong>{datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')} (台北時間)</p>
            <p><strong>分析範圍：</strong>AI產業龍頭、區塊鏈相關、台股連動核心股 (共 {len(all_stocks)} 支)</p>
        </div>

        <h2>🔥 漲幅前五名</h2>
        <table>
            <tr>
                <th>股票代號</th>
                <th>產業分類</th>
                <th>當前價格</th>
                <th>漲跌幅</th>
                <th>成交量比</th>
            </tr>
"""
    
    for stock in top_gainers:
        volume_badge = f'<span class="badge badge-volume">量增</span>' if stock['volume_ratio'] > 1.5 else ''
        html += f"""
            <tr>
                <td><strong>{stock['ticker']}</strong></td>
                <td>{stock['category']}</td>
                <td>${stock['price']}</td>
                <td class="positive">+{stock['change_pct']}%</td>
                <td>{stock['volume_ratio']}x {volume_badge}</td>
            </tr>
"""
    
    html += """
        </table>

        <h2>📉 跌幅前五名</h2>
        <table>
            <tr>
                <th>股票代號</th>
                <th>產業分類</th>
                <th>當前價格</th>
                <th>漲跌幅</th>
                <th>成交量比</th>
            </tr>
"""
    
    for stock in top_losers:
        volume_badge = f'<span class="badge badge-volume">量增</span>' if stock['volume_ratio'] > 1.5 else ''
        html += f"""
            <tr>
                <td><strong>{stock['ticker']}</strong></td>
                <td>{stock['category']}</td>
                <td>${stock['price']}</td>
                <td class="negative">{stock['change_pct']}%</td>
                <td>{stock['volume_ratio']}x {volume_badge}</td>
            </tr>
"""
    
    html += """
        </table>
"""
    
    if high_volume:
        html += """
        <h2>⚡ 成交量異常股票 (>1.5倍平均)</h2>
        <table>
            <tr>
                <th>股票代號</th>
                <th>產業分類</th>
                <th>漲跌幅</th>
                <th>成交量比</th>
            </tr>
"""
        for stock in sorted(high_volume, key=lambda x: x['volume_ratio'], reverse=True):
            change_class = "positive" if stock['change_pct'] > 0 else "negative"
            html += f"""
            <tr>
                <td><strong>{stock['ticker']}</strong></td>
                <td>{stock['category']}</td>
                <td class="{change_class}">{stock['change_pct']:+.2f}%</td>
                <td>{stock['volume_ratio']}x</td>
            </tr>
"""
        html += """
        </table>
"""
    
    # 依產業分類的完整列表
    for category, stocks in stock_data_by_category.items():
        html += f"""
        <div class="category-section">
            <h2>📊 {category}</h2>
            <table>
                <tr>
                    <th>股票代號</th>
                    <th>當前價格</th>
                    <th>漲跌幅</th>
                    <th>成交量比</th>
                </tr>
"""
        for stock in sorted(stocks, key=lambda x: x['change_pct'], reverse=True):
            change_class = "positive" if stock['change_pct'] > 0 else "negative"
            volume_badge = f'<span class="badge badge-volume">量增</span>' if stock['volume_ratio'] > 1.5 else ''
            html += f"""
                <tr>
                    <td><strong>{stock['ticker']}</strong></td>
                    <td>${stock['price']}</td>
                    <td class="{change_class}">{stock['change_pct']:+.2f}%</td>
                    <td>{stock['volume_ratio']}x {volume_badge}</td>
                </tr>
"""
        html += """
            </table>
        </div>
"""
    
    # 台股推薦
    html += taiwan_recommendations
    
    html += """
        <div class="footer">
            <p>本報告由自動化系統生成，僅供參考，不構成投資建議</p>
            <p>數據來源：Yahoo Finance | 發送時間：每日 07:30 (台北時間)</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


def generate_taiwan_recommendations(all_stocks):
    """根據美股表現生成台股推薦"""
    
    # 計算各類別平均漲跌幅
    category_performance = {}
    for category, tickers in STOCK_CATEGORIES.items():
        category_stocks = [s for s in all_stocks if s['category'] == category]
        if category_stocks:
            avg_change = sum(s['change_pct'] for s in category_stocks) / len(category_stocks)
            category_performance[category] = avg_change
    
    html = """
        <h2>🎯 產業分析師台股推薦</h2>
        <div class="summary">
            <p><strong>分析觀點：</strong>根據美股科技股表現，以下為台股相關標的投資建議</p>
        </div>
"""
    
    for category, avg_change in category_performance.items():
        if category not in TAIWAN_STOCK_RECOMMENDATIONS:
            continue
        
        sentiment = "看多" if avg_change > 0 else "觀望"
        sentiment_color = "#27ae60" if avg_change > 0 else "#e67e22"
        
        html += f"""
        <div class="category-section">
            <h3>{category} - 美股平均 <span style="color: {sentiment_color};">{avg_change:+.2f}%</span> ({sentiment})</h3>
            <table>
                <tr>
                    <th>股票代號</th>
                    <th>股票名稱</th>
                    <th>類型</th>
                    <th>外資目標價</th>
                    <th>進場建議</th>
                </tr>
"""
        
        recommendations = TAIWAN_STOCK_RECOMMENDATIONS[category]
        
        for stock_type, stocks in recommendations.items():
            for stock_info in stocks:
                stock_code = stock_info.split()[0]
                stock_name = stock_info.split()[1]
                
                target_badge = ""
                target_info = "-"
                entry_suggestion = ""
                
                if stock_code in FOREIGN_TARGETS:
                    target_data = FOREIGN_TARGETS[stock_code]
                    target_badge = f'<span class="badge badge-target">目標價調升</span>'
                    target_info = f"NT$ {target_data['target']} ({target_data['source']})"
                
                if avg_change > 2:
                    entry_suggestion = "積極佈局，尾盤前30分鐘進場"
                elif avg_change > 0:
                    entry_suggestion = "穩健佈局，觀察量能後進場"
                else:
                    entry_suggestion = "暫時觀望，等待回檔"
                
                html += f"""
                <tr>
                    <td><strong>{stock_code}</strong></td>
                    <td>{stock_name} {target_badge}</td>
                    <td>{stock_type}</td>
                    <td>{target_info}</td>
                    <td>{entry_suggestion}</td>
                </tr>
"""
        
        html += """
            </table>
        </div>
"""
    
    # 風險提示
    html += """
        <div class="summary">
            <h3>⚠️ 風險提示</h3>
            <ul>
                <li>小型活躍股波動較大，建議控制倉位在總資金的 10-15%</li>
                <li>外資目標價僅供參考，需搭配技術面與籌碼面綜合判斷</li>
                <li>建議在尾盤前 30 分鐘進行分析並佈局買進</li>
                <li>設定停損點，控制單筆虧損在 3-5% 以內</li>
            </ul>
        </div>
"""
    
    return html


def send_email(html_content):
    """透過 Gmail 發送報告"""
    try:
        print("\n" + "=" * 60)
        print("📧 準備發送郵件...")
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"美股科技股分析報告 - {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = GMAIL_USER
        msg['To'] = RECIPIENT_EMAIL
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ 郵件發送成功！")
        print(f"   收件人：{RECIPIENT_EMAIL}")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ 郵件發送失敗：{str(e)}")
        return False


def main():
    """主程式"""
    print("\n" + "=" * 60)
    print("🚀 美股科技股分析系統啟動")
    print("=" * 60)
    print(f"執行時間：{datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')} (台北時間)")
    
    # 分析股票
    all_stocks, stock_data_by_category = analyze_stocks()
    
    if not all_stocks:
        print("❌ 分析失敗：無法獲取股票數據")
        return
    
    # 生成報告
    print("\n📝 生成 HTML 報告...")
    html_report = generate_html_report(all_stocks, stock_data_by_category)
    
    # 發送郵件
    success = send_email(html_report)
    
    if success:
        print("\n✅ 任務完成！")
    else:
        print("\n⚠️  報告生成成功但郵件發送失敗")
        print("   請檢查 Gmail 設定與網路連線")


if __name__ == "__main__":
    main()
