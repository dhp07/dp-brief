#!/usr/bin/env python3
import json, os, sys
from pywebpush import webpush, WebPushException
STATE = ".notify_state"
ed = json.load(open('editions.json'))[0]
title   = (ed.get('notifyTitle') or "Morning Brief").strip()
summary = (ed.get('standfirst') or "A new edition is ready.").strip()
key = f"{ed.get('date')}|{title}"
last = open(STATE).read().strip() if os.path.exists(STATE) else ""
if key == last:
    print("Already notified for", key, "— skipping."); sys.exit(0)
url = "https://dhp07.github.io/dp-brief/"
try:
    r = webpush(subscription_info=json.load(open('subscription.json')),
                data=json.dumps({"title":title,"body":summary,"url":url}),
                vapid_private_key="vapid_private.pem",
                vapid_claims={"sub":"mailto:devhpatel07@gmail.com"})
    print("PUSH ->", r.status_code, "| key:", key)
    open(STATE,"w").write(key)
except WebPushException as e:
    print("PUSH FAILED ->", repr(e))
    if getattr(e,'response',None) is not None:
        print("response:", e.response.status_code, e.response.text[:300])
    sys.exit(1)
