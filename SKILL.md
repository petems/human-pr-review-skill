---
name: human-pr-reviewer
description: >
  Human-focused GitHub Pull Request code review skill. Use when asked to
  "review this PR", "human pr review", "code review", "review pull request",
  "check this PR", or when a GitHub PR URL is provided. Fetches PR metadata,
  diff, comments, commits, and related issues using gh CLI, drafts a review
  workspace, then enforces a mandatory /pr-<number>-show step in your IDE
  before any review can be posted under your name.
version: 2.0.0
category: code-review
triggers:
  - review pr
  - human pr review
  - human review
  - code review
  - review pull request
  - check pr
  - pr review
  - github.com/*/pull/*
author: Peter Souter
license: MIT
tags:
  - github
  - code-review
  - pull-request
  - quality-assurance
  - human-in-the-loop
---

# Human PR Reviewer Skill

A more human take on PR review automation. Drafts the review for you, but
refuses to post anything until you've actually opened it in your IDE and
looked at it.

## Attribution

This skill is a personal fork of
[`SpillwaveSolutions/pr-reviewer-skill`](https://github.com/SpillwaveSolutions/pr-reviewer-skill),
with the communication-focused patterns from
[`code-review-excellence`](https://github.com/wshobson/agents/blob/main/plugins/developer-essentials/skills/code-review-excellence/SKILL.md)
folded in.

**My personal take**: PR review should have a human touch. If a person is
named as the reviewer, they should actually look at the code. Otherwise the
human byline stops meaning much. The mandatory `/pr-<number>-show` step exists
to make that explicit - you cannot post a review under your name until you've
opened it in your IDE and looked at it.

## What this skill does

Conduct PR reviews on GitHub by automating the boring parts (data collection,
file scaffolding, posting commands) and leaving the judgement to a human:

## Table of Contents

- [Purpose](#purpose)
- [When to Use](#when-to-use)
- [Review Process Workflow](#review-process-workflow)
- [Reference Documentation](#reference-documentation)
- [Scripts Reference](#scripts-reference)
- [Best Practices](#best-practices)
- [Quick Reference Commands](#quick-reference-commands)
- [Tips for Effective Reviews](#tips-for-effective-reviews)
- [Resources](#resources)

## Purpose

This skill performs code reviews by:

1. **Automating data collection** - Fetching all PR-related information (metadata, diff, comments, commits, issues)
2. **Organizing review workspace** - Creating structured directory with all artifacts
3. **Applying systematic criteria** - Reviewing against comprehensive quality checklist
4. **Facilitating inline feedback** - Optionally adding comments directly to PR code
5. **Ensuring completeness** - Checking functionality, security, testing, maintainability

## When to Use

Activate this skill when:
- A GitHub PR URL is provided with a review request
- Receiving "review this PR" or "code review" requests
- Checking PR quality before merging
- Providing systematic feedback on proposed changes
- GitHub PR review is mentioned in any context

## Review Process Workflow

**IMPORTANT**: This skill uses a **gated approval process**. `/pr-<number>-show`
is mandatory when commands are deployed to the project directory: `/pr-<number>-send`
and `/pr-<number>-send-decline` will refuse to post anything until the reviewer
has opened the workspace in their IDE. The legacy `/show`, `/send`, and
`/send-decline` commands are still generated in the temporary review directory.

### Overview

1. **Fetch PR data** - Collect all information
2. **Generate review files** - Create detailed, human, and inline comment files
3. **MANDATORY `/pr-<number>-show`** - Open the review in your IDE. Reads the
   files and writes a `.human_reviewed` sentinel that the post commands check for.
4. **Approve and post** - Use `/pr-<number>-send` (approve) or
   `/pr-<number>-send-decline` (request changes). Both refuse without the sentinel.

### Step 1: Fetch PR Data

Use `fetch_pr_data.py` to automatically collect all PR information:

```bash
python scripts/fetch_pr_data.py <pr_url> [--output-dir <dir>] [--no-clone]
```

**Actions performed:**
- Parse PR URL to extract owner, repo, and PR number
- Create directory structure: `<output-dir>/PRs/<repo-name>/<PR-NUMBER>/`
- Fetch PR metadata (title, author, state, branches, labels)
- Download PR diff and commit history
- Retrieve all PR comments and reviews
- Extract ticket references (JIRA, GitHub issues)
- Optionally clone source branch and generate git diff

**Example:**
```bash
python scripts/fetch_pr_data.py https://github.com/facebook/react/pull/28476

# Custom output directory
python scripts/fetch_pr_data.py https://github.com/owner/repo/pull/123 --output-dir /tmp/reviews

# Skip cloning (faster, no git diff)
python scripts/fetch_pr_data.py https://github.com/owner/repo/pull/123 --no-clone
```

**Output structure:**
```
/tmp/PRs/<repo-name>/<PR-NUMBER>/
├── metadata.json           # PR metadata (title, author, branches)
├── diff.patch             # PR diff from gh CLI
├── git_diff.patch         # Git diff (if cloned)
├── comments.json          # Review comments on code
├── commits.json           # Commit history
├── related_issues.json    # Linked GitHub issues
├── ticket_numbers.json    # Extracted ticket references
├── SUMMARY.txt            # Human-readable summary
└── source/                # Cloned repository (if not --no-clone)
```

### Step 2: Analyze PR Data

After fetching, analyze collected data against review criteria:

1. Read `SUMMARY.txt` - High-level overview
2. Review `metadata.json` - PR context, labels, assignees
3. Examine `diff.patch` - Code changes
4. Check `comments.json` - Existing feedback
5. Review `commits.json` - Commit quality and messages
6. Check `related_issues.json` - Linked tickets/issues
7. Apply review criteria - Evaluate against comprehensive checklist

Use the Read tool to examine files:
```
Read /tmp/PRs/<repo-name>/<PR-NUMBER>/SUMMARY.txt
Read /tmp/PRs/<repo-name>/<PR-NUMBER>/metadata.json
Read /tmp/PRs/<repo-name>/<PR-NUMBER>/diff.patch
```

### Step 3: Generate Review Files

**CRITICAL**: After analysis, use `generate_review_files.py` to create structured review documents:

```bash
python scripts/generate_review_files.py <pr_review_dir> --findings <findings_json> [--metadata <metadata_json>] --project-dir <user_project_root>
```

Creates three files in `pr_review_dir/pr/`:

1. **`pr/review.md`** - Detailed internal review with emojis and line numbers
2. **`pr/human.md`** - Clean review for posting (no emojis, em-dashes, line numbers)
3. **`pr/inline.md`** - Proposed inline comments with code snippets

**Also creates slash commands**:
- In `<user_project_root>/.claude/commands/`: `/pr-<number>-show`,
  `/pr-<number>-send`, and `/pr-<number>-send-decline`
- In `<pr_review_dir>/.claude/commands/`: legacy `/show`, `/send`, and
  `/send-decline`

Use the PR-specific commands from the project directory. They avoid collisions
when reviewing multiple PRs and do not require changing into the temporary
review directory.

**Findings JSON structure**:
```json
{
  "summary": "Overall assessment of the PR...",
  "metadata": {
    "repository": "owner/repo",
    "number": 123,
    "title": "PR title",
    "author": "username",
    "head_branch": "feature",
    "base_branch": "main"
  },
  "blockers": [
    {
      "category": "Security",
      "issue": "SQL injection vulnerability",
      "file": "src/db/queries.py",
      "line": 45,
      "details": "Using string concatenation for SQL query",
      "fix": "Use parameterized queries",
      "code_snippet": "result = db.execute('SELECT * FROM users WHERE id = ' + user_id)"
    }
  ],
  "important": [...],
  "nits": [...],
  "suggestions": ["Consider adding...", "Future enhancement..."],
  "questions": ["Is this intended to...", "Should we..."],
  "praise": ["Excellent test coverage", "Clear documentation"],
  "inline_comments": [
    {
      "file": "src/app.py",
      "line": 42,
      "comment": "Consider edge case handling for empty input",
      "code_snippet": "def process(data):\n    return data.strip()",
      "start_line": 41,
      "end_line": 43,
      "owner": "owner",
      "repo": "repo",
      "pr_number": 123
    }
  ]
}
```

### Step 4: Mandatory Human Review (`/pr-<number>-show`)

**This step is required. `/pr-<number>-send` and
`/pr-<number>-send-decline` will refuse to run until `/pr-<number>-show` has
been used.**

From the user's project directory, run `/pr-<number>-show`. It will:

1. Open the review directory and review files in VS Code.
2. Write a sentinel file `.human_reviewed` containing a timestamp.

Then read and edit:

- `pr/review.md` - Detailed analysis (internal use)
- `pr/human.md` - **What gets posted on GitHub**. Edit anything that doesn't
  sound like you. The byline will say it's from you - make sure it actually is.
- `pr/inline.md` - Proposed inline comments. Trim, edit, or skip entirely.

**NOTHING is posted until explicit approval in Step 5.**

**Why is this mandatory?** See
[`references/human_review_principles.md`](./references/human_review_principles.md).
Short answer: if the review is going to carry your name, a human (you) should
have eyeballed it. The sentinel is a low-friction guardrail against posting
generated feedback without review.

### Step 5: Approve and Post

Post the review when ready. Both commands check for the `.human_reviewed`
sentinel and abort with a clear message if it is missing.

**Option A: Approve the PR**
```
/pr-<number>-send
```
- Verifies `.human_reviewed` exists (refuses otherwise)
- Posts `pr/human.md` as a PR comment
- Approves the PR
- Confirms action

**Option B: Request Changes**
```
/pr-<number>-send-decline
```
- Verifies `.human_reviewed` exists (refuses otherwise)
- Posts `pr/human.md` as a PR comment
- Requests changes on the PR
- Confirms action

**Posting inline comments** (optional, after `/pr-<number>-send` or
`/pr-<number>-send-decline`):
Review `pr/inline.md` and run the provided commands for specific code comments.

### Step 6: Apply Review Criteria

Reference `references/review_criteria.md` for comprehensive checklist. Review against these categories:

| Category | Key Questions |
|----------|--------------|
| Functionality | Does code solve the problem? Bugs? Edge cases? |
| Readability | Clear code? Meaningful names? DRY? |
| Style | Follows linter rules? Consistent with codebase? |
| Performance | Efficient algorithms? Scalable? |
| Security | Vulnerabilities addressed? Secrets protected? |
| Testing | Tests exist? Cover happy paths and edge cases? |
| PR Quality | Focused scope? Clean commits? Clear description? |

**Priority markers for findings:**
- Blocker: Must be fixed before merge
- Important: Should be addressed
- Nit: Nice to have, optional
- Suggestion: Consider for future
- Question: Clarification needed
- Praise: Good work

**For detailed criteria:** Read `references/review_criteria.md`

## Reference Documentation

This skill includes comprehensive reference guides:

| Reference | Purpose |
|-----------|---------|
| `references/human_review_principles.md` | **How to phrase feedback**. Severity tags, question approach, suggest-don't-command, sandwich method, handling disagreements. |
| `references/review_criteria.md` | **What to look for**. Checklist covering functionality, security, testing, performance, etc. |
| `references/gh_cli_guide.md` | Quick reference for GitHub CLI commands |
| `references/scenarios.md` | Detailed workflows for common review scenarios |
| `references/troubleshooting.md` | Common issues and solutions |

## Scripts Reference

### `scripts/fetch_pr_data.py`

Automated PR data fetching and organization.

```bash
python scripts/fetch_pr_data.py <pr_url> [options]

Options:
  --output-dir DIR    Base output directory (default: /tmp)
  --no-clone         Skip cloning repository
```

### `scripts/generate_review_files.py`

Generate structured review files from analysis findings.

```bash
python scripts/generate_review_files.py <pr_review_dir> --findings <findings_json> [--metadata <metadata_json>] --project-dir <user_project_root>
```

**Creates:**
- `pr/review.md` - Detailed internal review
- `pr/human.md` - Clean review for posting
- `pr/inline.md` - Proposed inline comments with commands
- `<user_project_root>/.claude/commands/pr-<number>-show.md` - **Mandatory**
  project command: opens the review in your IDE and writes the `.human_reviewed`
  sentinel
- `<user_project_root>/.claude/commands/pr-<number>-send.md` - Project command
  to approve and post (refuses unless the sentinel is present)
- `<user_project_root>/.claude/commands/pr-<number>-send-decline.md` - Project
  command to request changes (refuses unless the sentinel is present)
- `<pr_review_dir>/.claude/commands/show.md`, `send.md`, and `send-decline.md`
  - Legacy tmpdir commands for the same workflow
- `REVIEW_READY.txt` - Summary of next steps

### `scripts/add_inline_comment.py`

Add inline code review comments to specific lines in PR.

```bash
python scripts/add_inline_comment.py <owner> <repo> <pr_number> <commit_id> <file_path> <line> "<comment>" [options]

Options:
  --side RIGHT|LEFT       Side of diff (default: RIGHT)
  --start-line N         Starting line for multi-line comment
  --start-side RIGHT|LEFT Starting side for multi-line comment
  --no-fallback          Fail instead of falling back to a regular PR comment
```

**Automatic fallback**: If the target line is outside the PR diff, the script
automatically posts a regular PR comment instead, prefixed with the file and
line context. Use `--no-fallback` to disable this and fail with an error.

## Best Practices

### Communication
- Frame feedback as suggestions, not criticism
- Explain why an issue matters, not just what is wrong
- Acknowledge excellent practices
- Prioritize blockers first, style issues last

### Review Efficiency
- Use scripts to automate data fetching and comment posting
- Reference `review_criteria.md` as checklist
- Focus: Critical issues > Important > Nice-to-have
- Review promptly (within 24 hours if possible)

### Inline Comments
- Reference exact lines and files
- Provide better alternatives
- Test inline comments on test PRs first
- Use sparingly to avoid overwhelming
- Lines outside the PR diff automatically fall back to regular PR comments

### PR Size Handling
- Large PRs (>400 lines): Suggest splitting
- Review in logical chunks
- Focus on architecture for large changes

**For detailed scenarios:** Read `references/scenarios.md`

## Quick Reference Commands

```bash
# Fetch PR data
python scripts/fetch_pr_data.py https://github.com/owner/repo/pull/123

# Add inline comment
python scripts/add_inline_comment.py owner repo 123 latest "src/app.py" 42 "Comment"

# View PR in browser
gh pr view 123 --repo owner/repo --web

# Check PR status
gh pr checks 123 --repo owner/repo

# View existing comments
gh api /repos/owner/repo/pulls/123/comments --jq '.[] | {path, line, body}'
```

## Tips for Effective Reviews

1. Start with context: Read PR description, linked issues, commit messages
2. Understand intent: Identify the problem being solved
3. Check tests first: Verify tests demonstrate the fix/feature
4. Look for patterns: Repeated issues suggest architecture problems
5. Consider alternatives: Evaluate simpler approaches
6. Think about maintenance: Assess future modification ease
7. Remember humans: Maintain kindness, respect, and constructive tone

**For troubleshooting:** Read `references/troubleshooting.md`

## Resources

- **Review Criteria**: `references/review_criteria.md`
- **gh CLI Guide**: `references/gh_cli_guide.md`
- **Scenarios**: `references/scenarios.md`
- **Troubleshooting**: `references/troubleshooting.md`
- **GitHub PR Review Docs**: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests
- **Google Engineering Practices**: https://google.github.io/eng-practices/review/
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
