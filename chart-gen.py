#!/usr/bin/env python3
"""Generate a REAL data-driven market chart from Yahoo Finance data."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# REAL DATA from Yahoo Finance (June 6, 2025 - June 6, 2026)
btc_months = ['Jun','Jul','Aug','Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun']
btc_prices = [104390, 105615, 117500, 109800, 113214, 85090, 87500, 78200, 62702, 70000, 74800, 71319, 60901]
eth_prices = [2477, 2416, 4390, 4145, 3847, 2992, 2967, 2445, 1965, 2104, 2256, 2004, 1558]
sol_prices = [148, 165, 210, 198, 188, 142, 126, 105, 87, 84, 82, 71, 61]

fig, axes = plt.subplots(3, 2, figsize=(18, 12), gridspec_kw={'width_ratios': [3, 1], 'height_ratios': [1, 1, 1]})
fig.patch.set_facecolor('#0a0a0f')
fig.suptitle('KESTREL MARKET SCAN — June 6, 2026', fontsize=20, fontweight='bold', color='#00ffcc', y=0.98)

colors = {'btc': '#f7931a', 'eth': '#8c8cff', 'sol': '#00c853'}
x = np.arange(len(btc_months))

for idx, (data, color, name, ath_val, ath_idx, ath_date, curr_val, pct) in enumerate([
    (btc_prices, colors['btc'], 'BITCOIN (BTC)', 124752, 4, 'Oct 6', 60901, 51),
    (eth_prices, colors['eth'], 'ETHEREUM (ETH)', 4779, 1, 'Aug 24', 1558, 67),
    (sol_prices, colors['sol'], 'SOLANA (SOL)', 232, 4, 'Oct 6', 61, 73),
]):
    ax = axes[idx, 0]
    ax.set_facecolor('#111118')
    ax.plot(x, data, color=color, linewidth=2.5, marker='o', markersize=5, zorder=3)
    ax.fill_between(x, data, min(data)*0.85, alpha=0.15, color=color)
    ax.annotate(f'ATH: ${ath_val:,}\n({ath_date})', xy=(ath_idx, ath_val),
                xytext=(ath_idx + 1.5 if ath_idx < 8 else ath_idx - 4, ath_val * 1.15),
                arrowprops=dict(arrowstyle='->', color='#ff4444', lw=1.5),
                fontsize=9, color='#ff4444')
    ax.annotate(f'${curr_val:,}\n-{pct}%', xy=(12, curr_val),
                xytext=(9, curr_val * 1.4),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5),
                fontsize=10, color=color, fontweight='bold')
    ax.set_xticks(x[::2])
    ax.set_xticklabels(btc_months[::2], color='#666')
    ax.tick_params(colors='#666', labelsize=9)
    ax.set_ylabel('Price (USD)', color='#888', fontsize=10)
    ax.set_title(name, color=color, fontsize=13, fontweight='bold', pad=10)
    ax.grid(axis='y', alpha=0.15, color='#333')
    ax.set_ylim(min(data)*0.7, max(data)*1.3)

# Fear & Greed gauge
ax_fng = axes[0, 1]
ax_fng.set_facecolor('#111118')
ax_fng.set_xlim(0, 1)
ax_fng.set_ylim(0, 100)

theta = np.linspace(np.pi, 2*np.pi, 100)
r = 0.35
cx, cy = 0.5, 0.25
ax_fng.plot(cx + r*np.cos(theta), cy + r*np.sin(theta), color='#333', lw=12, zorder=1)

segments = [(0, 25, '#ff1744'), (25, 45, '#ff9100'), (45, 55, '#ffea00'), (55, 75, '#76ff03'), (75, 100, '#00e676')]
for start, end, color in segments:
    s = np.pi + (start/100)*np.pi
    e_rad = np.pi + (end/100)*np.pi
    t = np.linspace(s, e_rad, 20)
    ax_fng.plot(cx + r*np.cos(t), cy + r*np.sin(t), color=color, lw=12, zorder=2)

val_rad = np.pi + (12/100)*np.pi
ax_fng.plot([cx, cx + 0.28*np.cos(val_rad)], [cy, cy + 0.28*np.sin(val_rad)], color='#ffffff', lw=2.5, zorder=5)
ax_fng.plot(cx, cy, 'o', color='#ffffff', markersize=8, zorder=6)
ax_fng.plot(cx, cy, 'o', color='#ff1744', markersize=5, zorder=7)

ax_fng.text(0.5, 0.55, 'FEAR & GREED', fontsize=11, fontweight='bold', color='#888', ha='center', transform=ax_fng.transAxes)
ax_fng.text(0.5, 0.95, '12', fontsize=42, fontweight='bold', color='#ff1744', ha='center', transform=ax_fng.transAxes)
ax_fng.text(0.5, 0.85, 'EXTREME FEAR', fontsize=11, fontweight='bold', color='#ff1744', ha='center', transform=ax_fng.transAxes)
ax_fng.text(0.5, 0.75, '↓ from 47 (Neutral) last month', fontsize=8, color='#666', ha='center', transform=ax_fng.transAxes)
ax_fng.axis('off')

# S&P 500
ax_sp = axes[1, 1]
ax_sp.set_facecolor('#111118')
sp_values = [5400, 5700, 6200, 6400, 6700, 7100, 7383]
sp_x = np.arange(7)
ax_sp.plot(sp_x, sp_values, color='#4488ff', linewidth=2, marker='o', markersize=4)
ax_sp.fill_between(sp_x, sp_values, min(sp_values)*0.85, alpha=0.1, color='#4488ff')
ax_sp.set_xticks(sp_x[::2])
ax_sp.set_xticklabels(['Jun','Oct','Feb','Jun'], color='#666', fontsize=8)
ax_sp.tick_params(colors='#666')
ax_sp.grid(axis='y', alpha=0.1, color='#333')
ax_sp.text(0.5, 0.9, 'S&P 500', fontsize=11, fontweight='bold', color='#4488ff', ha='center', transform=ax_sp.transAxes)
ax_sp.text(0.5, 0.82, '7,383', fontsize=14, fontweight='bold', color='#ffffff', ha='center', transform=ax_sp.transAxes)
ax_sp.text(0.5, 0.76, '+36% YoY', fontsize=9, color='#76ff03', ha='center', transform=ax_sp.transAxes)
ax_sp.set_ylim(4500, 8000)

# Opportunities panel
ax_opp = axes[2, 1]
ax_opp.set_facecolor('#111118')
ax_opp.axis('off')
ax_opp.text(0.5, 0.9, 'SHORT-TERM OPPORTUNITIES', fontsize=10, fontweight='bold', color='#00ffcc', ha='center', transform=ax_opp.transAxes)
opps = ['HYPE — On-chain perp momentum','INJ — DeFi swing $8.50-$9.50',
        'NEAR — AI agent narrative','LIT — Identity narrative',
        'NOTV — +91% penny volume','SNBR — +36% sleep number']
for i, o in enumerate(opps):
    ax_opp.text(0.15, 0.75 - i*0.1, f'▸ {o}', fontsize=8, color='#ccc', transform=ax_opp.transAxes)
ax_opp.text(0.5, 0.05, 'Data: Yahoo Finance, AllPennyStocks, Mudrex | Jun 6, 2026', fontsize=7, color='#555', ha='center', transform=ax_opp.transAxes)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig('/home/synczus/kestrel-market-chart.png', dpi=150, facecolor='#0a0a0f')
print('✅ Chart saved!')
