import urllib.request
import ssl
import re
import base64
import os
import html

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_steam_full(custom_id, default_level="10", default_games="10"):
    xml_url = f"https://steamcommunity.com/id/{custom_id}/?xml=1"
    req = urllib.request.Request(xml_url, headers={'User-Agent': 'Mozilla/5.0'})
    
    avatar_b64 = ""
    name = custom_id
    state = "Offline"
    level = default_level
    games_count = default_games
    status_color = "#8b949e"
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            xml = resp.read().decode('utf-8', errors='ignore')
            name_m = re.search(r'<steamID><!\[CDATA\[(.*?)\]\]></steamID>', xml)
            if name_m:
                name = html.escape(name_m.group(1))
            
            state_m = re.search(r'<onlineState>(.*?)</onlineState>', xml)
            if state_m:
                raw_state = state_m.group(1).lower()
                if raw_state == "in-game":
                    state = "In-Game"
                    status_color = "#3fb950"
                elif raw_state == "online":
                    state = "Online"
                    status_color = "#58a6ff"
                else:
                    state = "Offline"
                    status_color = "#8b949e"
                    
            avatar_m = re.search(r'<avatarFull><!\[CDATA\[(.*?)\]\]></avatarFull>', xml)
            if avatar_m:
                avatar_url = avatar_m.group(1)
                req_img = urllib.request.Request(avatar_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req_img, context=ctx, timeout=10) as r_img:
                    avatar_b64 = "data:image/jpeg;base64," + base64.b64encode(r_img.read()).decode('utf-8')
    except Exception as e:
        print(f"Error fetching XML for {custom_id}: {e}")
        
    games_list = []
    try:
        html_url = f"https://steamcommunity.com/id/{custom_id}/"
        req2 = urllib.request.Request(html_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req2, context=ctx, timeout=10) as resp2:
            html_text = resp2.read().decode('utf-8', errors='ignore')
            
            lvl_m = re.search(r'<span class="friendPlayerLevelNum">(\\d+)</span>', html_text)
            if lvl_m:
                level = lvl_m.group(1)
            gms_m = re.search(r'href="https://steamcommunity\\.com/id/' + custom_id + r'/games/\\?tab=all"[^>]*>.*?<span class="profile_count_link_total">\\s*(\\d+)\\s*</span>', html_text, re.DOTALL)
            if gms_m:
                games_count = gms_m.group(1)
                
            names = re.findall(r'<div class="game_name">\\s*<a[^>]*>(.*?)</a>', html_text)
            details = re.findall(r'<div class="game_info_details">\\s*([\\d,.]+)\\s*hrs on record', html_text)
            for n, h in zip(names, details):
                clean_n = html.unescape(n.strip())
                games_list.append({"name": clean_n, "hours": f"{h} hrs"})
    except Exception as e:
        print(f"Error fetching HTML for {custom_id}: {e}")
        
    if not games_list:
        if custom_id == "NoBanOnlyZXC":
            games_list = [{"name": "Dota 2", "hours": "1,270 hrs"}, {"name": "Valheim", "hours": "138 hrs"}]
        else:
            games_list = [{"name": "Counter-Strike 2", "hours": "391 hrs"}]
            
    return {
        "id": custom_id,
        "name": name,
        "state": state,
        "level": level,
        "games_count": games_count,
        "status_color": status_color,
        "avatar_b64": avatar_b64,
        "games": games_list[:3]
    }

def generate_steam_github_svg(data, label, output_path):
    game_rows = []
    for idx, g in enumerate(data['games']):
        y = 120 + (idx * 22)
        game_rows.append(f"""
        <g transform="translate(25, {y})">
          <circle cx="4" cy="4" r="3" fill="#58a6ff" />
          <text x="16" y="8" class="game-name">{html.escape(g['name'][:22])}</text>
          <text x="290" y="8" class="game-hours" text-anchor="end">{g['hours']}</text>
        </g>
        """)
        
    svg = f"""<svg width="340" height="195" viewBox="0 0 340 195" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;600;700;800&amp;display=swap');
    .title {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; fill: #58a6ff; }}
    .status-text {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600; fill: {data['status_color']}; }}
    .nick {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; fill: #f0f6fc; }}
    .meta {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 500; fill: #8b949e; }}
    .sec-title {{ font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; fill: #8b949e; letter-spacing: 0.5px; text-transform: uppercase; }}
    .game-name {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600; fill: #c9d1d9; }}
    .game-hours {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 500; fill: #58a6ff; }}
  </style>

  <rect x="0.5" y="0.5" width="339" height="194" rx="10" fill="#0d1117" stroke="#30363d"/>

  <g transform="translate(25, 28)">
    <text x="0" y="0" class="title">Steam // {label}</text>
    <circle cx="286" cy="-4" r="3.5" fill="{data['status_color']}" />
    <text x="278" y="0" class="status-text" text-anchor="end">{data['state']}</text>
  </g>

  <g transform="translate(25, 42)">
    <clipPath id="avatar_clip_{data['id']}">
      <rect x="0" y="0" width="44" height="44" rx="8" />
    </clipPath>
    <rect x="0" y="0" width="44" height="44" rx="8" fill="#161b22" stroke="#30363d" />
    <image href="{data['avatar_b64']}" x="0" y="0" width="44" height="44" clip-path="url(#avatar_clip_{data['id']})" preserveAspectRatio="xMidYMid slice" />

    <text x="56" y="16" class="nick">{data['name'][:16]}</text>
    <text x="56" y="34" class="meta">Level {data['level']} • {data['games_count']} Games</text>
  </g>

  <line x1="25" y1="96" x2="315" y2="96" stroke="#21262d" stroke-width="1" />

  <text x="25" y="110" class="sec-title">Top Activity &amp; Playtime</text>

  {' '.join(game_rows)}
</svg>"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Generated {output_path}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    assets_dir = os.path.join(repo_root, "assets")
    
    d1 = fetch_steam_full("NoBanOnlyZXC", default_level="34", default_games="141")
    generate_steam_github_svg(d1, "Main", os.path.join(assets_dir, "steam-main.svg"))
    
    d2 = fetch_steam_full("iamsudoer", default_level="10", default_games="13")
    generate_steam_github_svg(d2, "Secondary", os.path.join(assets_dir, "steam-alt.svg"))
