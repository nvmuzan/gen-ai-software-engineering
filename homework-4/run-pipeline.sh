#!/usr/bin/env bash
# 4-Agent Bug-Fix Pipeline — Budget Tracker CLI, Bug Set 001
# Usage: bash run-pipeline.sh
# Prerequisites: claude CLI installed and authenticated (ANTHROPIC_API_KEY set)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BUGS_DIR="context/bugs/001"

# Strip YAML frontmatter from agent file (between first and second ---)
strip_frontmatter() {
  awk '/^---$/{n++;next} n==1{next} {print}' "$1"
}

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   4-Agent Bug-Fix Pipeline               ║"
echo "║   Budget Tracker CLI — Bug Set 001       ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Step 1: Research Verifier (claude-opus-4-8)
echo "━━━ Step 1/4: Research Verifier (claude-opus-4-8) ━━━"
claude -p \
  --model claude-opus-4-8 \
  --system-prompt "$(strip_frontmatter agents/research-verifier.agent.md)" \
  "Verify $BUGS_DIR/research/codebase-research.md against source files in src/. Apply skills/research-quality-measurement.md. Write $BUGS_DIR/research/verified-research.md."
echo "✓ verified-research.md written"

# Step 2: Bug Fixer (claude-sonnet-4-6)
echo ""
echo "━━━ Step 2/4: Bug Fixer (claude-sonnet-4-6) ━━━"
claude -p \
  --model claude-sonnet-4-6 \
  --system-prompt "$(strip_frontmatter agents/bug-fixer.agent.md)" \
  "Read $BUGS_DIR/implementation-plan.md. Apply all changes to src/ exactly as specified. Run python3 -m pytest tests/ -v after each change. Write $BUGS_DIR/fix-summary.md."
echo "✓ fix-summary.md written, source files patched"

# Step 3: Security Verifier (claude-opus-4-8)
echo ""
echo "━━━ Step 3/4: Security Verifier (claude-opus-4-8) ━━━"
claude -p \
  --model claude-opus-4-8 \
  --system-prompt "$(strip_frontmatter agents/security-verifier.agent.md)" \
  "Read $BUGS_DIR/fix-summary.md to find changed files. Scan those files for security issues. Write $BUGS_DIR/security-report.md."
echo "✓ security-report.md written"

# Step 4: Unit Test Generator (claude-sonnet-4-6)
echo ""
echo "━━━ Step 4/4: Unit Test Generator (claude-sonnet-4-6) ━━━"
claude -p \
  --model claude-sonnet-4-6 \
  --system-prompt "$(strip_frontmatter agents/unit-test-generator.agent.md)" \
  "Read $BUGS_DIR/fix-summary.md. Generate unit tests in tests/test_budget.py for changed functions only. Apply skills/unit-tests-FIRST.md. Run python3 -m pytest tests/ -v. Write $BUGS_DIR/test-report.md."
echo "✓ tests/test_budget.py written, test-report.md written"

echo ""
echo "━━━ Final Test Run ━━━"
python3 -m pytest tests/ -v

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Pipeline complete!                     ║"
echo "╚══════════════════════════════════════════╝"
echo "  Artifacts in $BUGS_DIR/:"
echo "    verified-research.md"
echo "    fix-summary.md"
echo "    security-report.md"
echo "    test-report.md"
