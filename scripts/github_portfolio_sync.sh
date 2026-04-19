#!/usr/bin/env bash
set -euo pipefail

# Requires: gh CLI authenticated with repo/admin rights for ElhombreX21th org/user repos.
OWNER="ElhombreX21th"

rename_repo() {
  local old_name="$1"
  local new_name="$2"
  gh api -X PATCH "/repos/${OWNER}/${old_name}" -f name="${new_name}" >/dev/null
  echo "Renamed: ${old_name} -> ${new_name}"
}

set_about() {
  local repo="$1"
  local desc="$2"
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
