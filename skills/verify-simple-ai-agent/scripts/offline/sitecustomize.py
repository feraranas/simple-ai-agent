"""Verification-only offline network boundary for simple-ai-agent.

Loaded via PYTHONPATH by agentctl. Every httpx client gets a MockTransport:
- api.openchargemap.io /v3/poi  -> generated POIs (DateCreated spread over recent months)
- api.marketstack.com  /v2/eod  -> generated daily closes
  (symbol VERIFY-EMPTY -> {"data": []}, to drive the "No data found" path)
- api.openai.com /v1/chat/completions -> refused (599) unless AGENT_VERIFY_FAKE_LLM=1, then a scripted
  fake model: first turn calls both fetch tools, second turn returns final_result with the Pearson
  correlation of the tool results (or AGENT_VERIFY_FAKE_LLM_CORRELATION if set). Not a real LLM.
- anything else                 -> refused (HTTP 599) so nothing leaves the box.
Every request is logged (API keys redacted) to $AGENT_VERIFY_NETLOG.
"""
import json, os, re, time
from datetime import datetime, timedelta, timezone
import httpx

LOG = os.environ.get("AGENT_VERIFY_NETLOG", "/tmp/agent-verify-net.log")

def _log(req, status, **extra):
    params = {k: ("<redacted>" if k in ("key", "access_key") else v) for k, v in req.url.params.items()}
    with open(LOG, "a") as f:
        f.write(json.dumps({"method": req.method, "host": req.url.host, "path": req.url.path, "params": params, "status": status, **extra}) + "\n")

def _pearson(xs, ys):
    n = min(len(xs), len(ys)); xs, ys = xs[:n], ys[:n]
    if n < 2: return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5; sy = sum((y - my) ** 2 for y in ys) ** 0.5
    return 0.0 if sx == 0 or sy == 0 else sxy / (sx * sy)

def _fake_llm(req):
    body = json.loads(req.content or b"{}")
    msgs = body.get("messages", [])
    tools = [t["function"]["name"] for t in body.get("tools", [])]
    user = " ".join(m.get("content") or "" for m in msgs if m.get("role") == "user" and isinstance(m.get("content"), str))
    months = int((re.search(r"months=(\d+)", user) or [0, 5])[1])
    symbol = (re.search(r"symbol=([A-Za-z0-9.-]+)", user) or [0, "PPLT"])[1]
    results = {}
    names = {c["id"]: c["function"]["name"] for m in msgs if m.get("role") == "assistant" for c in (m.get("tool_calls") or [])}
    for m in msgs:
        if m.get("role") == "tool":
            try: results[names.get(m.get("tool_call_id"), "?")] = json.loads(m.get("content") or "null")
            except ValueError: pass
    if "fetch_ev_charger_growth" not in results:
        calls = [("fetch_ev_charger_growth", {"months": months}), ("fetch_metals_prices", {"symbol": symbol, "months": months})]
        turn = "tools"
    else:
        ev, px = results.get("fetch_ev_charger_growth") or [], results.get("fetch_metals_prices") or []
        override = os.environ.get("AGENT_VERIFY_FAKE_LLM_CORRELATION")
        corr = float(override) if override else round(_pearson(ev, px), 6)
        final = next((t for t in tools if t not in ("fetch_ev_charger_growth", "fetch_metals_prices")), "final_result")
        calls = [(final, {"metals_etf_symbol": symbol, "correlation": corr, "recommendation": "verify fake LLM: scripted answer, not investment advice"})]
        turn = "final"
    msg = {"role": "assistant", "content": None, "tool_calls": [
        {"id": f"call_{turn}_{i}", "type": "function", "function": {"name": n, "arguments": json.dumps(a)}} for i, (n, a) in enumerate(calls)]}
    _log(req, 200, fake_llm=turn, tool_calls=[n for n, _ in calls])
    return httpx.Response(200, json={"id": f"chatcmpl-verify-{turn}", "object": "chat.completion", "created": int(time.time()),
        "model": body.get("model", "gpt-4o"), "choices": [{"index": 0, "message": msg, "finish_reason": "tool_calls"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}})

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
        if sym == "VERIFY-EMPTY":
            _log(req, 200, fixture="empty"); return httpx.Response(200, json={"pagination": {"count": 0}, "data": []})
        data = [{"symbol": sym, "close": round(100 + k * 0.5, 2), "date": (now - timedelta(days=100 - k)).strftime("%Y-%m-%dT00:00:00+0000")} for k in range(100)]
        _log(req, 200); return httpx.Response(200, json={"pagination": {"count": 100}, "data": data})
    if req.url.host == "api.openai.com" and req.url.path == "/v1/chat/completions" and os.environ.get("AGENT_VERIFY_FAKE_LLM") == "1":
        return _fake_llm(req)
    _log(req, 599); return httpx.Response(599, text="blocked by verify offline shim")

_orig_async = httpx.AsyncClient.__init__
_orig_sync = httpx.Client.__init__
def _async_init(self, *a, **kw):
    kw["transport"] = httpx.MockTransport(_handler); _orig_async(self, *a, **kw)
def _sync_init(self, *a, **kw):
    kw["transport"] = httpx.MockTransport(_handler); _orig_sync(self, *a, **kw)
httpx.AsyncClient.__init__ = _async_init
httpx.Client.__init__ = _sync_init
