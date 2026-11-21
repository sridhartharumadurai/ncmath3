#!/command/with-contenv sh
# s6-overlay cont-init hook (runs as root, after 01-hermes-setup and
# 02-reconcile-profiles, before user services). Pattern borrowed from the
# Caduceus desk (mywork/caduceus/docker/desk-cont-init.sh): the image owns
# PID 1; our only job is to render the MathBuddy profile into HERMES_HOME.
# Profile files must be written as the hermes user — Hermes refuses
# state writes as root ("unsafe_control_path").
set -e

BUNDLE=/opt/ncmath3-bundle
HERMES_BIN=/opt/hermes/bin/hermes
PROF="${HERMES_HOME:-/opt/data}/profiles/ncmath3"

if [ -f "$PROF/distribution.yaml" ]; then
    echo "[ncmath3] profile present — updating from bundle"
    # --force-config: the model/provider block is author-owned and re-rendered
    # below; installers' .env, memories and sessions are untouched by it.
    s6-setuidgid hermes "$HERMES_BIN" profile update ncmath3 -y --force-config \
        || echo "[ncmath3] update skipped/failed (install state stays)"
else
    echo "[ncmath3] installing profile from $BUNDLE"
    s6-setuidgid hermes "$HERMES_BIN" profile install "$BUNDLE" -y \
        || { echo "[ncmath3] profile install FAILED"; exit 1; }
fi

# Telegram + model keys arrive as container env (compose env_file). Hermes
# auto-enables the telegram adapter when TELEGRAM_BOT_TOKEN is present, and
# the OpenAI-compatible provider reads its *_API_KEY from the env — nothing
# else to render. Echo what is set WITHOUT values.
# Local model endpoint: re-render the profile's model block at every boot.
# The desktop app's llama.cpp supervisor port rotates per app session; compose
# passes the live value in NCMATH3_MODEL_URL (+ its key via NCMATH3_MODEL_KEY).
MODEL_URL="${NCMATH3_MODEL_URL:-http://192.168.65.254:52215/v1}"
echo "[ncmath3] model base_url -> $MODEL_URL"
sed -i -E "s@^  base_url: .*@  base_url: ${MODEL_URL}@" "$PROF/config.yaml"
if [ -n "${NCMATH3_MODEL_KEY:-}" ]; then
    sed -i -E "s@^  api_key: .*@  api_key: \"${NCMATH3_MODEL_KEY}\"@" "$PROF/config.yaml"
    echo "[ncmath3] model api_key rendered (supervisor key)"
fi

for v in TELEGRAM_BOT_TOKEN TELEGRAM_ALLOWED_USERS NCMATH3_MODEL_KEY; do
    if [ -n "$(printenv "$v")" ]; then echo "[ncmath3] env $v: set"; else echo "[ncmath3] env $v: MISSING"; fi
done
# The image enforces ONE host gateway, and inbound Telegram sessions run on
# the DEFAULT profile (session keys agent:main:telegram:*; `profile use` only
# affects CLI defaults — verified live 2026-11-20). This container is
# single-purpose, so the tutor must BE the default profile: render persona,
# skills and model into $HERMES_HOME, then mirror into the named profile for
# CLI use.
cp "$BUNDLE/SOUL.md" "${HERMES_HOME:-/opt/data}/SOUL.md"
mkdir -p "${HERMES_HOME:-/opt/data}/skills"
cp -R "$BUNDLE/skills/math3-tutor" "${HERMES_HOME:-/opt/data}/skills/"
for kv in "model.default Qwen3.8-Flash-Next-UD-IQ4_XS" \
          "model.provider custom" \
          "model.base_url ${MODEL_URL:-http://192.168.65.254:52215/v1}" \
          "model.api_key ${NCMATH3_MODEL_KEY:-}" \
          "model.context_length 262144"; do
    # -p default: `hermes config set` writes to the ACTIVE profile; the
    # gateway serves the default one (verified 2026-11-21).
    s6-setuidgid hermes "$HERMES_BIN" -p default config set $kv \
        || echo "[ncmath3] config set ${kv%% *} FAILED"
done
# progress.jsonl target dir: created early so the tutor appends to an
# existing dir and the read-only UI mount can list it
mkdir -p "${HERMES_HOME:-/opt/data}/workspace"
chown hermes:hermes "${HERMES_HOME:-/opt/data}/workspace"

echo "[ncmath3] default profile rendered with tutor persona + local model"

echo "[ncmath3] profile ready at $PROF"
