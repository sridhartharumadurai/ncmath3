# MathBuddy — Hermes Profile Distribution

A complete Hermes agent: a Socratic Telegram tutor for **Open Up HS Math 3
(North Carolina)** — 10 units, 78 lessons (mapped in
`skills/math3-tutor/references/syllabus.json`).

Installs as its own profile: separate memory (it remembers *him* — weak
topics, last lesson), own config, own gateway. Your other Hermes profiles are
untouched.

## Install (from this local directory)
```bash
hermes profile install /Users/stharumadurai/mywork/ncmath3 --alias
ncmath3 model           # pick provider + model, store the API key
```
Then add to `~/.hermes/profiles/ncmath3/.env` (the installer writes an
`.env.EXAMPLE` with the keys commented out):
```
TELEGRAM_BOT_TOKEN=*** from @BotFather>
TELEGRAM_ALLOWED_USERS=<your-telegram-id>,<sons-telegram-id>
```
User IDs: message @userinfobot on Telegram.

## Run it (two ways)

### A. Docker container (caduceus-style appliance) — recommended
```bash
# 1. create .env from .env.example (owner-only), fill token, user IDs, model key
docker compose up -d --build
docker compose logs -f      # "[mathbuddy] profile ready" + "Hermes Gateway Starting"
```
This builds on the **official `nousresearch/hermes-agent` appliance image**:
s6-overlay supervises everything; a boot hook (`docker/ncmath3-cont-init.sh`)
installs/updates this very directory as the `mathbuddy` profile into the
`ncmath3-data` volume and makes it the active profile. The container runs
ONE multiplexed host gateway (image-enforced: one gateway per host serves all
profiles — verified 2026-11-20). No published ports: Telegram is outbound
long-polling. Memories/sessions/pairing persist in the volume across rebuilds;
edit `SOUL.md`, rebuild, and the hook updates the profile in place.

Smoke-tested with placeholder credentials: hook installs the profile, gateway
boots under s6, the Telegram adapter activates from `TELEGRAM_BOT_TOKEN` and
correctly refuses to connect on a fake token.

### B. Local profile (no Docker)
```bash
ncmath3 gateway start
```
Chat with it in Telegram. The bot profile shows Online/Offline automatically.

## What ships
| Path | Role |
|---|---|
| `distribution.yaml` | manifest + `env_requires` (install-time checklist) |
| `SOUL.md` | tutor persona: hint ladder, no-answer-first rules, full 78-lesson index, Telegram etiquette |
| `config.yaml` | model defaults, memory on, max_turns 20, telegram extras |
| `skills/math3-tutor/` | quiz / EOC drill / progress digest workflows + syllabus reference |
| `.gitignore` | the distribution-safe set (secrets, sessions, state never ship) |

## Update flow
Bump `version:` here and push; installers run `hermes profile update ncmath3`
— their memories, sessions, and keys stay put.

## Two ways to deploy the same tutor
This distribution is the **Hermes-native** path (memory, skills, cron digests,
voice notes out of the box). The standalone container in `../mathbuddy/` is the
zero-dependency path. Do not run both against the same bot token at once —
Telegram delivers updates to a single poller (409 conflict).
