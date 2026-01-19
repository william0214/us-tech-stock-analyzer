#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股科技股分析報告生成器
分析 AI 產業、區塊鏈、台股連動股的漲跌情況
生成包含外資目標價與台股推薦建議的專業分析報告
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pytz

# 股票分類
STOCK_CATEGORIES = {
    'AI產業龍頭': ['NVDA', 'MSFT', 'GOOGL', 'META', 'TSLA', 'AMD', 'AVGO', 'ORCL', 'CRM', 'PLTR'],
    '區塊鏈相關': ['COIN', 'MSTR', 'RIOT', 'MARA', 'PYPL'],
    '台股連動核心': ['AAPL', 'QCOM', 'INTC', 'AMZN']
}

# 外資目標價資料庫
FOREIGN_TARGET_PRICES = {
    '台積電 (2330)': {'target': 2400, 'source': 'Aletheia Capital'},
    '鴻海 (2317)': {'target': 400, 'source': '美系外資'},
    '廣達 (2382)': {'target': 400, 'source': '野村/瑞銀/群益'},
    '日月光 (3711)': {'target': 340, 'source': '美系外資'},
    '京元電 (2449)': {'target': 330, 'source': '美系外資'},
    '緯創 (3231)': {'target': 215, 'source': '多家法人'},
    '旺矽 (6223)': {'target': 2800, 'source': '美系外資'}
}

# Gmail 設定
GMAIL_CONFIG = {
    'sender': 'william0214@gmail.com',
    'receiver': 'william0214@gmail.com',
    'password': 'mbvg fhbx axrp hwua',
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 465
}

def get_stock_data(ticker):
    """獲取單支股票數據"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='5d')
        
        if len(hist) < 2:
            print(f"警告：{ticker} 數據不足")
            return None
        
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change_pct = ((current_price - prev_price) / prev_price) * 100
        
        current_volume = hist['Volume'].iloc[-1]
        avg_volume = hist['Volume'].iloc[:-1].mean()
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        return {
            'ticker': ticker,
            'name': stock.info.get('shortName', ticker),
            'current_price': current_price,
            'prev_price': prev_price,
            'change_pct': change_pct,
            'volume': current_volume,
            'avg_volume': avg_volume,
            'volume_ratio': volume_ratio
        }
    except Exception as e:
        print(f"錯誤：無法獲取 {ticker} 數據 - {str(e)}")
        return None

def analyze_stocks():
    """分析所有股票"""
    all_stocks = []
    stock_data_by_category = {}
    
    print("開始獲取股票數據...")
    
    for category, tickers in STOCK_CATEGORIES.items():
        print(f"\n處理 {category}...")
        category_data = []
        
        for ticker in tickers:
            data = get_stock_data(ticker)
            if data:
                data['category'] = category
                all_stocks.append(data)
                category_data.append(data)
                print(f"  ✓ {ticker}: {data['change_pct']:.2f}%")
        
        stock_data_by_category[category] = category_data
    
    if not all_stocks:
        raise Exception("無法獲取任何股票數據")
    
    df = pd.DataFrame(all_stocks)
    return df, stock_data_by_category

def generate_taiwan_recommendations(us_stocks_df):
    """根據美股表現生成台股推薦"""
    recommendations = []
    
    # 分析 AI 產業龍頭表現
    ai_stocks = us_stocks_df[us_stocks_df['category'] == 'AI產業龍頭']
    ai_avg_change = ai_stocks['change_pct'].mean()
    
    # NVIDIA 相關供應鏈
    if 'NVDA' in ai_stocks['ticker'].values:
        nvda_change = ai_stocks[ai_stocks['ticker'] == 'NVDA']['change_pct'].iloc[0]
        if nvda_change > 2:
            recommendations.append({
                'stock': '台積電 (2330)',
                'reason': f'NVIDIA 大漲 {nvda_change:.2f}%，CoWoS 先進封裝需求強勁',
                'timing': '開盤後觀察，若站穩平盤可分批進場',
                'risk': '留意美股後續走勢',
                'has_target': True
            })
            recommendations.append({
                'stock': '日月光 (3711)',
                'reason': 'AI 晶片封測需求增溫',
                'timing': '回檔至支撐區可布局',
                'risk': '短期波動較大',
                'has_target': True
            })
    
    # Apple 供應鏈
    if 'AAPL' in us_stocks_df['ticker'].values:
        aapl_change = us_stocks_df[us_stocks_df['ticker'] == 'AAPL']['change_pct'].iloc[0]
        if aapl_change > 1:
            recommendations.append({
                'stock': '鴻海 (2317)',
                'reason': f'Apple 上漲 {aapl_change:.2f}%，iPhone 組裝訂單穩定',
                'timing': '尾盤前 30 分鐘觀察量能',
                'risk': '注意匯率波動影響',
                'has_target': True
            })
    
    # AI 伺服器供應鏈
    if ai_avg_change > 1:
        recommendations.append({
            'stock': '廣達 (2382)',
            'reason': f'AI 產業平均上漲 {ai_avg_change:.2f}%，伺服器出貨動能強',
            'timing': '突破前高可追價',
            'risk': '已有一段漲幅，注意高檔震盪',
            'has_target': True
        })
        recommendations.append({
            'stock': '緯創 (3231)',
            'reason': 'AI 伺服器訂單能見度佳',
            'timing': '回測季線支撐可加碼',
            'risk': '毛利率壓力需觀察',
            'has_target': True
        })
    
    # 半導體設備與測試
    amd_stocks = us_stocks_df[us_stocks_df['ticker'] == 'AMD']
    if not amd_stocks.empty and amd_stocks['change_pct'].iloc[0] > 2:
        recommendations.append({
            'stock': '京元電 (2449)',
            'reason': 'AMD 強勢，GPU 測試需求增加',
            'timing': '量增價漲時進場',
            'risk': '小型股波動大，設停損',
            'has_target': True
        })
        recommendations.append({
            'stock': '旺矽 (6223)',
            'reason': 'AI 晶片測試需求爆發',
            'timing': '突破整理平台可布局',
            'risk': '籌碼集中，留意主力動向',
            'has_target': True
        })
    
    # 區塊鏈相關
    crypto_stocks = us_stocks_df[us_stocks_df['category'] == '區塊鏈相關']
    if not crypto_stocks.empty:
        crypto_avg_change = crypto_stocks['change_pct'].mean()
        if crypto_avg_change > 3:
            recommendations.append({
                'stock': '世芯-KY (3661)',
                'reason': f'區塊鏈股平均大漲 {crypto_avg_change:.2f}%，挖礦晶片設計受惠',
                'timing': '開盤跳空可等回測缺口',
                'risk': '加密貨幣波動影響大',
                'has_target': False
            })
    
    return recommendations

def generate_html_report(df, stock_data_by_category, taiwan_recs):
    """生成 HTML 格式報告"""
    
    # 取得台北時間
    taipei_tz = pytz.timezone('Asia/Taipei')
    report_time = datetime.now(taipei_tz).strftime('%Y年%m月%d日 %H:%M')
    
    # 計算統計數據
    top_gainers = df.nlargest(5, 'change_pct')[['ticker', 'name', 'change_pct', 'current_price']]
    top_losers = df.nsmallest(5, 'change_pct')[['ticker', 'name', 'change_pct', 'current_price']]
    high_volume = df[df['volume_ratio'] > 1.5].sort_values('volume_ratio', ascending=False)[['ticker', 'name', 'volume_ratio', 'change_pct']]
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>美股科技股分析報告 - {report_time}</title>
    <style>
        body {{
            font-family: 'Microsoft JhengHei', 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 28px;
        }}
        .header .time {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th {{
            background-color: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e0e0e0;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .positive {{
            color: #d32f2f;
            font-weight: bold;
        }}
        .negative {{
            color: #388e3c;
            font-weight: bold;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            margin-left: 5px;
        }}
        .badge-target {{
            background-color: #d32f2f;
            color: white;
        }}
        .badge-hot {{
            background-color: #ff6f00;
            color: white;
        }}
        .recommendation-card {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .recommendation-card h3 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 18px;
        }}
        .recommendation-card p {{
            margin: 5px 0;
            font-size: 14px;
        }}
        .recommendation-card .label {{
            font-weight: bold;
            color: #667eea;
        }}
        .risk-warning {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 美股科技股分析報告</h1>
        <div class="time">報告時間：{report_time}</div>
    </div>
"""
    
    # 漲幅前五名
    html += """
    <div class="section">
        <h2>🚀 漲幅前五名</h2>
        <table>
            <tr>
                <th>代碼</th>
                <th>名稱</th>
                <th>漲跌幅</th>
                <th>當前價格</th>
            </tr>
"""
    for _, row in top_gainers.iterrows():
        html += f"""
            <tr>
                <td><strong>{row['ticker']}</strong></td>
                <td>{row['name']}</td>
                <td class="positive">+{row['change_pct']:.2f}%</td>
                <td>${row['current_price']:.2f}</td>
            </tr>
"""
    html += """
        </table>
    </div>
"""
    
    # 跌幅前五名
    html += """
    <div class="section">
        <h2>📉 跌幅前五名</h2>
        <table>
            <tr>
                <th>代碼</th>
                <th>名稱</th>
                <th>漲跌幅</th>
                <th>當前價格</th>
            </tr>
"""
    for _, row in top_losers.iterrows():
        html += f"""
            <tr>
                <td><strong>{row['ticker']}</strong></td>
                <td>{row['name']}</td>
                <td class="negative">{row['change_pct']:.2f}%</td>
                <td>${row['current_price']:.2f}</td>
            </tr>
"""
    html += """
        </table>
    </div>
"""
    
    # 成交量異常
    if not high_volume.empty:
        html += """
    <div class="section">
        <h2>📈 成交量異常股票（>1.5倍平均）</h2>
        <table>
            <tr>
                <th>代碼</th>
                <th>名稱</th>
                <th>量比</th>
                <th>漲跌幅</th>
            </tr>
"""
        for _, row in high_volume.iterrows():
            change_class = 'positive' if row['change_pct'] > 0 else 'negative'
            change_sign = '+' if row['change_pct'] > 0 else ''
            html += f"""
            <tr>
                <td><strong>{row['ticker']}</strong></td>
                <td>{row['name']}</td>
                <td><span class="badge badge-hot">{row['volume_ratio']:.2f}x</span></td>
                <td class="{change_class}">{change_sign}{row['change_pct']:.2f}%</td>
            </tr>
"""
        html += """
        </table>
    </div>
"""
    
    # 依產業分類
    for category, stocks in stock_data_by_category.items():
        if stocks:
            html += f"""
    <div class="section">
        <h2>📋 {category}</h2>
        <table>
            <tr>
                <th>代碼</th>
                <th>名稱</th>
                <th>漲跌幅</th>
                <th>當前價格</th>
                <th>量比</th>
            </tr>
"""
            for stock in sorted(stocks, key=lambda x: x['change_pct'], reverse=True):
                change_class = 'positive' if stock['change_pct'] > 0 else 'negative'
                change_sign = '+' if stock['change_pct'] > 0 else ''
                volume_badge = f'<span class="badge badge-hot">{stock["volume_ratio"]:.1f}x</span>' if stock['volume_ratio'] > 1.5 else f'{stock["volume_ratio"]:.1f}x'
                html += f"""
            <tr>
                <td><strong>{stock['ticker']}</strong></td>
                <td>{stock['name']}</td>
                <td class="{change_class}">{change_sign}{stock['change_pct']:.2f}%</td>
                <td>${stock['current_price']:.2f}</td>
                <td>{volume_badge}</td>
            </tr>
"""
            html += """
        </table>
    </div>
"""
    
    # 台股推薦建議
    html += """
    <div class="section">
        <h2>🎯 產業分析師觀點：台股投資建議</h2>
        <p style="color: #666; margin-bottom: 20px;">
            根據美股科技股表現，以下為台股相關供應鏈投資建議。標註 <span class="badge badge-target">外資調升</span> 者為近期外資調高目標價之個股。
        </p>
"""
    
    for rec in taiwan_recs:
        target_badge = '<span class="badge badge-target">外資調升</span>' if rec['has_target'] else ''
        target_info = ''
        
        if rec['has_target'] and rec['stock'] in FOREIGN_TARGET_PRICES:
            target_data = FOREIGN_TARGET_PRICES[rec['stock']]
            target_info = f'<p><span class="label">目標價：</span>NT$ {target_data["target"]} ({target_data["source"]})</p>'
        
        html += f"""
        <div class="recommendation-card">
            <h3>{rec['stock']} {target_badge}</h3>
            <p><span class="label">投資邏輯：</span>{rec['reason']}</p>
            <p><span class="label">進場時機：</span>{rec['timing']}</p>
            <p><span class="label">風險提示：</span>{rec['risk']}</p>
            {target_info}
        </div>
"""
    
    html += """
    </div>
    
    <div class="risk-warning">
        <strong>⚠️ 風險提示</strong><br>
        本報告僅供參考，不構成投資建議。股市有風險，投資需謹慎。請根據自身風險承受能力做出投資決策，並設定適當停損點。
    </div>
    
    <div class="footer">
        <p>本報告由自動化系統生成 | 數據來源：Yahoo Finance</p>
        <p>© 2026 美股科技股分析系統</p>
    </div>
</body>
</html>
"""
    
    return html

def send_email(html_content):
    """透過 Gmail 發送報告"""
    try:
        taipei_tz = pytz.timezone('Asia/Taipei')
        report_date = datetime.now(taipei_tz).strftime('%Y/%m/%d')
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'美股科技股分析報告 - {report_date}'
        msg['From'] = GMAIL_CONFIG['sender']
        msg['To'] = GMAIL_CONFIG['receiver']
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        print("\n正在連接 Gmail SMTP 伺服器...")
        with smtplib.SMTP_SSL(GMAIL_CONFIG['smtp_server'], GMAIL_CONFIG['smtp_port']) as server:
            print("正在登入...")
            server.login(GMAIL_CONFIG['sender'], GMAIL_CONFIG['password'])
            print("正在發送郵件...")
            server.send_message(msg)
            print(f"✓ 郵件已成功發送至 {GMAIL_CONFIG['receiver']}")
        
        return True
    except Exception as e:
        print(f"✗ 郵件發送失敗：{str(e)}")
        return False

def main():
    """主程式"""
    print("=" * 60)
    print("美股科技股分析報告生成器")
    print("=" * 60)
    
    try:
        # 分析股票
        print("\n【步驟 1/4】分析美股科技股...")
        df, stock_data_by_category = analyze_stocks()
        print(f"✓ 成功分析 {len(df)} 支股票")
        
        # 生成台股推薦
        print("\n【步驟 2/4】生成台股投資建議...")
        taiwan_recs = generate_taiwan_recommendations(df)
        print(f"✓ 生成 {len(taiwan_recs)} 項台股推薦")
        
        # 生成報告
        print("\n【步驟 3/4】生成 HTML 報告...")
        html_report = generate_html_report(df, stock_data_by_category, taiwan_recs)
        print("✓ HTML 報告生成完成")
        
        # 發送郵件
        print("\n【步驟 4/4】發送郵件...")
        if send_email(html_report):
            print("\n" + "=" * 60)
            print("✓ 任務完成！報告已成功發送")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("✗ 報告生成成功，但郵件發送失敗")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n✗ 執行失敗：{str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
