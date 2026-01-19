#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股科技股分析報告生成器
分析 AI產業、區塊鏈、台股連動股的漲跌情況
生成包含外資目標價與台股推薦建議的專業分析報告
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pytz

# 股票列表
STOCKS = {
    'AI產業龍頭': ['NVDA', 'MSFT', 'GOOGL', 'META', 'TSLA', 'AMD', 'AVGO', 'ORCL', 'CRM', 'PLTR'],
    '區塊鏈相關': ['COIN', 'MSTR', 'RIOT', 'MARA', 'PYPL'],
    '台股連動核心': ['AAPL', 'QCOM', 'INTC', 'AMZN'],
    'CPO共封裝光學': ['AVGO', 'MRVL', 'LITE', 'INTC'],
    '低軌衛星': ['GSAT', 'IRDM', 'GILT', 'AMZN'],
    'HBM記憶體': ['MU', 'SSNLF', 'WDC', 'STX']
}

# 外資目標價資料庫
FOREIGN_TARGETS = {
    '台積電 (2330)': {'target': 2400, 'broker': 'Aletheia Capital'},
    '鴻海 (2317)': {'target': 400, 'broker': '美系外資'},
    '廣達 (2382)': {'target': 400, 'broker': '野村/瑞銀/群益'},
    '日月光 (3711)': {'target': 340, 'broker': '美系外資'},
    '京元電 (2449)': {'target': 330, 'broker': '美系外資'},
    '緯創 (3231)': {'target': 215, 'broker': '多家法人'},
    '旺矽 (6223)': {'target': 2800, 'broker': '美系外資'},
    '聯亞 (3081)': {'target': 520, 'broker': '外資券商', 'note': 'CPO供應鏈'},
    '波若威 (3163)': {'target': 850, 'broker': '法人機構', 'note': 'CPO光通訊'},
    '輝達 (3363)': {'target': 180, 'broker': '外資券商', 'note': 'CPO光學元件'},
    '昇達科 (3491)': {'target': 380, 'broker': '外資券商', 'note': '低軌衛星通訊'},
    '啟碁 (6285)': {'target': 280, 'broker': '外資券商', 'note': '低軌衛星終端'},
    '南亞 (2408)': {'target': 420, 'broker': '外資券商', 'note': 'HBM基板供應'},
    '欣興電 (3037)': {'target': 180, 'broker': '法人機構', 'note': 'HBM測試設備'},
    '載德 (2436)': {'target': 650, 'broker': '外資券商', 'note': 'HBM封裝測試'},
    '智原 (3035)': {'target': 320, 'broker': '法人機構', 'note': 'HBM測試界面'}
}

# Gmail 設定
GMAIL_USER = 'william0214@gmail.com'
GMAIL_APP_PASSWORD = 'mbvg fhbx axrp hwua'
RECIPIENT = 'william0214@gmail.com'


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
            'price': current_price,
            'change_pct': change_pct,
            'volume': current_volume,
            'volume_ratio': volume_ratio
        }
    except Exception as e:
        print(f"錯誤：無法獲取 {ticker} 數據 - {e}")
        return None


def analyze_stocks():
    """分析所有股票"""
    all_data = []
    
    for category, tickers in STOCKS.items():
        print(f"\n正在分析 {category}...")
        for ticker in tickers:
            data = get_stock_data(ticker)
            if data:
                data['category'] = category
                all_data.append(data)
    
    if not all_data:
        raise Exception("無法獲取任何股票數據")
    
    df = pd.DataFrame(all_data)
    return df


def generate_taiwan_recommendations(df):
    """根據美股表現生成台股推薦"""
    recommendations = []
    
    # 檢查 CPO 相關股票
    cpo_stocks = df[df['category'] == 'CPO共封裝光學']
    if not cpo_stocks.empty:
        avg_cpo_change = cpo_stocks['change_pct'].mean()
        if avg_cpo_change > 1:
            recommendations.append({
                'stock': '聯亞 (3081)',
                'reason': f'CPO 共封裝光學概念股，美股 CPO 類股平均上漲 {avg_cpo_change:.2f}%',
                'timing': '09:15分析，09:30進場，小型活躍股',
                'risk': '2026 CPO 商轉元年，注意出貨進度',
                'has_target': True
            })
            recommendations.append({
                'stock': '波若威 (3163)',
                'reason': 'CPO 光通訊模組供應商，台積電 CoWoS 受惠',
                'timing': '尾盤前30分鐘佈局',
                'risk': '小型股波動大，控制部位',
                'has_target': True
            })
    
    # 檢查低軌衛星相關股票
    leo_stocks = df[df['category'] == '低軌衛星']
    if not leo_stocks.empty:
        avg_leo_change = leo_stocks['change_pct'].mean()
        if avg_leo_change > 1:
            recommendations.append({
                'stock': '昇達科 (3491)',
                'reason': f'低軌衛星通訊設備商，美股低軌衛星類股平均上漨 {avg_leo_change:.2f}%',
                'timing': '13:00分析，13:20進場',
                'risk': '留意 Starlink 訂單動態',
                'has_target': True
            })
            recommendations.append({
                'stock': '啟碁 (6285)',
                'reason': '低軌衛星終端設備，受惠全球衛星網路建設',
                'timing': '開盤後觀察，站穩支撐再進',
                'risk': '注意毛利率與訂單能見度',
                'has_target': True
            })
    
    # 檢查 HBM 記憶體相關股票
    hbm_stocks = df[df['category'] == 'HBM記憶體']
    if not hbm_stocks.empty:
        avg_hbm_change = hbm_stocks['change_pct'].mean()
        # 檢查 Micron (MU) 表現
        mu = df[df['ticker'] == 'MU']
        if not mu.empty and mu.iloc[0]['change_pct'] > 1.5:
            recommendations.append({
                'stock': '南亞 (2408)',
                'reason': f'Micron 上漨 {mu.iloc[0]["change_pct"]:.2f}%，HBM 基板需求強勁',
                'timing': '尾盤前30分鐘佈局',
                'risk': '2026 HBM 超級週期，注意出貨量',
                'has_target': True
            })
            recommendations.append({
                'stock': '載德 (2436)',
                'reason': 'HBM 封裝測試領導廠，AI 伺服器需求爆發',
                'timing': '09:15分析，09:30進場',
                'risk': '留意美光與SK海力士訂單',
                'has_target': True
            })
        if avg_hbm_change > 1:
            recommendations.append({
                'stock': '欣興電 (3037)',
                'reason': f'HBM 測試設備供應商，美股 HBM 類股平均上漨 {avg_hbm_change:.2f}%',
                'timing': '13:00分析，13:20進場，小型活躍股',
                'risk': '注意資本支出與產能擴充',
                'has_target': True
            })
    
    # 檢查 NVDA 表現
    nvda = df[df['ticker'] == 'NVDA']
    if not nvda.empty and nvda.iloc[0]['change_pct'] > 2:
        recommendations.append({
            'stock': '台積電 (2330)',
            'reason': 'NVIDIA 強勢上漲，AI 供應鏈受惠',
            'timing': '開盤後觀察，若站穩前高可進場',
            'risk': '留意外資動向與匯率波動',
            'has_target': True
        })
        recommendations.append({
            'stock': '廣達 (2382)',
            'reason': 'AI 伺服器需求強勁',
            'timing': '尾盤前30分鐘佈局',
            'risk': '注意成交量是否放大',
            'has_target': True
        })
    
    # 檢查 AAPL 表現
    aapl = df[df['ticker'] == 'AAPL']
    if not aapl.empty and aapl.iloc[0]['change_pct'] > 1:
        recommendations.append({
            'stock': '鴻海 (2317)',
            'reason': 'Apple 供應鏈核心，訂單穩定',
            'timing': '13:00後分析，13:20進場',
            'risk': '留意產能利用率報告',
            'has_target': True
        })
    
    # 檢查半導體類股
    amd = df[df['ticker'] == 'AMD']
    if not amd.empty and amd.iloc[0]['change_pct'] > 3:
        recommendations.append({
            'stock': '日月光 (3711)',
            'reason': 'AMD 強勢，封測需求增加',
            'timing': '開盤觀察，突破壓力再進',
            'risk': '注意產能稼動率',
            'has_target': True
        })
        recommendations.append({
            'stock': '京元電 (2449)',
            'reason': '測試需求旺盛，小型活躍股',
            'timing': '09:15分析，09:30進場',
            'risk': '波動較大，設好停損',
            'has_target': True
        })
    
    # 總是推薦一些有外資調升的標的
    if len(recommendations) < 5:
        recommendations.append({
            'stock': '緯創 (3231)',
            'reason': 'AI 伺服器代工受惠，外資調升',
            'timing': '尾盤前30分鐘佈局',
            'risk': '留意毛利率變化',
            'has_target': True
        })
        recommendations.append({
            'stock': '旺矽 (6223)',
            'reason': '小型活躍股，測試介面晶片需求強',
            'timing': '09:15分析，09:30進場',
            'risk': '流動性較低，控制部位',
            'has_target': True
        })
    
    return recommendations


def generate_html_report(df, recommendations):
    """生成 HTML 格式報告"""
    # 排序
    top_gainers = df.nlargest(5, 'change_pct')
    top_losers = df.nsmallest(5, 'change_pct')
    high_volume = df[df['volume_ratio'] > 1.5].sort_values('volume_ratio', ascending=False)
    
    # 台北時間
    taipei_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taipei_tz)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Microsoft JhengHei', Arial, sans-serif;
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
                margin: 0;
                font-size: 28px;
            }}
            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
            }}
            .section {{
                background: white;
                padding: 25px;
                margin-bottom: 25px;
                border-radius: 10px;
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
                font-weight: bold;
            }}
            td {{
                padding: 12px;
                border-bottom: 1px solid #e0e0e0;
            }}
            tr:hover {{
                background-color: #f8f9ff;
            }}
            .positive {{
                color: #22c55e;
                font-weight: bold;
            }}
            .negative {{
                color: #ef4444;
                font-weight: bold;
            }}
            .badge {{
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 8px;
            }}
            .badge-red {{
                background-color: #fee2e2;
                color: #dc2626;
            }}
            .badge-blue {{
                background-color: #dbeafe;
                color: #2563eb;
            }}
            .recommendation-card {{
                background: #f8f9ff;
                border-left: 4px solid #667eea;
                padding: 15px;
                margin-bottom: 15px;
                border-radius: 5px;
            }}
            .recommendation-card h3 {{
                margin: 0 0 10px 0;
                color: #667eea;
            }}
            .recommendation-card p {{
                margin: 5px 0;
                line-height: 1.6;
            }}
            .footer {{
                text-align: center;
                color: #666;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 美股科技股每日分析報告</h1>
            <p>報告時間：{now.strftime('%Y年%m月%d日 %H:%M')} (台北時間)</p>
            <p>涵蓋範圍：AI產業龍頭、區塊鏈相關、台股連動核心、CPO共封裝光學、低軌衛星、HBM記憶體</p>
        </div>
        
        <div class="section">
            <h2>🚀 漲幅前五名</h2>
            <table>
                <tr>
                    <th>股票代碼</th>
                    <th>產業分類</th>
                    <th>當前價格</th>
                    <th>漲跌幅</th>
                    <th>成交量比</th>
                </tr>
    """
    
    for _, row in top_gainers.iterrows():
        html += f"""
                <tr>
                    <td><strong>{row['ticker']}</strong></td>
                    <td>{row['category']}</td>
                    <td>${row['price']:.2f}</td>
                    <td class="positive">+{row['change_pct']:.2f}%</td>
                    <td>{row['volume_ratio']:.2f}x</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
        
        <div class="section">
            <h2>📉 跌幅前五名</h2>
            <table>
                <tr>
                    <th>股票代碼</th>
                    <th>產業分類</th>
                    <th>當前價格</th>
                    <th>漲跌幅</th>
                    <th>成交量比</th>
                </tr>
    """
    
    for _, row in top_losers.iterrows():
        html += f"""
                <tr>
                    <td><strong>{row['ticker']}</strong></td>
                    <td>{row['category']}</td>
                    <td>${row['price']:.2f}</td>
                    <td class="negative">{row['change_pct']:.2f}%</td>
                    <td>{row['volume_ratio']:.2f}x</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
    """
    
    if not high_volume.empty:
        html += """
        <div class="section">
            <h2>📈 成交量異常股票 (>1.5倍平均)</h2>
            <table>
                <tr>
                    <th>股票代碼</th>
                    <th>產業分類</th>
                    <th>漲跌幅</th>
                    <th>成交量比</th>
                </tr>
        """
        
        for _, row in high_volume.iterrows():
            change_class = 'positive' if row['change_pct'] > 0 else 'negative'
            change_sign = '+' if row['change_pct'] > 0 else ''
            html += f"""
                <tr>
                    <td><strong>{row['ticker']}</strong></td>
                    <td>{row['category']}</td>
                    <td class="{change_class}">{change_sign}{row['change_pct']:.2f}%</td>
                    <td><strong>{row['volume_ratio']:.2f}x</strong></td>
                </tr>
            """
        
        html += """
            </table>
        </div>
        """
    
    # 完整列表
    html += """
        <div class="section">
            <h2>📋 完整股票列表（依產業分類）</h2>
    """
    
    for category in STOCKS.keys():
        category_stocks = df[df['category'] == category].sort_values('change_pct', ascending=False)
        html += f"""
            <h3>{category}</h3>
            <table>
                <tr>
                    <th>股票代碼</th>
                    <th>當前價格</th>
                    <th>漲跌幅</th>
                    <th>成交量比</th>
                </tr>
        """
        
        for _, row in category_stocks.iterrows():
            change_class = 'positive' if row['change_pct'] > 0 else 'negative'
            change_sign = '+' if row['change_pct'] > 0 else ''
            html += f"""
                <tr>
                    <td><strong>{row['ticker']}</strong></td>
                    <td>${row['price']:.2f}</td>
                    <td class="{change_class}">{change_sign}{row['change_pct']:.2f}%</td>
                    <td>{row['volume_ratio']:.2f}x</td>
                </tr>
            """
        
        html += """
            </table>
        """
    
    html += """
        </div>
        
        <div class="section">
            <h2>💡 產業分析師觀點：台股投資建議</h2>
            <p style="color: #666; margin-bottom: 20px;">
                根據美股科技股表現，以下為台股相關標的投資建議。
                標註 <span class="badge badge-red">外資調升</span> 者為近期外資上調目標價之標的。
            </p>
    """
    
    for rec in recommendations:
        target_badge = ''
        target_info = ''
        if rec['has_target'] and rec['stock'] in FOREIGN_TARGETS:
            target_data = FOREIGN_TARGETS[rec['stock']]
            target_badge = '<span class="badge badge-red">外資調升</span>'
            target_info = f'<p><strong>目標價：</strong>{target_data["target"]}元 ({target_data["broker"]})</p>'
        
        html += f"""
            <div class="recommendation-card">
                <h3>{rec['stock']} {target_badge}</h3>
                <p><strong>推薦理由：</strong>{rec['reason']}</p>
                <p><strong>進場時機：</strong>{rec['timing']}</p>
                <p><strong>風險提示：</strong>{rec['risk']}</p>
                {target_info}
            </div>
        """
    
    html += """
        </div>
        
        <div class="section">
            <h2>📋 外資目標價總覽</h2>
            <table>
                <tr>
                    <th>股票</th>
                    <th>目標價</th>
                    <th>券商</th>
                    <th>產業備註</th>
                </tr>
    """
    
    for stock, data in FOREIGN_TARGETS.items():
        note = data.get('note', '-')
        html += f"""
                <tr>
                    <td><strong>{stock}</strong></td>
                    <td class="positive">{data['target']}元</td>
                    <td>{data['broker']}</td>
                    <td>{note}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
        
        <div class="footer">
            <p>本報告由自動化系統生成，數據來源：Yahoo Finance</p>
            <p>投資有風險，請謹慎評估後進行投資決策</p>
        </div>
    </body>
    </html>
    """
    
    return html


def send_email(html_content):
    """發送郵件"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'📊 美股科技股每日分析報告 - {datetime.now().strftime("%Y/%m/%d")}'
        msg['From'] = GMAIL_USER
        msg['To'] = RECIPIENT
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        print("\n正在連接 Gmail SMTP 伺服器...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ 郵件已成功發送至 {RECIPIENT}")
        return True
    except Exception as e:
        print(f"❌ 郵件發送失敗：{e}")
        return False


def main():
    """主程式"""
    print("=" * 60)
    print("美股科技股分析報告生成器")
    print("=" * 60)
    
    try:
        # 分析股票
        print("\n開始分析股票數據...")
        df = analyze_stocks()
        print(f"✅ 成功獲取 {len(df)} 支股票數據")
        
        # 生成台股推薦
        print("\n生成台股投資建議...")
        recommendations = generate_taiwan_recommendations(df)
        print(f"✅ 生成 {len(recommendations)} 項推薦")
        
        # 生成報告
        print("\n生成 HTML 報告...")
        html_report = generate_html_report(df, recommendations)
        print("✅ 報告生成完成")
        
        # 發送郵件
        print("\n發送郵件...")
        if send_email(html_report):
            print("\n" + "=" * 60)
            print("✅ 任務完成！")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("⚠️  報告生成成功但郵件發送失敗")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ 執行失敗：{e}")
        raise


if __name__ == "__main__":
    main()
