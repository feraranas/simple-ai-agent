"""Verification-only offline network boundary for simple-ai-agent.

Loaded via PYTHONPATH by agentctl. Every httpx client gets a MockTransport:
- api.openchargemap.io /v3/poi  -> generated POIs (DateCreated spread over recent months)
- api.marketstack.com  /v2/eod  -> generated daily closes
- anything else                 -> refused (HTTP 599) so nothing leaves the box.
Every request is logged (API keys redacted) to $AGENT_VERIFY_NETLOG.
"""
import json, os
from datetime import datetime, timedelta, timezone
import httpx

LOG = os.environ.get("AGENT_VERIFY_NETLOG", "/tmp/agent-verify-net.log")

def _log(req, status):
    params = {k: ("<redacted>" if k in ("key", "access_key") else v) for k, v in req.url.params.items()}
    with open(LOG, "a") as f:
        f.write(json.dumps({"method": req.method, "host": req.url.host, "path": req.url.path, "params": params, "status": status}) + "\n")

def _handler(req):
    now = datetime.now(timezone.utc)
    if req.url.host == "api.openchargemap.io" and req.url.path == "/v3/poi":
        # month i ago gets (i+1)*2 POIs -> deterministic counts
        pois = []
        for i in range(5):
            for j in range((i + 1) * 2):
                d = (now - timedelta(days=30 * i)).replace(hour=0, minute=0, second=0, microsecond=0)
                pois.append({"ID": len(pois) + 1, "DateCreated": d.strftime("%Y-%m-%dT%H:%M:%SZ")})
        _log(req, 200); return httpx.Response(200, json=pois)
    if req.url.host == "api.marketstack.com" and req.url.path == "/v2/eod":
        sym = req.url.params.get("symbols", "X")
        data = [{"symbol": sym, "close": round(100 + k * 0.5, 2), "date": (now - timedelta(days=100 - k)).strftime("%Y-%m-%dT00:00:00+0000")} for k in range(100)]
        _log(req, 200); return httpx.Response(200, json={"pagination": {"count": 100}, "data": data})
    _log(req, 599); return httpx.Response(599, text="blocked by verify offline shim")

_orig_async = httpx.AsyncClient.__init__
_orig_sync = httpx.Client.__init__
def _async_init(self, *a, **kw):
    kw["transport"] = httpx.MockTransport(_handler); _orig_async(self, *a, **kw)
def _sync_init(self, *a, **kw):
    kw["transport"] = httpx.MockTransport(_handler); _orig_sync(self, *a, **kw)
httpx.AsyncClient.__init__ = _async_init
httpx.Client.__init__ = _sync_init
