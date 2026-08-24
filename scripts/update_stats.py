import urllib.request
import json
import os
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_github_data(username):
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. User info
    user_url = f"https://api.github.com/users/{username}"
    req = urllib.request.Request(user_url, headers=headers)
    with urllib.request.urlopen(req, context=ctx) as r:
        user = json.loads(r.read().decode('utf-8'))
        
    # 2. Repos info
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
    req_repos = urllib.request.Request(repos_url, headers=headers)
    with urllib.request.urlopen(req_repos, context=ctx) as r:
        repos = json.loads(r.read().decode('utf-8'))
        
    total_stars = sum(repo.get('stargazers_count', 0) for repo in repos if not repo.get('fork', False))
    total_forks = sum(repo.get('forks_count', 0) for repo in repos if not repo.get('fork', False))
    
    # Count languages
    lang_counts = {}
    for repo in repos:
        lang = repo.get('language')
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
            
    sorted_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
    total_lang_repos = sum(v for _, v in sorted_langs)
    
    lang_colors = {
        "Python": "#3572A5",
        "Rust": "#dea584",
        "C++": "#f34b7d",
        "C": "#555555",
        "TypeScript": "#3178c6",
        "JavaScript": "#f1e05a",
        "Dart": "#00B4AB",
        "Kotlin": "#A97BFF",
        "Shell": "#89e051",
        "HTML": "#e34c26",
        "CSS": "#563d7c"
    }
    
    lang_data = []
    for l, count in sorted_langs[:6]:
        pct = round((count / total_lang_repos) * 100, 1)
        color = lang_colors.get(l, "#58a6ff")
        lang_data.append({"name": l, "pct": pct, "color": color, "count": count})
        
    return {
        "name": user.get('name') or username,
        "username": username,
        "public_repos": len([r for r in repos if not r.get('fork', False)]),
        "total_stars": total_stars,
        "total_forks": total_forks,
        "followers": user.get('followers', 0),
        "langs": lang_data
    }

def generate_stats_svg(data, output_path):
    svg = f"""<svg width="340" height="195" viewBox="0 0 340 195" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;600;700;800&amp;display=swap');
    .title {{ font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 700; fill: #58a6ff; }}
    .label {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 500; fill: #8b949e; }}
    .value {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; fill: #f0f6fc; }}
  </style>
  <rect x="0.5" y="0.5" width="339" height="194" rx="10" fill="#0d1117" stroke="#30363d"/>
  
  <text x="25" y="32" class="title">GitHub Stats</text>
  
  <g transform="translate(25, 52)">
    <g transform="translate(0, 0)">
      <circle cx="6" cy="6" r="3" fill="#58a6ff" />
      <text x="18" y="10" class="label">Total Stars Earned:</text>
      <text x="280" y="10" class="value" text-anchor="end">{data['total_stars']}</text>
    </g>
    
    <g transform="translate(0, 26)">
      <circle cx="6" cy="6" r="3" fill="#58a6ff" />
      <text x="18" y="10" class="label">Public Repositories:</text>
      <text x="280" y="10" class="value" text-anchor="end">{data['public_repos']}</text>
    </g>

    <g transform="translate(0, 52)">
      <circle cx="6" cy="6" r="3" fill="#58a6ff" />
      <text x="18" y="10" class="label">Total Forks:</text>
      <text x="280" y="10" class="value" text-anchor="end">{data['total_forks']}</text>
    </g>

    <g transform="translate(0, 78)">
      <circle cx="6" cy="6" r="3" fill="#58a6ff" />
      <text x="18" y="10" class="label">Followers:</text>
      <text x="280" y="10" class="value" text-anchor="end">{data['followers']}</text>
    </g>

    <g transform="translate(0, 104)">
      <circle cx="6" cy="6" r="3" fill="#3fb950" />
      <text x="18" y="10" class="label">Status:</text>
      <text x="280" y="10" class="value" fill="#3fb950" text-anchor="end">Active Core</text>
    </g>
  </g>
</svg>"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("Generated", output_path)

def generate_langs_svg(data, output_path):
    bar_rects = []
    curr_x = 0
    total_w = 290
    for l in data['langs']:
        w = (l['pct'] / 100.0) * total_w
        bar_rects.append(f'<rect x="{curr_x}" y="0" width="{w}" height="8" rx="2" fill="{l["color"]}" />')
        curr_x += w
        
    items = []
    for idx, l in enumerate(data['langs']):
        col = idx % 2
        row = idx // 2
        x_pos = 25 if col == 0 else 170
        y_pos = 85 + (row * 24)
        items.append(f"""
        <g transform="translate({x_pos}, {y_pos})">
          <circle cx="5" cy="5" r="4" fill="{l['color']}" />
          <text x="15" y="9" class="lang-name">{l['name']}</text>
          <text x="120" y="9" class="lang-pct" text-anchor="end">{l['pct']}%</text>
        </g>
        """)
        
    svg = f"""<svg width="340" height="195" viewBox="0 0 340 195" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;600;700;800&amp;display=swap');
    .title {{ font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 700; fill: #58a6ff; }}
    .lang-name {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600; fill: #c9d1d9; }}
    .lang-pct {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 500; fill: #8b949e; }}
  </style>
  <rect x="0.5" y="0.5" width="339" height="194" rx="10" fill="#0d1117" stroke="#30363d"/>
  
  <text x="25" y="32" class="title">Top Languages</text>
  
  <g transform="translate(25, 48)">
    <rect x="0" y="0" width="290" height="8" rx="4" fill="#21262d" />
    <g clip-path="url(#bar_clip)">
      {' '.join(bar_rects)}
    </g>
    <clipPath id="bar_clip">
      <rect x="0" y="0" width="290" height="8" rx="4" />
    </clipPath>
  </g>

  {' '.join(items)}
</svg>"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("Generated", output_path)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    assets_dir = os.path.join(repo_root, "assets")
    
    d = fetch_github_data("imsudoer")
    generate_stats_svg(d, os.path.join(assets_dir, "github-stats.svg"))
    generate_langs_svg(d, os.path.join(assets_dir, "top-langs.svg"))
