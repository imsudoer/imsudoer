import urllib.request
import ssl
import re
import base64
import os
import html

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_steam_profile(custom_id, default_level="10", default_games="10+"):
    xml_url = f"https://steamcommunity.com/id/{custom_id}/?xml=1"
    req = urllib.request.Request(xml_url, headers={'User-Agent': 'Mozilla/5.0'})
    
    avatar_b64 = ""
    name = custom_id
    state = "Offline"
    level = default_level
    games = default_games
    status_color = "#6c757d"
    status_bg = "#6c757d22"
    
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
                    status_color = "#a3e635"
                    status_bg = "#a3e63522"
                elif raw_state == "online":
                    state = "Online"
                    status_color = "#38bdf8"
                    status_bg = "#38bdf822"
                else:
                    state = "Offline"
                    status_color = "#94a3b8"
                    status_bg = "#94a3b822"
                    
            avatar_m = re.search(r'<avatarFull><!\[CDATA\[(.*?)\]\]></avatarFull>', xml)
            if avatar_m:
                avatar_url = avatar_m.group(1)
                req_img = urllib.request.Request(avatar_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req_img, context=ctx, timeout=10) as r_img:
                    avatar_b64 = "data:image/jpeg;base64," + base64.b64encode(r_img.read()).decode('utf-8')
    except Exception as e:
        print(f"Error fetching XML for {custom_id}: {e}")
        
    try:
        html_url = f"https://steamcommunity.com/id/{custom_id}/"
        req2 = urllib.request.Request(html_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req2, context=ctx, timeout=10) as resp2:
            page = resp2.read().decode('utf-8', errors='ignore')
            lvl_m = re.search(r'<span class="friendPlayerLevelNum">(\\d+)</span>', page)
            if lvl_m:
                level = lvl_m.group(1)
            gms_m = re.search(r'href="https://steamcommunity\\.com/id/' + custom_id + r'/games/\\?tab=all"[^>]*>.*?<span class="profile_count_link_total">\\s*(\\d+)\\s*</span>', page, re.DOTALL)
            if gms_m:
                games = gms_m.group(1)
    except Exception as e:
        print(f"Error fetching HTML for {custom_id}: {e}")
        
    return {
        "id": custom_id,
        "name": name,
        "state": state,
        "level": level,
        "games": games,
        "status_color": status_color,
        "status_bg": status_bg,
        "avatar_b64": avatar_b64
    }

def generate_steam_svg(data, label, output_path):
    svg = f"""<svg width="410" height="140" viewBox="0 0 410 140" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700;800&amp;family=Plus+Jakarta+Sans:wght@600;700;800&amp;display=swap');
    .title {{
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
      font-weight: 800;
      font-size: 16px;
      fill: #f8fafc;
      letter-spacing: -0.2px;
    }}
    .tag {{
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      font-size: 10px;
      fill: #38bdf8;
      letter-spacing: 1.2px;
      text-transform: uppercase;
    }}
    .status {{
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
      font-size: 11px;
      fill: {data['status_color']};
    }}
    .stat-label {{
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
      font-size: 9px;
      fill: #64748b;
      letter-spacing: 0.8px;
    }}
    .stat-val {{
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      font-size: 12px;
      fill: #f1f5f9;
    }}
  </style>

  <defs>
    <!-- Background Gradient -->
    <linearGradient id="card_bg_{data['id']}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#090d16"/>
      <stop offset="60%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>

    <!-- Border Gradient -->
    <linearGradient id="card_border_{data['id']}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.6"/>
      <stop offset="50%" stop-color="#1e293b" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#0284c7" stop-opacity="0.2"/>
    </linearGradient>

    <!-- Glow Filter -->
    <filter id="glow_{data['id']}" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>

    <!-- Avatar Clip -->
    <clipPath id="clip_avatar_{data['id']}">
      <rect x="18" y="20" width="100" height="100" rx="14" />
    </clipPath>
  </defs>

  <!-- Card Body -->
  <rect x="1" y="1" width="408" height="138" rx="16" fill="url(#card_bg_{data['id']})" stroke="url(#card_border_{data['id']})" stroke-width="1.5" />

  <!-- Avatar Shadow & Border -->
  <rect x="16" y="18" width="104" height="104" rx="16" fill="none" stroke="{data['status_color']}" stroke-width="2" opacity="0.85" />
  <image href="{data['avatar_b64']}" x="18" y="20" width="100" height="100" clip-path="url(#clip_avatar_{data['id']})" preserveAspectRatio="xMidYMid slice" />

  <!-- Steam Logo Decorative -->
  <g transform="translate(365, 18)" opacity="0.4">
    <path d="M14.9 0C6.7 0 0 6.7 0 14.9C0 21.6 4.5 27.2 10.7 29L15.3 22.4C14.7 22.1 14.1 21.5 13.8 20.8L8.6 22.9C8.6 22.9 6.2 17.5 9.8 14.3C10.7 13.5 11.9 13.1 13.1 13.2L16.2 8.7C16.2 5.5 18.8 2.9 22 2.9C25.3 2.9 27.9 5.5 27.9 8.8C27.9 12 25.3 14.6 22 14.6L17.7 17.7C17.7 18.6 17.4 19.5 16.9 20.2L21.3 26.5C27 24.3 31 18.8 31 12.3C29.8 5.5 23 0 14.9 0ZM22 5.2C24 5.2 25.6 6.8 25.6 8.8C25.6 10.8 24 12.4 22 12.4C20 12.4 18.4 10.8 18.4 8.8C18.4 6.8 20 5.2 22 5.2Z" fill="#38bdf8"/>
  </g>

  <!-- Tag -->
  <text x="136" y="34" class="tag">{label}</text>

  <!-- Nickname -->
  <text x="136" y="56" class="title">{data['name'][:18]}</text>

  <!-- Status Pill -->
  <g transform="translate(136, 68)">
    <rect x="0" y="0" width="80" height="20" rx="10" fill="{data['status_bg']}" stroke="{data['status_color']}" stroke-width="1" opacity="0.8"/>
    <circle cx="10" cy="10" r="3.5" fill="{data['status_color']}" filter="url(#glow_{data['id']})" />
    <text x="20" y="14" class="status">{data['state']}</text>
  </g>

  <!-- Stats Grid -->
  <g transform="translate(136, 96)">
    <!-- Level Badge -->
    <rect x="0" y="0" width="76" height="26" rx="6" fill="#0f172a" stroke="#334155" stroke-width="1"/>
    <text x="8" y="17" class="stat-label">LVL</text>
    <text x="44" y="18" class="stat-val" fill="#38bdf8">{data['level']}</text>

    <!-- Games Count -->
    <rect x="84" y="0" width="96" height="26" rx="6" fill="#0f172a" stroke="#334155" stroke-width="1"/>
    <text x="92" y="17" class="stat-label">GAMES</text>
    <text x="145" y="18" class="stat-val">{data['games']}</text>
  </g>
</svg>"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Generated {output_path}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    assets_dir = os.path.join(repo_root, "assets")
    
    d1 = fetch_steam_profile("NoBanOnlyZXC", default_level="34", default_games="141")
    generate_steam_svg(d1, "Steam Main (CS2)", os.path.join(assets_dir, "steam-main.svg"))
    
    d2 = fetch_steam_profile("iamsudoer", default_level="10", default_games="13")
    generate_steam_svg(d2, "Steam Secondary", os.path.join(assets_dir, "steam-alt.svg"))
