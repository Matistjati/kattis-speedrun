import requests

def ping_user(user_id, problem, status):

    webhook_url = 'https://discord.com/api/webhooks/1380701487872868382/zaPPm3_mwWtNS31ru2NEeQ1Ru5HA0UQzkSSHbwDk3lUZ17OaGG0EZbNgJGJcmaNUdgUW'

    message = {
        "content": f"<@{user_id}> Judged **{problem}**! Verdict: **{status}**",
        "allowed_mentions": {
            "users": [str(user_id)]
        }
    }

    requests.post(webhook_url, json=message)
