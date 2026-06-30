#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成预测结果展示网页
从 prediction_archive/ 读取最新存档，生成 docs/index.html
"""

import json
import os
import glob
from datetime import datetime


def parse_archive(filepath):
    """解析存档文件，返回结构化数据"""
    data = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("{"):
                key, _, value = line.partition("=")
                data[key.strip()] = value.strip()

    tickets = []
    for i in range(1, 10):
        key = f"ticket{i}"
        if key not in data:
            break
        raw = data[key]
        parts = raw.split("|")
        nums_part = parts[0].strip()
        agents = parts[1].strip() if len(parts) > 1 else ""

        if "+" in nums_part:
            red_str, blue_str = nums_part.split("+")
            red_balls = [int(x) for x in red_str.split()]
            blue_ball = int(blue_str.strip())
        else:
            continue

        # 解析JSON explain
        json_key = f"ticket{i}_explain_json"
        explain = {}
        if json_key in data:
            try:
                explain = json.loads(data[json_key])
            except Exception:
                pass

        is_anti = "anti_consensus" in agents
        tickets.append({
            "index": i,
            "red_balls": red_balls,
            "blue_ball": blue_ball,
            "agents": agents,
            "is_anti": is_anti,
            "explain": explain,
        })

    # 解析 lead_summary
    lead = {}
    for part in data.get("lead_summary", "").split(";"):
        if "=" in part:
            k, _, v = part.partition("=")
            lead[k.strip()] = v.strip()

    return {
        "period": data.get("period", "未知"),
        "generated_at": data.get("generated_at", ""),
        "tickets": tickets,
        "lead": lead,
    }


def get_recent_archives(archive_dir, count=10):
    """获取最近N期存档文件（排除时间戳版本）"""
    files = glob.glob(os.path.join(archive_dir, "20?????.txt"))
    files = [f for f in files if "__" not in os.path.basename(f)]
    files.sort(reverse=True)
    return files[:count]


def render_ball(num, ball_type="red"):
    """渲染单个球的 HTML"""
    cls = "ball-red" if ball_type == "red" else "ball-blue"
    return f'<span class="{cls}">{num:02d}</span>'


def render_ticket(ticket, idx):
    """渲染一张票的卡片 HTML"""
    red_html = "".join(render_ball(b, "red") for b in ticket["red_balls"])
    blue_html = render_ball(ticket["blue_ball"], "blue")

    badge = ""
    if ticket["is_anti"]:
        badge = '<span class="badge badge-anti">反共识票</span>'
    else:
        agents_list = [a.strip() for a in ticket["agents"].split(",") if a.strip()]
        agent_tags = "".join(f'<span class="agent-tag">{a}</span>' for a in agents_list[:5])
        badge = f'<div class="agents">{agent_tags}</div>'

    # 红球贡献来源
    contrib_html = ""
    if ticket.get("explain") and ticket["explain"].get("red"):
        items = []
        for rb in ticket["explain"]["red"]:
            ball = rb.get("ball", "")
            agent = rb.get("top_agent", "")
            score = rb.get("top_contribution", 0)
            items.append(f'<span class="contrib">{ball:02d}<em>{agent}</em></span>')
        contrib_html = f'<div class="contrib-row">{"".join(items)}</div>'

    card_class = "ticket-card anti-card" if ticket["is_anti"] else "ticket-card"

    return f"""
    <div class="{card_class}">
      <div class="ticket-header">
        <span class="ticket-num">第 {idx} 注</span>
        {badge}
      </div>
      <div class="balls-row">
        {red_html}
        <span class="plus">+</span>
        {blue_html}
      </div>
      {contrib_html}
    </div>"""


def render_history_row(archive_data):
    """渲染历史记录行"""
    period = archive_data["period"]
    gen_at = archive_data["generated_at"][:10] if archive_data["generated_at"] else ""
    ticket_count = len(archive_data["tickets"])
    return f"""
    <tr>
      <td class="period-cell">{period}</td>
      <td>{gen_at}</td>
      <td>{ticket_count} 注</td>
      <td><a href="https://github.com/lgdglgc/letter-predictor/tree/main/prediction_archive/{period}.txt" target="_blank">查看详情 →</a></td>
    </tr>"""


def generate_html(archive_dir="prediction_archive", output="docs/index.html"):
    """主函数：生成 index.html"""
    files = get_recent_archives(archive_dir)
    if not files:
        print("未找到存档文件")
        return

    # 最新期
    latest = parse_archive(files[0])
    # 历史记录
    history = [parse_archive(f) for f in files[1:]]

    period = latest["period"]
    gen_at = latest["generated_at"]
    lead = latest["lead"]

    tickets_html = "\n".join(
        render_ticket(t, t["index"]) for t in latest["tickets"]
    )

    history_rows = "\n".join(render_history_row(h) for h in history)

    lead_agent = lead.get("领跑Agent", "-")
    team_health = lead.get("团队健康", "-")
    style_label = lead.get("report", "").replace("策略风格=", "").split(";")[0] if lead.get("report") else "-"

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>双色球预测 · {period}期</title>
  <meta name="description" content="双色球多专家团队预测系统，纯娱乐，理性购彩。">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg: #0f0f1a;
      --surface: #1a1a2e;
      --surface2: #16213e;
      --border: #2a2a4a;
      --text: #e2e8f0;
      --text-muted: #8892a4;
      --red: #ff4757;
      --red-glow: rgba(255,71,87,0.3);
      --blue: #3742fa;
      --blue-glow: rgba(55,66,250,0.4);
      --accent: #7c3aed;
      --accent2: #06b6d4;
      --gold: #f59e0b;
    }}

    body {{
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }}

    .bg-glow {{
      position: fixed; top: 0; left: 0; right: 0; height: 100vh;
      background: radial-gradient(ellipse 80% 50% at 50% -20%, rgba(124,58,237,0.15), transparent);
      pointer-events: none; z-index: 0;
    }}

    .container {{ max-width: 900px; margin: 0 auto; padding: 0 16px; position: relative; z-index: 1; }}

    /* Header */
    header {{
      padding: 40px 0 24px;
      text-align: center;
    }}
    .disclaimer {{
      display: inline-block;
      background: rgba(245,158,11,0.15);
      border: 1px solid rgba(245,158,11,0.4);
      color: var(--gold);
      font-size: 12px;
      padding: 4px 12px;
      border-radius: 20px;
      margin-bottom: 16px;
    }}
    header h1 {{
      font-size: clamp(24px, 5vw, 36px);
      font-weight: 700;
      background: linear-gradient(135deg, #a78bfa, #06b6d4);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 8px;
    }}
    .subtitle {{ color: var(--text-muted); font-size: 14px; }}

    /* Period badge */
    .period-info {{
      display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;
      margin: 24px 0;
    }}
    .info-chip {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 16px;
      font-size: 13px;
    }}
    .info-chip strong {{ color: var(--accent2); }}

    /* Stats row */
    .stats-row {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-bottom: 32px;
    }}
    .stat-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      text-align: center;
    }}
    .stat-label {{ font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }}
    .stat-value {{ font-size: 20px; font-weight: 700; color: var(--accent2); }}

    /* Section title */
    .section-title {{
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--text-muted);
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border);
    }}

    /* Ticket card */
    .tickets-grid {{ display: flex; flex-direction: column; gap: 14px; margin-bottom: 40px; }}
    .ticket-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 20px;
      transition: transform 0.2s, border-color 0.2s;
    }}
    .ticket-card:hover {{ transform: translateY(-2px); border-color: var(--accent); }}
    .anti-card {{ border-color: rgba(124,58,237,0.5); background: rgba(124,58,237,0.07); }}

    .ticket-header {{
      display: flex; align-items: center; gap: 10px; margin-bottom: 14px;
    }}
    .ticket-num {{ font-size: 12px; color: var(--text-muted); font-weight: 500; }}

    .balls-row {{
      display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 10px;
    }}
    .ball-red, .ball-blue {{
      width: 40px; height: 40px;
      border-radius: 50%;
      display: inline-flex; align-items: center; justify-content: center;
      font-family: 'JetBrains Mono', monospace;
      font-size: 14px; font-weight: 600;
      flex-shrink: 0;
    }}
    .ball-red {{
      background: radial-gradient(circle at 35% 35%, #ff6b7a, #cc0000);
      color: white;
      box-shadow: 0 2px 8px var(--red-glow);
    }}
    .ball-blue {{
      background: radial-gradient(circle at 35% 35%, #5563ff, #1a28d4);
      color: white;
      box-shadow: 0 2px 12px var(--blue-glow);
    }}
    .plus {{ color: var(--text-muted); font-size: 18px; font-weight: 300; }}

    /* badges */
    .badge {{ font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: 500; }}
    .badge-anti {{ background: rgba(124,58,237,0.25); color: #a78bfa; border: 1px solid rgba(124,58,237,0.4); }}
    .agents {{ display: flex; gap: 4px; flex-wrap: wrap; }}
    .agent-tag {{
      font-size: 10px; padding: 2px 7px; border-radius: 5px;
      background: rgba(6,182,212,0.12); color: var(--accent2);
      border: 1px solid rgba(6,182,212,0.25);
    }}

    /* contrib */
    .contrib-row {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }}
    .contrib {{
      font-size: 11px; background: rgba(255,255,255,0.05);
      border-radius: 5px; padding: 2px 7px; color: var(--text-muted);
    }}
    .contrib em {{ font-style: normal; color: var(--accent2); margin-left: 3px; }}

    /* History table */
    .history-table {{ width: 100%; border-collapse: collapse; margin-bottom: 40px; font-size: 13px; }}
    .history-table th {{
      text-align: left; padding: 10px 12px;
      color: var(--text-muted); font-weight: 500;
      border-bottom: 1px solid var(--border);
    }}
    .history-table td {{ padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.04); }}
    .history-table tr:hover td {{ background: rgba(255,255,255,0.02); }}
    .period-cell {{ font-family: 'JetBrains Mono', monospace; color: var(--accent2); }}
    .history-table a {{ color: var(--text-muted); text-decoration: none; }}
    .history-table a:hover {{ color: var(--accent2); }}

    /* Footer */
    footer {{
      text-align: center; padding: 32px 0;
      color: var(--text-muted); font-size: 12px;
      border-top: 1px solid var(--border);
    }}
    footer p {{ margin-bottom: 4px; }}

    @media (max-width: 600px) {{
      .stats-row {{ grid-template-columns: repeat(3, 1fr); gap: 8px; }}
      .ball-red, .ball-blue {{ width: 34px; height: 34px; font-size: 12px; }}
      .balls-row {{ gap: 5px; }}
    }}
  </style>
</head>
<body>
<div class="bg-glow"></div>
<div class="container">

  <header>
    <div class="disclaimer">⚠️ 纯娱乐工具 · 彩票完全随机 · 理性购彩</div>
    <h1>双色球多专家预测系统</h1>
    <p class="subtitle">8 专家团队协同 · 反共识辩论 · 自学习优化</p>
  </header>

  <div class="period-info">
    <div class="info-chip">🎯 预测期号：<strong>{period}</strong></div>
    <div class="info-chip">🕐 生成时间：<strong>{gen_at}</strong></div>
    <div class="info-chip">🏆 领跑专家：<strong>{lead_agent}</strong></div>
  </div>

  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-label">团队状态</div>
      <div class="stat-value">{team_health}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">策略风格</div>
      <div class="stat-value" style="font-size:14px">{style_label}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">出票数量</div>
      <div class="stat-value">{len(latest["tickets"])} 注</div>
    </div>
  </div>

  <div class="section-title">本期预测票</div>
  <div class="tickets-grid">
    {tickets_html}
  </div>

  <div class="section-title">历史预测记录</div>
  <table class="history-table">
    <thead>
      <tr>
        <th>期号</th><th>生成日期</th><th>票数</th><th>存档</th>
      </tr>
    </thead>
    <tbody>
      {history_rows}
    </tbody>
  </table>

  <footer>
    <p>⚠️ 本工具仅供娱乐和学习，不构成任何投资建议。彩票开奖完全随机，历史统计不具备预测效力。</p>
    <p>页面自动更新于 {now_str} · <a href="https://github.com/lgdglgc/letter-predictor" style="color:inherit">GitHub 仓库</a></p>
  </footer>

</div>
</body>
</html>"""

    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成网页: {output}")


if __name__ == "__main__":
    generate_html()
