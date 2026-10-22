## Verification

To prove CLI behavior of this repo offline, use the verification skill at `skills/verify-simple-ai-agent/SKILL.md` (also linked from `.cursor/skills/` and `.claude/skills/`):

```bash
export RUN_ID=$(date +%s)
skills/verify-simple-ai-agent/scripts/agentctl launch
skills/verify-simple-ai-agent/scripts/agentctl doctor
skills/verify-simple-ai-agent/scripts/agentctl journey fetch-ev-charger-growth
skills/verify-simple-ai-agent/scripts/agentctl cleanup
```

It mocks Open Charge Map and Marketstack at the httpx boundary, uses dummy keys and a scratch `data.csv`, and never calls OpenAI. Feature recipes are in `skills/verify-simple-ai-agent/features/`.
