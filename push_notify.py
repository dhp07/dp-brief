#!/usr/bin/env python3
import json, sys
from pywebpush import webpush, WebPushException
sub=json.load(open('subscription.json'))
title=sys.argv[1] if len(sys.argv)>1 else "The DP Brief"
body=sys.argv[2] if len(sys.argv)>2 else "A new edition is ready."
url=sys.argv[3] if len(sys.argv)>3 else "https://dhp07.github.io/dp-brief/"
try:
    r=webpush(subscription_info=sub,
              data=json.dumps({"title":title,"body":body,"url":url}),
              vapid_private_key="vapid_private.pem",
              vapid_claims={"sub":"mailto:devhpatel07@gmail.com"})
    print("PUSH ->", r.status_code)
except WebPushException as e:
    print("PUSH FAILED ->", repr(e))
    if getattr(e,'response',None) is not None:
        print("response:", e.response.status_code, e.response.text[:300])
    sys.exit(1)
