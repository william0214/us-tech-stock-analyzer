#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 股票分析短影片生成器
從真實股票數據自動生成 YouTube 短影片
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as pe
from matplotlib.gridspec import GridSpec
from datetime import datetime
import subprocess

# ── 讀取股票數據 ──────────────────────────────────────────
with open('/home/ubuntu/stock_history.json', 'r') as f:
    STOCK_DATA = json.load(f)

OUTPUT_DIR = '/home/ubuntu/video_frames'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 顏色設定 ──────────────────────────────────────────────
BG_COLOR      = '#0A0E1A'   # 深藍黑背景
ACCENT_BLUE   = '#00D4FF'   # 亮藍
ACCENT_GREEN  = '#00FF88'   # 亮綠
ACCENT_RED    = '#FF4466'   # 亮紅
ACCENT_GOLD   = '#FFD700'   # 金色
TEXT_WHITE    = '#FFFFFF'
TEXT_GRAY     = '#8899AA'
GRID_COLOR    = '#1A2035'

# ── 字型設定 ──────────────────────────────────────────────
plt.rcParams['font.family'] = ['Noto Sans CJK SC', 'Noto Sans', 'DejaVu Sans']
plt.rcParams['axes.facecolor'] = BG_COLOR
plt.rcParams['figure.facecolor'] = BG_COLOR

# 影片尺寸：9:16 豎版（YouTube Shorts）
VIDEO_W, VIDEO_H = 1080, 1920
DPI = 96
FIG_W = VIDEO_W / DPI
FIG_H = VIDEO_H / DPI

TOTAL_FRAMES = 300   # 10 秒 × 30fps
FPS = 30

# ── 輔助函數 ──────────────────────────────────────────────
def color_for_change(pct):
    return ACCENT_GREEN if pct >= 0 else ACCENT_RED

def arrow_for_change(pct):
    return '▲' if pct >= 0 else '▼'

def glow_text(ax, x, y, text, fontsize, color, weight='bold', ha='center', va='center', alpha_glow=0.3):
    """帶光暈效果的文字"""
    for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
        ax.text(x + offset[0]*0.001, y + offset[1]*0.001, text,
                fontsize=fontsize, color=color, weight=weight,
                ha=ha, va=va, alpha=alpha_glow,
                transform=ax.transAxes)
    ax.text(x, y, text,
            transform=ax.transAxes,
            fontsize=fontsize, color=color, weight=weight,
            ha=ha, va=va)

# ── 場景 1：開場動畫（0-60 幀）──────────────────────────
def render_intro(frame_idx):
    """開場：品牌標題動畫"""
    t = frame_idx / 60.0  # 0→1

    fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=BG_COLOR)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_facecolor(BG_COLOR)

    # 動態網格線
    for i in range(0, 11):
        alpha = 0.08 + 0.04 * np.sin(t * np.pi * 2 + i * 0.5)
        ax.axhline(y=i/10, color=ACCENT_BLUE, alpha=alpha, linewidth=0.5)
        ax.axvline(x=i/10, color=ACCENT_BLUE, alpha=alpha, linewidth=0.5)

    # 漸入效果
    alpha_main = min(1.0, t * 2)

    # 主標題
    ax.text(0.5, 0.62, 'AI 美股分析', fontsize=72, color=TEXT_WHITE,
            weight='bold', ha='center', va='center', alpha=alpha_main,
            transform=ax.transAxes)

    # 副標題
    ax.text(0.5, 0.52, 'US Tech Stock Analyzer', fontsize=28, color=ACCENT_BLUE,
            weight='bold', ha='center', va='center', alpha=alpha_main,
            transform=ax.transAxes)

    # 日期
    today = datetime.now().strftime('%Y.%m.%d')
    ax.text(0.5, 0.44, today, fontsize=22, color=TEXT_GRAY,
            ha='center', va='center', alpha=alpha_main,
            transform=ax.transAxes)

    # 底部標語
    ax.text(0.5, 0.20, '每日自動分析 · AI 驅動洞察', fontsize=24, color=ACCENT_GOLD,
            ha='center', va='center', alpha=alpha_main * 0.9,
            transform=ax.transAxes)

    # 掃描線動畫
    scan_y = (t * 1.2) % 1.0
    ax.axhline(y=scan_y, color=ACCENT_BLUE, alpha=0.4, linewidth=2)
    ax.axhline(y=scan_y, color=TEXT_WHITE, alpha=0.1, linewidth=6)

    # 角落裝飾
    for corner_x, corner_y in [(0.05, 0.92), (0.95, 0.92), (0.05, 0.08), (0.95, 0.08)]:
        ax.text(corner_x, corner_y, '◈', fontsize=16, color=ACCENT_BLUE,
                ha='center', va='center', alpha=0.6, transform=ax.transAxes)

    plt.tight_layout(pad=0)
    path = f'{OUTPUT_DIR}/frame_{frame_idx:04d}.png'
    fig.savefig(path, dpi=DPI, bbox_inches='tight', pad_inches=0, facecolor=BG_COLOR)
    plt.close(fig)


# ── 場景 2：市場總覽（60-130 幀）────────────────────────
def render_market_overview(frame_idx, local_frame):
    """市場總覽：7 支股票的漲跌看板"""
    t = local_frame / 70.0

    tickers = ['NVDA', 'GOOGL', 'META', 'AAPL', 'TSLA', 'MSFT', 'AMD']
    stocks = [STOCK_DATA[tk] for tk in tickers]

    fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=BG_COLOR)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_facecolor(BG_COLOR)

    # 背景網格
    for i in range(0, 11):
        ax.axhline(y=i/10, color=ACCENT_BLUE, alpha=0.04, linewidth=0.5)

    # 標題
    ax.text(0.5, 0.94, '>> 今日市場總覽', fontsize=36, color=TEXT_WHITE,
            weight='bold', ha='center', va='center', transform=ax.transAxes)
    ax.text(0.5, 0.89, datetime.now().strftime('%Y-%m-%d  美股收盤'), fontsize=18,
            color=TEXT_GRAY, ha='center', va='center', transform=ax.transAxes)

    # 分隔線
    ax.axhline(y=0.87, xmin=0.05, xmax=0.95, color=ACCENT_BLUE, alpha=0.4, linewidth=1)

    # 每支股票的卡片
    card_h = 0.09
    card_gap = 0.01
    start_y = 0.83

    for i, (ticker, stock) in enumerate(zip(tickers, stocks)):
        card_y_top = start_y - i * (card_h + card_gap)
        card_y_bot = card_y_top - card_h

        # 動畫：逐一滑入
        slide_t = max(0, min(1, t * 3 - i * 0.3))
        x_offset = (1 - slide_t) * 0.3

        chg = stock['change_pct']
        clr = color_for_change(chg)
        arrow = arrow_for_change(chg)

        # 卡片背景
        card_alpha = 0.15 if chg >= 0 else 0.12
        card_color = ACCENT_GREEN if chg >= 0 else ACCENT_RED
        rect = patches.FancyBboxPatch(
            (0.04 + x_offset, card_y_bot + 0.005),
            0.92, card_h - 0.01,
            boxstyle='round,pad=0.01',
            facecolor=card_color, edgecolor=card_color,
            alpha=card_alpha * slide_t, transform=ax.transAxes
        )
        ax.add_patch(rect)

        mid_y = (card_y_top + card_y_bot) / 2

        # 股票代號
        ax.text(0.10 + x_offset, mid_y, ticker, fontsize=26, color=TEXT_WHITE,
                weight='bold', ha='center', va='center', transform=ax.transAxes,
                alpha=slide_t)

        # 公司名稱
        ax.text(0.10 + x_offset, mid_y - 0.025, stock['name'], fontsize=13,
                color=TEXT_GRAY, ha='center', va='center', transform=ax.transAxes,
                alpha=slide_t)

        # 價格
        ax.text(0.55 + x_offset, mid_y, f'${stock["current"]:,.2f}', fontsize=24,
                color=TEXT_WHITE, weight='bold', ha='center', va='center',
                transform=ax.transAxes, alpha=slide_t)

        # 漲跌幅
        ax.text(0.82 + x_offset, mid_y, f'{arrow} {abs(chg):.2f}%', fontsize=22,
                color=clr, weight='bold', ha='center', va='center',
                transform=ax.transAxes, alpha=slide_t)

    # 底部
    ax.text(0.5, 0.04, '數據來源：Yahoo Finance  |  AI 自動生成', fontsize=14,
            color=TEXT_GRAY, ha='center', va='center', transform=ax.transAxes)

    plt.tight_layout(pad=0)
    path = f'{OUTPUT_DIR}/frame_{frame_idx:04d}.png'
    fig.savefig(path, dpi=DPI, bbox_inches='tight', pad_inches=0, facecolor=BG_COLOR)
    plt.close(fig)


# ── 場景 3：GOOGL 深度分析（130-220 幀）────────────────
def render_stock_detail(frame_idx, local_frame, ticker='GOOGL'):
    """單股深度分析：走勢圖 + 技術指標"""
    t = local_frame / 90.0
    stock = STOCK_DATA[ticker]

    closes = np.array(stock['closes'])
    dates = stock['dates']
    n = len(closes)

    # 動態繪製：逐漸揭示走勢
    reveal_n = max(5, int(n * min(1.0, t * 1.5)))
    x_vals = np.arange(reveal_n)
    y_vals = closes[:reveal_n]

    fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=BG_COLOR)

    # 佈局
    gs = GridSpec(3, 1, figure=fig, hspace=0.08,
                  top=0.88, bottom=0.12, left=0.08, right=0.96,
                  height_ratios=[2.5, 0.8, 0.8])

    # ── 主圖：K 線走勢 ──
    ax1 = fig.add_subplot(gs[0])
    ax1.set_facecolor(BG_COLOR)

    # 填充區域
    ax1.fill_between(x_vals, y_vals, y_vals.min() * 0.995,
                     alpha=0.2, color=color_for_change(stock['change_pct']))
    ax1.plot(x_vals, y_vals, color=color_for_change(stock['change_pct']),
             linewidth=2.5, zorder=5)

    # 移動平均線
    if reveal_n >= 5:
        ma5 = np.convolve(closes[:reveal_n], np.ones(5)/5, mode='valid')
        ax1.plot(np.arange(4, reveal_n), ma5, color=ACCENT_GOLD,
                 linewidth=1.5, alpha=0.8, linestyle='--', label='MA5')

    # 最新價格標記
    if reveal_n > 0:
        ax1.scatter([reveal_n-1], [y_vals[-1]], color=color_for_change(stock['change_pct']),
                    s=80, zorder=10)
        ax1.annotate(f'${y_vals[-1]:.2f}',
                     xy=(reveal_n-1, y_vals[-1]),
                     xytext=(reveal_n-1 - 2, y_vals[-1] + (closes.max()-closes.min())*0.08),
                     fontsize=14, color=TEXT_WHITE, weight='bold',
                     arrowprops=dict(arrowstyle='->', color=TEXT_WHITE, lw=1.5))

    ax1.set_xlim(-1, n)
    ax1.set_ylim(closes.min() * 0.99, closes.max() * 1.01)
    ax1.tick_params(colors=TEXT_GRAY, labelsize=11)
    ax1.spines[:].set_color(GRID_COLOR)
    ax1.yaxis.tick_right()
    for spine in ax1.spines.values():
        spine.set_edgecolor(GRID_COLOR)
    ax1.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.5)
    ax1.set_ylabel('Price (USD)', color=TEXT_GRAY, fontsize=12)

    # ── 成交量圖 ──
    ax2 = fig.add_subplot(gs[1])
    ax2.set_facecolor(BG_COLOR)
    vols = np.array(stock['volumes'][:reveal_n])
    vol_colors = [ACCENT_GREEN if closes[i] >= closes[i-1] else ACCENT_RED
                  for i in range(1, reveal_n)] + [ACCENT_GREEN]
    ax2.bar(x_vals, vols, color=vol_colors[:reveal_n], alpha=0.7, width=0.8)
    ax2.set_xlim(-1, n)
    ax2.tick_params(colors=TEXT_GRAY, labelsize=10)
    for spine in ax2.spines.values():
        spine.set_edgecolor(GRID_COLOR)
    ax2.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.3)
    ax2.set_ylabel('Volume', color=TEXT_GRAY, fontsize=11)
    ax2.yaxis.tick_right()

    # ── RSI 指標 ──
    ax3 = fig.add_subplot(gs[2])
    ax3.set_facecolor(BG_COLOR)
    if reveal_n >= 15:
        delta = np.diff(closes[:reveal_n])
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = np.convolve(gain, np.ones(14)/14, mode='valid')
        avg_loss = np.convolve(loss, np.ones(14)/14, mode='valid')
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        rsi_x = np.arange(len(rsi))
        if len(rsi_x) > 0 and len(rsi) > 0:
            ax3.plot(rsi_x, rsi, color=ACCENT_BLUE, linewidth=1.5)
            ax3.axhline(y=70, color=ACCENT_RED, alpha=0.5, linewidth=1, linestyle='--')
            ax3.axhline(y=30, color=ACCENT_GREEN, alpha=0.5, linewidth=1, linestyle='--')
            ax3.fill_between(rsi_x, rsi, 50, where=(rsi > 50),
                             alpha=0.1, color=ACCENT_GREEN)
            ax3.fill_between(rsi_x, rsi, 50, where=(rsi < 50),
                             alpha=0.1, color=ACCENT_RED)
        ax3.set_ylim(0, 100)
    ax3.set_xlim(-1, n)
    ax3.tick_params(colors=TEXT_GRAY, labelsize=10)
    for spine in ax3.spines.values():
        spine.set_edgecolor(GRID_COLOR)
    ax3.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.3)
    ax3.set_ylabel('RSI', color=TEXT_GRAY, fontsize=11)
    ax3.yaxis.tick_right()

    # ── 頂部標題 ──
    chg = stock['change_pct']
    clr = color_for_change(chg)
    arrow = arrow_for_change(chg)

    fig.text(0.08, 0.95, ticker, fontsize=44, color=TEXT_WHITE, weight='bold')
    fig.text(0.08, 0.91, stock['name'], fontsize=20, color=TEXT_GRAY)
    fig.text(0.60, 0.95, f'${stock["current"]:,.2f}', fontsize=38,
             color=TEXT_WHITE, weight='bold', ha='right')
    fig.text(0.62, 0.95, f'{arrow} {abs(chg):.2f}%', fontsize=30,
             color=clr, weight='bold')
    fig.text(0.08, 0.88, '30 日走勢  ·  技術分析', fontsize=16, color=TEXT_GRAY)

    # ── 底部 ──
    fig.text(0.5, 0.04, '數據來源：Yahoo Finance  |  AI 自動生成分析', fontsize=13,
             color=TEXT_GRAY, ha='center')

    path = f'{OUTPUT_DIR}/frame_{frame_idx:04d}.png'
    fig.savefig(path, dpi=DPI, bbox_inches='tight', pad_inches=0, facecolor=BG_COLOR)
    plt.close(fig)


# ── 場景 4：AI 洞察文字（220-270 幀）────────────────────
INSIGHTS = [
    ('GOOGL', '+4.01%', 'Google 今日強勢領漲', 'Alphabet Q4 財報超預期\n廣告收入年增 +13%\nAI 搜尋引擎加速滲透'),
    ('NVDA', '+1.02%', 'NVIDIA 維持強勢', 'Blackwell GPU 出貨加速\nAI 資本支出持續擴大\n數據中心需求旺盛'),
    ('AMD', '-1.58%', 'AMD 短線回調', 'MI300X 出貨不如預期\n競爭壓力加劇\n關注下季財測指引'),
]

def render_ai_insight(frame_idx, local_frame):
    """AI 洞察：逐字顯示分析文字"""
    t = local_frame / 50.0
    insight_idx = min(int(t * len(INSIGHTS)), len(INSIGHTS) - 1)
    sub_t = (t * len(INSIGHTS)) % 1.0

    ticker, chg_str, title, body = INSIGHTS[insight_idx]
    stock = STOCK_DATA[ticker]
    chg = stock['change_pct']
    clr = color_for_change(chg)

    fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=BG_COLOR)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_facecolor(BG_COLOR)

    # 背景裝飾
    for i in range(0, 11):
        ax.axhline(y=i/10, color=ACCENT_BLUE, alpha=0.03, linewidth=0.5)

    # AI 標籤
    ax.text(0.5, 0.92, '[ AI 智能洞察 ]', fontsize=32, color=ACCENT_BLUE,
            weight='bold', ha='center', va='center', transform=ax.transAxes)

    # 股票代號大字
    ax.text(0.5, 0.80, ticker, fontsize=80, color=TEXT_WHITE,
            weight='bold', ha='center', va='center', transform=ax.transAxes,
            alpha=min(1.0, sub_t * 3))

    # 漲跌幅
    ax.text(0.5, 0.70, chg_str, fontsize=48, color=clr,
            weight='bold', ha='center', va='center', transform=ax.transAxes,
            alpha=min(1.0, sub_t * 3))

    # 標題
    ax.text(0.5, 0.60, title, fontsize=28, color=TEXT_WHITE,
            weight='bold', ha='center', va='center', transform=ax.transAxes,
            alpha=min(1.0, max(0, sub_t * 3 - 0.3)))

    # 分隔線
    line_alpha = min(1.0, max(0, sub_t * 3 - 0.5))
    ax.axhline(y=0.55, xmin=0.1, xmax=0.9, color=clr, alpha=line_alpha * 0.5, linewidth=1.5)

    # 分析內容（逐行顯示）
    lines = body.strip().split('\n')
    for li, line in enumerate(lines):
        line_t = min(1.0, max(0, sub_t * 4 - 0.5 - li * 0.3))
        ax.text(0.5, 0.48 - li * 0.07, f'• {line}', fontsize=22, color=TEXT_GRAY,
                ha='center', va='center', transform=ax.transAxes, alpha=line_t)

    # 進度指示器
    for pi in range(len(INSIGHTS)):
        dot_color = ACCENT_BLUE if pi == insight_idx else TEXT_GRAY
        ax.text(0.35 + pi * 0.15, 0.12, '●', fontsize=16, color=dot_color,
                ha='center', va='center', transform=ax.transAxes)

    ax.text(0.5, 0.06, '由 us-tech-stock-analyzer 驅動  |  AI 自動生成', fontsize=14,
            color=TEXT_GRAY, ha='center', va='center', transform=ax.transAxes)

    path = f'{OUTPUT_DIR}/frame_{frame_idx:04d}.png'
    fig.savefig(path, dpi=DPI, bbox_inches='tight', pad_inches=0, facecolor=BG_COLOR)
    plt.close(fig)


# ── 場景 5：結尾 CTA（270-300 幀）───────────────────────
def render_outro(frame_idx, local_frame):
    """結尾：訂閱 CTA"""
    t = local_frame / 30.0

    fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=BG_COLOR)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_facecolor(BG_COLOR)

    # 動態背景
    for i in range(0, 11):
        alpha = 0.06 + 0.04 * np.sin(t * np.pi * 3 + i * 0.5)
        ax.axhline(y=i/10, color=ACCENT_BLUE, alpha=alpha, linewidth=0.5)
        ax.axvline(x=i/10, color=ACCENT_BLUE, alpha=alpha, linewidth=0.5)

    pulse = 0.9 + 0.1 * np.sin(t * np.pi * 4)

    ax.text(0.5, 0.72, '每日自動更新', fontsize=36, color=TEXT_WHITE,
            weight='bold', ha='center', va='center', transform=ax.transAxes)
    ax.text(0.5, 0.63, 'AI 驅動 · 數據精準 · 洞察深刻', fontsize=24,
            color=ACCENT_BLUE, ha='center', va='center', transform=ax.transAxes)

    # 訂閱按鈕
    btn = patches.FancyBboxPatch((0.15, 0.44), 0.70, 0.10,
                                  boxstyle='round,pad=0.02',
                                  facecolor=ACCENT_RED, edgecolor='none',
                                  alpha=0.9 * pulse, transform=ax.transAxes)
    ax.add_patch(btn)
    ax.text(0.5, 0.49, '>> 訂閱頻道  不錯過每日分析', fontsize=22,
            color=TEXT_WHITE, weight='bold', ha='center', va='center',
            transform=ax.transAxes)

    ax.text(0.5, 0.35, '[+] 按讚   [?] 留言   [^] 分享', fontsize=22,
            color=ACCENT_GOLD, ha='center', va='center', transform=ax.transAxes)

    ax.text(0.5, 0.22, 'us-tech-stock-analyzer', fontsize=20,
            color=TEXT_GRAY, ha='center', va='center', transform=ax.transAxes)
    ax.text(0.5, 0.16, 'GitHub: william0214', fontsize=18,
            color=ACCENT_BLUE, ha='center', va='center', transform=ax.transAxes)

    ax.text(0.5, 0.07, '! 本影片僅供參考，不構成投資建議', fontsize=14,
            color=TEXT_GRAY, ha='center', va='center', transform=ax.transAxes)

    path = f'{OUTPUT_DIR}/frame_{frame_idx:04d}.png'
    fig.savefig(path, dpi=DPI, bbox_inches='tight', pad_inches=0, facecolor=BG_COLOR)
    plt.close(fig)


# ── 主渲染迴圈 ────────────────────────────────────────────
def render_all_frames():
    print(f"開始渲染 {TOTAL_FRAMES} 幀...")
    for i in range(TOTAL_FRAMES):
        if i % 30 == 0:
            print(f"  渲染進度：{i}/{TOTAL_FRAMES} ({i/TOTAL_FRAMES*100:.0f}%)")

        if i < 60:
            render_intro(i)
        elif i < 130:
            render_market_overview(i, i - 60)
        elif i < 220:
            render_stock_detail(i, i - 130)
        elif i < 270:
            render_ai_insight(i, i - 220)
        else:
            render_outro(i, i - 270)

    print(f"✅ 所有幀渲染完成！保存在 {OUTPUT_DIR}")


# ── 合成影片 ──────────────────────────────────────────────
def compose_video():
    output_path = '/home/ubuntu/ai_stock_analysis.mp4'
    print(f"\n開始合成影片：{output_path}")

    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(FPS),
        '-i', f'{OUTPUT_DIR}/frame_%04d.png',
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',
        '-vf', f'scale={VIDEO_W}:{VIDEO_H}',
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ 影片合成成功：{output_path}")
    else:
        print(f"❌ 影片合成失敗：{result.stderr}")

    return output_path


if __name__ == '__main__':
    render_all_frames()
    compose_video()
    print("\n🎬 AI 股票分析短影片製作完成！")
