#!/usr/bin/env bash
set -euo pipefail

# Full GitHub portfolio/profile sync for ElhombreX21th.
# Requirements:
#   - curl, git
#   - Personal Access Token with repo + user scopes in GITHUB_TOKEN
# Usage:
#   GITHUB_TOKEN=xxx ./scripts/github_portfolio_sync.sh

OWNER="ElhombreX21th"
API="https://api.github.com"
WORKDIR="$(mktemp -d)"

cleanup() {
  rm -rf "$WORKDIR"
}
trap cleanup EXIT

require_env() {
  if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    echo "ERROR: GITHUB_TOKEN is not set."
    exit 1
  fi
}

api_patch() {
  local path="$1"
  local json_payload="$2"

  curl -fsSL -X PATCH "${API}${path}" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    -d "${json_payload}" >/dev/null
}

api_post() {
  local path="$1"
  local json_payload="$2"

  curl -fsSL -X POST "${API}${path}" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    -d "${json_payload}" >/dev/null
}

repo_exists() {
  local repo="$1"
  local status
  status=$(curl -s -o /dev/null -w '%{http_code}' \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    "${API}/repos/${OWNER}/${repo}")
  [[ "$status" == "200" ]]
}
# Requires: gh CLI authenticated with repo/admin rights for ElhombreX21th org/user repos.
OWNER="ElhombreX21th"

rename_repo() {
  local old_name="$1"
  local new_name="$2"

  if repo_exists "$new_name"; then
    echo "Skip rename: ${new_name} already exists"
    return
  fi

  if repo_exists "$old_name"; then
    api_patch "/repos/${OWNER}/${old_name}" "{\"name\":\"${new_name}\"}"
    echo "Renamed: ${old_name} -> ${new_name}"
  else
    echo "Skip rename: ${old_name} not found"
  fi
  gh api -X PATCH "/repos/${OWNER}/${old_name}" -f name="${new_name}" >/dev/null
  echo "Renamed: ${old_name} -> ${new_name}"
}

set_about() {
  local repo="$1"
  local desc="$2"

  if repo_exists "$repo"; then
    api_patch "/repos/${OWNER}/${repo}" "{\"description\":\"${desc}\"}"
    echo "Updated About: ${repo}"
  else
    echo "Skip About: ${repo} not found"
  fi
}

ensure_profile_repo() {
  local repo="${OWNER}"

  if repo_exists "$repo"; then
    echo "Profile repo already exists: ${repo}"
  else
    api_post "/user/repos" "{\"name\":\"${repo}\",\"private\":false,\"description\":\"GitHub profile README for ${OWNER}\"}"
    echo "Created profile repo: ${repo}"
  fi
}

sync_readme() {
  local repo="$1"
  local template_path="$2"

  if ! repo_exists "$repo"; then
    echo "Skip README sync: ${repo} not found"
    return
  fi

  local remote="https://${GITHUB_TOKEN}@github.com/${OWNER}/${repo}.git"
  local local_dir="${WORKDIR}/${repo}"

  git clone --depth 1 "$remote" "$local_dir" >/dev/null 2>&1
  cp "$template_path" "$local_dir/README.md"

  (
    cd "$local_dir"
    git add README.md
    if git diff --cached --quiet; then
      echo "README unchanged: ${repo}"
      exit 0
    fi
    git -c user.name="codex-bot" -c user.email="codex-bot@users.noreply.github.com" \
      commit -m "docs: align README with MedTech/Data/AI portfolio positioning" >/dev/null
    git push origin HEAD >/dev/null 2>&1
    echo "README updated: ${repo}"
  )
}

main() {
  require_env

  echo "== 1) Update profile fields =="
  api_patch "/user" '{"name":"Flavio Cruz","bio":"MedTech Systems | Data & Analytics | AI-Enabled Technical Solutions","company":"FPConnect","location":"Brazil","blog":"https://www.linkedin.com/in/flavio-cruz-09751820"}'
  echo "Profile fields updated"

  echo "== 2) Ensure profile README repo =="
  ensure_profile_repo

  echo "== 3) Rename repositories =="
  rename_repo "Project-Principal" "servicenow-logic-lab"
  rename_repo "Projeto-de-extens-o-plataforma-web-para-a-cooperativa." "doce-sabor-digital"
  rename_repo "Main-Repository" "flavio-cruz-portfolio"
  rename_repo "https-eu-de.dataplatform.cloud.ibm.com-analytics-notebooks-v2-1389bf1e-33e5-4ff2-ab80-da4e1d5725b8" "ibm-data-analysis-labs"
  rename_repo "agente-autonomo" "autonomous-ai-agent-lab"

  echo "== 4) Update About descriptions =="
  set_about "fpconnect-rca-copilot" "SaaS platform for technical operations, incident tracking and RCA workflows in MedTech and healthcare environments."
  set_about "servicenow-logic-lab" "Study project to practice ServiceNow-style concepts: incidents, business rules, client scripts and outbound REST integrations."
  set_about "doce-sabor-digital" "University extension project to digitize order workflows and web presence for a local artisanal cooperative."
  set_about "flavio-cruz-portfolio" "Portfolio hub with selected projects in MedTech systems, data analytics, AI automation and full-stack development."
  set_about "ibm-data-analysis-labs" "Data analysis notebooks and exercises built during IBM and Python-based analytics studies."
  set_about "autonomous-ai-agent-lab" "Experimental repository for autonomous AI agent workflows, automation logic and applied orchestration concepts."

  echo "== 5) Replace READMEs =="
  sync_readme "${OWNER}" "github-readmes/PROFILE_README_ElhombreX21th.md"
  sync_readme "flavio-cruz-portfolio" "README.md"
  sync_readme "servicenow-logic-lab" "github-readmes/README_servicenow-logic-lab.md"
  sync_readme "doce-sabor-digital" "github-readmes/README_doce-sabor-digital.md"
  sync_readme "ibm-data-analysis-labs" "github-readmes/README_ibm-data-analysis-labs.md"
  sync_readme "autonomous-ai-agent-lab" "github-readmes/README_autonomous-ai-agent-lab.md"
  sync_readme "fpconnect-rca-copilot" "github-readmes/README_fpconnect-rca-copilot.md"

  echo "All steps completed."
}

main "$@"
  gh api -X PATCH "/repos/${OWNER}/${repo}" -f description="${desc}" >/dev/null
  echo "Updated About: ${repo}"
}

echo "== Step 1: Rename repositories =="
rename_repo "Project-Principal" "servicenow-logic-lab"
rename_repo "Projeto-de-extens-o-plataforma-web-para-a-cooperativa." "doce-sabor-digital"
rename_repo "Main-Repository" "flavio-cruz-portfolio"
rename_repo "https-eu-de.dataplatform.cloud.ibm.com-analytics-notebooks-v2-1389bf1e-33e5-4ff2-ab80-da4e1d5725b8" "ibm-data-analysis-labs"
rename_repo "agente-autonomo" "autonomous-ai-agent-lab"

echo "== Step 2: Set repository About descriptions =="
set_about "fpconnect-rca-copilot" "SaaS platform for technical operations, incident tracking and RCA workflows in MedTech and healthcare environments."
set_about "servicenow-logic-lab" "Study project to practice ServiceNow-style concepts: incidents, business rules, client scripts and outbound REST integrations."
set_about "doce-sabor-digital" "University extension project to digitize order workflows and web presence for a local artisanal cooperative."
set_about "flavio-cruz-portfolio" "Portfolio hub with selected projects in MedTech systems, data analytics, AI automation and full-stack development."
set_about "ibm-data-analysis-labs" "Data analysis notebooks and exercises built during IBM and Python-based analytics studies."
set_about "autonomous-ai-agent-lab" "Experimental repository for autonomous AI agent workflows, automation logic and applied orchestration concepts."

echo "== Step 3: Set profile name and bio =="
gh api -X PATCH "/user" -f name="Flavio Cruz" -f bio="MedTech Systems | Data & Analytics | AI-Enabled Technical Solutions" >/dev/null
echo "Profile updated"

echo "== Step 4 (manual in each repo): replace README.md with templates in github-readmes/ =="
echo "Done."
