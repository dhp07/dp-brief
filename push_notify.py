#!/usr/bin/env python3
import json, sys
from pywebpush import webpush, WebPushException
ed = json.load(open('editions.json'))[0]
title = (ed.get('label') or "Morning Brief").strip()      # short bold title (e.g., "Wed · Jul 22")
summary = (ed.get('standfirst') or "A new edition is ready.").strip()
url = "https://dhp07.github.io/dp-brief/"
try:
    r = webpush(subscription_info=json.load(open('subscription.json')),
                data=json.dumps({"title":title,"body":summary,"url":url}),
                vapid_private_key="vapid_private.pem",
                vapid_claims={"sub":"mailto:devhpatel07@gmail.com"})
    print("PUSH ->", r.status_code, "| title:", title)
except WebPushException as e:
    print("PUSH FAILED ->", repr(e))
    if getattr(e,'response',None) is not None:
        print("response:", e.response.status_code, e.response.text[:300])
    sys.exit(1)
