from fastapi import FastAPI, Request
import requests
from config import FEISHU_WEBHOOK, GITHUB_TO_FEISHU

app = FastAPI(title="GitHub → Feishu Webhook")


def send_to_feishu(card: dict):
    requests.post(FEISHU_WEBHOOK, json=card)


def build_card(
    title: str,
    repo: str,
    author: str,
    base: str,
    head: str,
    url: str,
    color: str,
):
    elements = [
        {"tag": "markdown", "content": f"**仓库**：{repo}"},
        {"tag": "markdown", "content": f"**作者**：{author}"},
        {"tag": "markdown", "content": f"**源分支**：{head}"},
        {"tag": "markdown", "content": f"**目标分支**：{base}"},
        {"tag": "markdown", "content": f"🔗 **[查看 PR]({url})**"},
    ]

    # @ 发起人（如果配置）
    if author in GITHUB_TO_FEISHU:
        elements.append({
            "tag": "markdown",
            "content": f"<at id='{GITHUB_TO_FEISHU[author]}'></at>"
        })

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color
            },
            "elements": elements
        }
    }


@app.post("/github/webhook")
async def github_webhook(request: Request):
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")

    if event != "pull_request":
        return {"msg": "ignored"}

    action = payload.get("action")
    pr = payload.get("pull_request")

    repo = payload["repository"]["full_name"]
    title = pr["title"]
    author = pr["user"]["login"]
    base = pr["base"]["ref"]
    head = pr["head"]["ref"]
    url = pr["html_url"]

    # 事件判断
    if action == "opened":
        msg_title = "🆕 新建 Pull Request"
        color = "blue"
    elif action == "closed" and pr.get("merged"):
        msg_title = "✅ PR 已合并"
        color = "green"
    elif action == "closed":
        msg_title = "❌ PR 已关闭"
        color = "red"
    else:
        return {"msg": "ignored"}

    card = build_card(
        title=msg_title,
        repo=repo,
        author=author,
        base=base,
        head=head,
        url=url,
        color=color,
    )

    send_to_feishu(card)

    return {"msg": "ok"}

