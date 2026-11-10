import os
import re
import json
import urllib.request

username = os.environ.get("GH_USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "LostDiscipleAkaza"
token = os.environ.get("TOKEN", "")

def fetch_graphql_stats(username, token):
    if not token:
        return None
    url = "https://api.github.com/graphql"
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
          }
        }
        repositories(privacy: PUBLIC) {
          totalCount
        }
        followers {
          totalCount
        }
      }
    }
    """
    req = urllib.request.Request(
        url,
        data=json.dumps({"query": query, "variables": {"login": username}}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "GitHub-Profile-Sync"
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            user_data = data.get("data", {}).get("user", {})
            contribs = user_data.get("contributionsCollection", {}).get("contributionCalendar", {}).get("totalContributions")
            repos = user_data.get("repositories", {}).get("totalCount")
            followers = user_data.get("followers", {}).get("totalCount")
            return contribs, repos, followers
    except Exception as e:
        print(f"GraphQL request error: {e}")
        return None

def fetch_rest_stats(username):
    url = f"https://api.github.com/users/{username}"
    req = urllib.request.Request(url, headers={"User-Agent": "GitHub-Profile-Sync"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("public_repos"), data.get("followers")
    except Exception as e:
        print(f"REST API error: {e}")
        return None, None

def update_stats_svg(contribs=None, repos=None, followers=None):
    svg_path = "stats.svg"
    if not os.path.exists(svg_path):
        return
    with open(svg_path, "r", encoding="utf-8") as f:
        content = f.read()

    if contribs is not None:
        content = re.sub(
            r'(Total Contributions:</text>\s*<text[^>]*>)\d+\+?(</text>)',
            rf'\g<1>{contribs}\g<2>',
            content
        )
    if repos is not None:
        content = re.sub(
            r'(Public Repositories:</text>\s*<text[^>]*>)\d+(</text>)',
            rf'\g<1>{repos}\g<2>',
            content
        )
    if followers is not None:
        content = re.sub(
            r'(Followers / Community:</text>\s*<text[^>]*>)\d+(</text>)',
            rf'\g<1>{followers}\g<2>',
            content
        )

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated stats.svg successfully")

def update_3d_svg(contribs=None):
    if contribs is None:
        return
    svg_path = os.path.join("profile-3d-contrib", "profile-custom-gitblock.svg")
    if not os.path.exists(svg_path):
        return
    with open(svg_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match the number before contributions
    content = re.sub(
        r'(<text style="font-size: 32px; font-weight: bold;" x="384" y="830" text-anchor="end" class="fill-strong">)\d+(</text><text style="font-size: 24px;" x="394" y="830" text-anchor="start" class="fill-fg">contributions</text>)',
        rf'\g<1>{contribs}\g<2>',
        content
    )

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated 3D SVG successfully")

def main():
    contribs, repos, followers = None, None, None
    if token:
        res = fetch_graphql_stats(username, token)
        if res:
            contribs, repos, followers = res

    # If GraphQL didn't fetch repos/followers or no token, fallback to REST
    rest_repos, rest_followers = fetch_rest_stats(username)
    if repos is None and rest_repos is not None:
        repos = rest_repos
    if followers is None and rest_followers is not None:
        followers = rest_followers

    print(f"Stats fetched: contribs={contribs}, repos={repos}, followers={followers}")

    # Only update if we have values
    if contribs or repos or followers:
        update_stats_svg(contribs, repos, followers)
    if contribs:
        update_3d_svg(contribs)

if __name__ == "__main__":
    main()
