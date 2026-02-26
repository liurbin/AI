import requests

DATABRICKS_HOST = "https://xxx.azuredatabricks.net"
DATABRICKS_TOKEN = ""  # <-- 请确认 Token 仍有效
MODEL = "databricks-claude-sonnet-4-6"

headers = {"Authorization": f"Bearer {DATABRICKS_TOKEN}"}

# ========== Step 1: 先验证 Token 是否有效 ==========
test = requests.get(
    f"{DATABRICKS_HOST}/api/2.0/serving-endpoints",
    headers=headers
)

# 先检查返回的是不是 HTML（说明 Token 失效被重定向到登录页）
if "<!doctype html>" in test.text.lower() or "<html" in test.text.lower():
    raise SystemExit("❌ Token 无效！返回的是登录页面。请去 Databricks UI → Settings → Developer → Access Tokens 重新生成 Token")

if test.status_code == 200:
    data = test.json()
    endpoints = data.get("endpoints", [])
    print(f"✅ Token 有效！共有 {len(endpoints)} 个 serving endpoint：")
    for ep in endpoints:
        print(f"   - {ep['name']}  (state: {ep.get('state', {}).get('ready', 'N/A')})")
elif test.status_code in (401, 403):
    raise SystemExit(f"❌ Token 无效或已过期 (HTTP {test.status_code})")
else:
    raise SystemExit(f"❌ 请求失败 (HTTP {test.status_code}): {test.text[:500]}")

# ========== Step 2: 调用模型 ==========
resp = requests.post(
    f"{DATABRICKS_HOST}/serving-endpoints/{MODEL}/invocations",
    headers={**headers, "Content-Type": "application/json"},
    json={
        "messages": [
            {"role": "system", "content": "你是一个专业的助手。"},
            {"role": "user", "content": "请用三句话介绍 Databricks Model Serving。"}
        ],
        "temperature": 0.2,
        "max_tokens": 300
    }
)

if resp.status_code == 200:
    result = resp.json()
    print("\n🤖 模型回答：")
    print(result["choices"][0]["message"]["content"])
else:
    print(f"❌ 调用失败 (HTTP {resp.status_code}): {resp.text[:500]}")
