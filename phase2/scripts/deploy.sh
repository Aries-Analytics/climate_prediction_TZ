#!/usr/bin/env bash
# =============================================================
#  HewaSense — Deployment Framework
#
#  Usage:
#    ./scripts/deploy.sh                       List available profiles
#    ./scripts/deploy.sh <profile>             Auto-detect init vs update
#    ./scripts/deploy.sh <profile> --init      First-time full setup
#    ./scripts/deploy.sh <profile> --update    Pull latest + restart
#
#  Works from any machine that has a clone of this repo and
#  SSH access to the server. No local secrets required.
# =============================================================
set -euo pipefail

# ── Server target (same for all profiles) ──────────────────
SERVER_USER=root
SERVER_HOST=37.27.200.227
SERVER_DOMAIN=hewasense.majaribio.com
SERVER="${SERVER_USER}@${SERVER_HOST}"
REPO_CLONE_DIR="/opt/hewasense/app"      # git clone lands here

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILES_DIR="${SCRIPT_DIR}/deploy/profiles"

# ── Colours ────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()     { echo -e "${GREEN}  ✓  ${NC} $*"; }
info()   { echo -e "${CYAN}  →  ${NC} $*"; }
warn()   { echo -e "${YELLOW}  !  ${NC} $*"; }
fail()   { echo -e "${RED}  ✗  ${NC} $*" >&2; exit 1; }
ask()    { echo -e "${YELLOW}  ?  ${NC} $*"; }
banner() { echo -e "\n${BOLD}${CYAN}─── $* ───${NC}"; }

# ── SSH helper ─────────────────────────────────────────────
ssh_run() {
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 "${SERVER}" "$@"
}

# ── List available profiles ────────────────────────────────
list_profiles() {
  echo -e "\n${BOLD}Available deployment profiles:${NC}\n"
  for f in "${PROFILES_DIR}"/*.env; do
    [[ -f "$f" ]] || continue
    local name desc
    name=$(basename "$f" .env)
    desc=$(grep '^PROFILE_DESCRIPTION=' "$f" | cut -d= -f2- | tr -d '"')
    printf "  ${CYAN}%-18s${NC}%s\n" "$name" "$desc"
  done
  echo -e "\n${BOLD}Usage:${NC}  ./scripts/deploy.sh <profile> [--init|--update]\n"
}

# ── Parse arguments ────────────────────────────────────────
PROFILE=""
MODE=""
for arg in "$@"; do
  case "$arg" in
    --init)   MODE=init ;;
    --update) MODE=update ;;
    --*)      fail "Unknown flag: $arg" ;;
    *)        PROFILE="$arg" ;;
  esac
done

if [[ -z "$PROFILE" ]]; then
  list_profiles
  exit 0
fi

# ── Load profile ───────────────────────────────────────────
PROFILE_FILE="${PROFILES_DIR}/${PROFILE}.env"
[[ -f "$PROFILE_FILE" ]] || fail "Profile not found: '${PROFILE}'. Run without args to list profiles."
# shellcheck source=/dev/null
source "$PROFILE_FILE"

echo -e "\n${BOLD}HewaSense Deployment Framework${NC}"
echo -e "  Profile  : ${CYAN}${PROFILE_NAME}${NC} — ${PROFILE_DESCRIPTION}"
echo -e "  Server   : ${SERVER_HOST} (${SERVER_DOMAIN})"
echo -e "  Branch   : ${BRANCH}"
echo -e "  Schedule : ${PIPELINE_SCHEDULE}"
echo ""

# ── Auto-detect mode ───────────────────────────────────────
if [[ -z "$MODE" ]]; then
  if ssh_run "test -d ${REMOTE_DIR}" 2>/dev/null; then
    MODE=update
    info "Existing deployment found — running update"
  else
    MODE=init
    info "No existing deployment — running first-time init"
  fi
fi

# =============================================================
# SHARED: Health check
# =============================================================
health_check() {
  banner "Health check"
  info "Waiting for containers to stabilise (up to 90s)..."

  local elapsed=0
  while [[ $elapsed -lt 90 ]]; do
    local up
    up=$(ssh_run "cd ${REMOTE_DIR} && docker compose -f ${COMPOSE_FILE} ps --services --filter status=running 2>/dev/null | wc -l" || echo 0)
    [[ "$up" -ge 5 ]] && break
    sleep 5; elapsed=$((elapsed + 5))
    echo -ne "  ${elapsed}s elapsed...\r"
  done
  echo ""

  ssh_run "cd ${REMOTE_DIR} && docker compose -f ${COMPOSE_FILE} ps"
  echo ""

  local running
  running=$(ssh_run "cd ${REMOTE_DIR} && docker compose -f ${COMPOSE_FILE} ps --services --filter status=running 2>/dev/null | wc -l" || echo 0)
  if [[ "$running" -ge 5 ]]; then
    ok "All ${running} containers running"
  else
    warn "${running}/5 containers running — check logs:"
    warn "  ssh ${SERVER} \"cd ${REMOTE_DIR} && docker compose -f ${COMPOSE_FILE} logs --tail 50\""
  fi
}

# =============================================================
# SHARED: Slack deployment ping (Option C — deployment event,
#         not a forecast result; confirms webhook works)
# =============================================================
send_slack_ping() {
  local webhook="${DEPLOY_SLACK_WEBHOOK:-}"

  # Fall back to reading from the server .env if not already set
  if [[ -z "$webhook" ]]; then
    webhook=$(ssh_run "grep -m1 '^ALERT_SLACK_WEBHOOK_URL=' ${REMOTE_DIR}/.env 2>/dev/null | cut -d= -f2-" || true)
  fi

  if [[ -z "$webhook" ]]; then
    warn "No Slack webhook found — skipping deployment ping"
    return
  fi

  info "Sending Slack deployment notification..."
  local msg
  msg="*HewaSense [${PROFILE_NAME}] deployed* :rocket:
Server: \`${SERVER_HOST}\` (${SERVER_DOMAIN})
Branch: \`${BRANCH}\`
Schedule: \`${PIPELINE_SCHEDULE}\` (Africa/Dar_es_Salaam)
Dashboard: http://${SERVER_DOMAIN}:${PORT_DASHBOARD}
_This is a deployment event, not a forecast result._"

  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$webhook" \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"${msg}\"}")

  if [[ "$http_code" == "200" ]]; then
    ok "Slack ping sent — webhook confirmed working"
  else
    warn "Slack ping returned HTTP ${http_code} — check ALERT_SLACK_WEBHOOK_URL in server .env"
  fi
}

# =============================================================
# SHARED: Summary
# =============================================================
print_summary() {
  echo ""
  echo -e "${BOLD}${GREEN}══════════════════════════════════════════════════${NC}"
  echo -e "${BOLD}${GREEN}  [${PROFILE_NAME}] DEPLOYMENT COMPLETE${NC}"
  echo -e "${BOLD}${GREEN}══════════════════════════════════════════════════${NC}"
  echo -e "  Dashboard  : ${CYAN}http://${SERVER_DOMAIN}:${PORT_DASHBOARD}${NC}"
  echo -e "  API docs   : ${CYAN}http://${SERVER_DOMAIN}:${PORT_API}/docs${NC}"
  echo -e "  Branch     : ${BRANCH}"
  echo -e "  Schedule   : ${PIPELINE_SCHEDULE} (Africa/Dar_es_Salaam)"
  echo ""
  echo -e "  ${BOLD}Useful commands:${NC}"
  echo -e "  Logs   : ssh ${SERVER} \"docker logs climate_pipeline_scheduler_dev -f --tail 100\""
  echo -e "  Status : ssh ${SERVER} \"cd ${REMOTE_DIR} && docker compose -f ${COMPOSE_FILE} ps\""
  echo -e "  Down   : ssh ${SERVER} \"cd ${REMOTE_DIR} && docker compose -f ${COMPOSE_FILE} down\""
  echo ""
  echo -e "  ${YELLOW}Local scheduler is paused — keep it that way.${NC}"
  echo -e "  ${YELLOW}All forecasts now run on the server at ${PIPELINE_SCHEDULE} EAT.${NC}"
  echo -e "${BOLD}${GREEN}══════════════════════════════════════════════════${NC}"
  echo ""
}

# =============================================================
# INIT MODE — First-time full setup
# =============================================================
run_init() {

  # ── Step 1: Pre-flight ─────────────────────────────────
  banner "STEP 1/7  Pre-flight checks"
  command -v ssh  >/dev/null || fail "ssh not found on this machine"
  command -v curl >/dev/null || fail "curl not found on this machine"
  ok "Local tools present: ssh, curl"

  info "Testing SSH connection to ${SERVER}..."
  ssh_run "echo ok" >/dev/null \
    || fail "Cannot SSH to ${SERVER}. Make sure your public key is in the server's authorized_keys."
  ok "SSH connection: ${SERVER}"

  # ── Step 2: Clone repository (public repo — no auth needed) ──
  banner "STEP 2/6  Clone repository"

  # Derive HTTPS URL from local git remote (works for both SSH and HTTPS remotes)
  local raw_url
  raw_url=$(git -C "$(dirname "$SCRIPT_DIR")" remote get-url origin 2>/dev/null || true)
  # Convert SSH format (git@github.com:org/repo.git) to HTTPS if needed
  REPO_URL=$(echo "$raw_url" | sed 's|git@github.com:|https://github.com/|')
  [[ -z "$REPO_URL" ]] && fail "Could not determine repo URL from git remote. Run from inside the repo."
  info "Repo URL: ${REPO_URL}"

  ssh_run "mkdir -p $(dirname "${REPO_CLONE_DIR}")"
  info "Cloning → ${REPO_CLONE_DIR} ..."
  ssh_run "git clone ${REPO_URL} ${REPO_CLONE_DIR}"
  ok "Repository cloned"

  info "Checking out branch: ${BRANCH}"
  ssh_run "cd ${REPO_CLONE_DIR} && git checkout ${BRANCH}"
  ok "Branch: ${BRANCH}"

  # ── Step 4: Configure secrets (.env) ──────────────────
  banner "STEP 3/6  Configure secrets"

  if ssh_run "test -f ${REMOTE_DIR}/.env" 2>/dev/null; then
    warn ".env already exists on server"
    ask "Overwrite it? [y/N]: "
    read -r overwrite
    [[ "${overwrite,,}" != "y" ]] && { info "Keeping existing .env"; }
  fi

  if [[ "${overwrite,,:-n}" == "y" ]] || ! ssh_run "test -f ${REMOTE_DIR}/.env" 2>/dev/null; then
    echo ""
    ask "Slack webhook URL (ALERT_SLACK_WEBHOOK_URL): "
    read -r SLACK_WEBHOOK
    [[ -z "$SLACK_WEBHOOK" ]] && fail "Slack webhook URL is required"

    ask "ERA5 / ECMWF API key (ERA5_API_KEY): "
    read -r ERA5_KEY
    [[ -z "$ERA5_KEY" ]] && fail "ERA5 API key is required"

    ask "NASA API key (NASA_API_KEY) [press Enter to use DEMO_KEY]: "
    read -r NASA_KEY
    NASA_KEY="${NASA_KEY:-DEMO_KEY}"

    info "Writing .env to server..."
    printf '%s\n' \
      "# HewaSense server .env — generated by deploy.sh on $(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      "# Do NOT commit this file to git." \
      "" \
      "# Slack alerts" \
      "ALERT_SLACK_ENABLED=true" \
      "ALERT_SLACK_WEBHOOK_URL=${SLACK_WEBHOOK}" \
      "ALERT_EMAIL_ENABLED=false" \
      "" \
      "# ERA5 / ECMWF" \
      "ERA5_API_KEY=${ERA5_KEY}" \
      "" \
      "# NASA POWER" \
      "NASA_API_URL=https://power.larc.nasa.gov/api/temporal/monthly/point" \
      "NASA_API_KEY=${NASA_KEY}" \
      "" \
      "# Defaults" \
      "DATA_DIR=data" \
      "OUTPUT_DIR=data/outputs" \
      "LOG_LEVEL=INFO" \
      "LOG_FILE=logs/pipeline.log" \
      "DEFAULT_REGION=Tanzania" \
      "DEFAULT_CRS=EPSG:4326" \
      | ssh_run "cat > ${REMOTE_DIR}/.env"

    ok ".env written to server"
    DEPLOY_SLACK_WEBHOOK="$SLACK_WEBHOOK"
  fi

  # ── Step 5: Google Earth Engine credentials ────────────
  banner "STEP 4/6  Google Earth Engine credentials"
  ssh_run "mkdir -p /root/.config/earthengine"

  if ssh_run "test -s /root/.config/earthengine/credentials" 2>/dev/null; then
    warn "GEE credentials already exist on server — skipping"
  else
    echo ""
    echo -e "${BOLD}Paste your GEE credentials JSON below.${NC}"
    echo -e "${YELLOW}(Local source: ~/.config/earthengine/credentials)${NC}"
    echo -e "${YELLOW}Paste the JSON, then press Enter, then Ctrl+D:${NC}\n"
    GEE_JSON=$(cat)
    [[ -z "$GEE_JSON" ]] && fail "GEE credentials cannot be empty"
    printf '%s\n' "$GEE_JSON" | ssh_run "cat > /root/.config/earthengine/credentials"
    ok "GEE credentials written to server"
  fi

  # Ensure .cdsapirc exists (required by volume mount in compose file)
  ssh_run "touch /root/.cdsapirc"
  ok ".cdsapirc placeholder created (required by volume mount)"

  # ── Step 6: Configure pipeline schedule ───────────────
  banner "STEP 5/6  Configure pipeline schedule"
  info "Setting PIPELINE_SCHEDULE → ${PIPELINE_SCHEDULE}"
  ssh_run "cd ${REMOTE_DIR} && \
    sed -i 's|- PIPELINE_SCHEDULE=.*|- PIPELINE_SCHEDULE=${PIPELINE_SCHEDULE}|' ${COMPOSE_FILE}"
  ok "Schedule set: ${PIPELINE_SCHEDULE}"

  # ── Step 7: Build and launch ───────────────────────────
  banner "STEP 6/6  Build & launch"
  info "Building Docker images (this may take a few minutes)..."
  ssh_run "cd ${REMOTE_DIR} && docker compose -f ${COMPOSE_FILE} build"
  ok "Images built"

  info "Starting all containers in detached mode..."
  ssh_run "cd ${REMOTE_DIR} && docker compose -f ${COMPOSE_FILE} up -d"
  ok "Containers started"

  health_check
  send_slack_ping
  print_summary
}

# =============================================================
# UPDATE MODE — Pull latest code and restart (any machine)
# =============================================================
run_update() {
  banner "Updating [${PROFILE_NAME}] on ${SERVER_HOST}"

  info "Testing SSH connection to ${SERVER}..."
  ssh_run "echo ok" >/dev/null \
    || fail "Cannot SSH to ${SERVER}. Make sure your public key is in the server's authorized_keys."
  ok "SSH OK"

  info "Pulling latest code from ${BRANCH}..."
  ssh_run "cd ${REMOTE_DIR} && git fetch origin && git checkout ${BRANCH} && git pull origin ${BRANCH}"
  ok "Code updated to HEAD of ${BRANCH}"

  # Re-apply schedule in case it drifted
  info "Confirming schedule: ${PIPELINE_SCHEDULE}"
  ssh_run "cd ${REMOTE_DIR} && \
    sed -i 's|- PIPELINE_SCHEDULE=.*|- PIPELINE_SCHEDULE=${PIPELINE_SCHEDULE}|' ${COMPOSE_FILE}"
  ok "Schedule confirmed"

  info "Rebuilding changed images and restarting containers..."
  ssh_run "cd ${REMOTE_DIR} && docker compose -f ${COMPOSE_FILE} up -d --build"
  ok "Containers updated"

  health_check
  print_summary
}

# =============================================================
# Dispatch
# =============================================================
if [[ "$MODE" == "init" ]]; then
  run_init
else
  run_update
fi
