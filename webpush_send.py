#!/usr/bin/env python3
"""Self-contained Web Push sender (RFC 8291 aes128gcm + RFC 8292 VAPID).
Usage: python3 webpush_send.py subscription.json vapid_private.pem "Title" "Body" "url"
Needs: cryptography. No pywebpush/http-ece dependency."""
import sys, os, json, struct, base64, time, urllib.request, urllib.error
from cryptography.hazmat.primitives.asymmetric import ec, utils as asym_utils
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF, HKDFExpand
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def b64u_dec(s):
    s=s+'='*((4-len(s)%4)%4); return base64.urlsafe_b64decode(s)
def b64u_enc(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()

def hkdf(salt, ikm, info, length):
    return HKDF(algorithm=hashes.SHA256(), length=length, salt=salt, info=info).derive(ikm)

def encrypt(payload, ua_public_b64, auth_b64):
    ua_public = b64u_dec(ua_public_b64)          # 65 bytes
    auth = b64u_dec(auth_b64)                     # 16 bytes
    as_priv = ec.generate_private_key(ec.SECP256R1())
    as_public = as_priv.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    ua_pub_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_public)
    shared = as_priv.exchange(ec.ECDH(), ua_pub_key)
    # RFC 8291: derive IKM
    key_info = b"WebPush: info\x00" + ua_public + as_public
    ikm = hkdf(auth, shared, key_info, 32)
    salt = os.urandom(16)
    cek = hkdf(salt, ikm, b"Content-Encoding: aes128gcm\x00", 16)
    nonce = hkdf(salt, ikm, b"Content-Encoding: nonce\x00", 12)
    plaintext = payload + b"\x02"                 # single-record last delimiter
    ct = AESGCM(cek).encrypt(nonce, plaintext, None)
    rs = 4096
    header = salt + struct.pack("!I", rs) + struct.pack("!B", len(as_public)) + as_public
    return header + ct

def vapid_header(endpoint, vapid_pem, sub_email="mailto:dp-brief@local"):
    from urllib.parse import urlparse
    u=urlparse(endpoint); aud=f"{u.scheme}://{u.netloc}"
    priv = serialization.load_pem_private_key(open(vapid_pem,'rb').read(), password=None)
    hdr = {"typ":"JWT","alg":"ES256"}
    payload = {"aud":aud, "exp":int(time.time())+12*3600, "sub":sub_email}
    seg = lambda d: b64u_enc(json.dumps(d,separators=(',',':')).encode())
    signing_input = (seg(hdr)+"."+seg(payload)).encode()
    der = priv.sign(signing_input, ec.ECDSA(hashes.SHA256()))
    r,s = asym_utils.decode_dss_signature(der)
    sig = r.to_bytes(32,'big')+s.to_bytes(32,'big')
    jwt = signing_input.decode()+"."+b64u_enc(sig)
    pub = priv.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return f"vapid t={jwt}, k={b64u_enc(pub)}"

def send(sub, vapid_pem, title, body, url):
    payload = json.dumps({"title":title,"body":body,"url":url}).encode()
    enc = encrypt(payload, sub["keys"]["p256dh"], sub["keys"]["auth"])
    req = urllib.request.Request(sub["endpoint"], data=enc, method="POST")
    req.add_header("Content-Encoding","aes128gcm")
    req.add_header("Content-Type","application/octet-stream")
    req.add_header("TTL","86400")
    req.add_header("Authorization", vapid_header(sub["endpoint"], vapid_pem))
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]

if __name__=="__main__":
    sub=json.load(open(sys.argv[1])); pem=sys.argv[2]
    title=sys.argv[3] if len(sys.argv)>3 else "The DP Brief"
    body=sys.argv[4] if len(sys.argv)>4 else "A new edition is ready."
    url=sys.argv[5] if len(sys.argv)>5 else "https://dhp07.github.io/dp-brief/"
    st,msg=send(sub,pem,title,body,url)
    print("PUSH ->", st, msg)
