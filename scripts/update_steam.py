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
                    status_color = "#90ba3c"
                elif raw_state == "online":
                    state = "Online"
                    status_color = "#57cbde"
                else:
                    state = "Offline"
                    status_color = "#8f98a0"
                    
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
        "avatar_b64": avatar_b64
    }

def generate_steam_svg(data, label, output_path):
    svg = f"""<svg width="380" height="130" viewBox="0 0 380 130" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg_{data['id']}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0a0e14"/>
      <stop offset="50%" stop-color="#121820"/>
      <stop offset="100%" stop-color="#1a2330"/>
    </linearGradient>
    <linearGradient id="border_{data['id']}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2a3f55" stop-opacity="0.8"/>
      <stop offset="50%" stop-color="#58a6ff" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#1f6feb" stop-opacity="0.1"/>
    </linearGradient>
    <clipPath id="avatar_clip_{data['id']}">
      <rect x="16" y="18" width="94" height="94" rx="10" />
    </clipPath>
  </defs>

  <rect x="1" y="1" width="378" height="128" rx="12" fill="url(#bg_{data['id']})" stroke="url(#border_{data['id']})" stroke-width="1.2" />

  <rect x="14" y="16" width="98" height="98" rx="12" fill="none" stroke="{data['status_color']}" stroke-width="2" />
  <image href="{data['avatar_b64']}" x="16" y="18" width="94" height="94" clip-path="url(#avatar_clip_{data['id']})" preserveAspectRatio="xMidYMid slice" />

  <g transform="translate(338, 14)">
    <path d="M14.9 0C6.7 0 0 6.7 0 14.9C0 21.6 4.5 27.2 10.7 29L15.3 22.4C14.7 22.1 14.1 21.5 13.8 20.8L8.6 22.9C8.6 22.9 6.2 17.5 9.8 14.3C10.7 13.5 11.9 13.1 13.1 13.2L16.2 8.7C16.2 5.5 18.8 2.9 22 2.9C25.3 2.9 27.9 5.5 27.9 8.8C27.9 12 25.3 14.6 22 14.6L17.7 17.7C17.7 18.6 17.4 19.5 16.9 20.2L21.3 26.5C27 24.3 31 18.8 31 12.3C29.8 5.5 23 0 14.9 0ZM22 5.2C24 5.2 25.6 6.8 25.6 8.8C25.6 10.8 24 12.4 22 12.4C20 12.4 18.4 10.8 18.4 8.8C18.4 6.8 20 5.2 22 5.2Z" fill="#58a6ff" opacity="0.4"/>
  </g>

  <text x="125" y="32" fill="#58a6ff" font-family="'Fira Code', monospace, sans-serif" font-size="10" font-weight="700" letter-spacing="1">{label.upper()}</text>

  <text x="125" y="52" fill="#ffffff" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="15" font-weight="700">
    {data['name'][:16]}
  </text>

  <circle cx="130" cy="71" r="4" fill="{data['status_color']}" />
  <text x="140" y="75" fill="{data['status_color']}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="600">
    {data['state']}
  </text>

  <g transform="translate(125, 88)">
    <rect x="0" y="0" width="70" height="24" rx="5" fill="#161b22" stroke="#30363d" stroke-width="1"/>
    <text x="7" y="16" fill="#8b949e" font-family="'Fira Code', monospace, sans-serif" font-size="10" font-weight="500">LVL</text>
    <text x="42" y="17" fill="#58a6ff" font-family="'Fira Code', monospace, sans-serif" font-size="12" font-weight="700">{data['level']}</text>

    <rect x="78" y="0" width="85" height="24" rx="5" fill="#161b22" stroke="#30363d" stroke-width="1"/>
    <text x="85" y="16" fill="#8b949e" font-family="'Fira Code', monospace, sans-serif" font-size="10" font-weight="500">GAMES</text>
    <text x="135" y="17" fill="#ffffff" font-family="'Fira Code', monospace, sans-serif" font-size="12" font-weight="700">{data['games']}</text>
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
    generate_steam_svg(d1, "Steam Main", os.path.join(assets_dir, "steam-main.svg"))
    
    d2 = fetch_steam_profile("iamsudoer", default_level="10", default_games="13")
    generate_steam_svg(d2, "Steam Alt", os.path.join(assets_dir, "steam-alt.svg"))
