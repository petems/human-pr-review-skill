# Human PR Reviewer Skill for Claude Code

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude-Code-5A67D8)](https://claude.ai/code)

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
named as the reviewer, they should actually look at the code. Otherwise it's
just agents reviewing agents in an ouroboros, and at that point why is a
person assigned at all? The mandatory `/show` step exists to make that
explicit - you cannot post a review under your name until you've opened it
in your IDE and looked at it.

## Overview

This is a Claude Code skill that does the boring half of code review for you
- fetching the PR diff, comments, commits and linked issues, and scaffolding
the review files - while keeping the judgement step in human hands. The
`/show` slash command is mandatory: it writes a `.human_reviewed` sentinel,
and `/send` / `/send-decline` will refuse to post anything until that
sentinel exists.

## Features

- **Automated Data Collection** - Fetches PR metadata, diffs, comments, commits, and related issues via GitHub CLI
- **Systematic Analysis** - Reviews against comprehensive criteria: security, testing, maintainability, performance
- **Structured Review Files** - Generates detailed internal review, clean public review, and inline comment templates
- **Mandatory `/show` Gate** - `/send` and `/send-decline` refuse to post until you've opened the review in your IDE. No more drive-by approvals.
- **Communication Patterns Built In** - Severity tags (`[blocking]`, `[important]`, `[nit]`, `[suggestion]`, `[learning]`, `[question]`, `[praise]`), question approach, and suggest-don't-command phrasing baked into the templates
- **Inline Comments** - Adds specific feedback directly to code lines with posting commands
- **Ticket Tracking** - Extracts and links JIRA/GitHub issue references
- **Professional Templates** - Clean, respectful review format without emojis or excessive formatting

## Installation

### Installing with Skilz (Recommended)

The easiest way to install this skill is using the [Skilz Universal Installer](https://github.com/SpillwaveSolutions/skilz):

```bash
# Install Skilz (one-time setup)
curl -fsSL https://raw.githubusercontent.com/SpillwaveSolutions/skilz/main/install.sh | bash

# Install this skill
skilz install SpillwaveSolutions_pr-reviewer-skill/pr-reviewer
```

View on the Skilz Marketplace: [pr-reviewer](https://skillzwave.ai/skill/SpillwaveSolutions__pr-reviewer-skill__pr-reviewer__SKILL/)

### Manual Installation

1. **Install GitHub CLI** (if not already installed):
   ```bash
   # macOS
   brew install gh

   # Linux
   sudo apt install gh  # or yum, dnf, etc.

   # Windows
   winget install GitHub.cli
   ```

2. **Authenticate with GitHub**:
   ```bash
   gh auth login
   ```

3. **Clone this skill** to your Claude Code skills directory:
   ```bash
   cd ~/.claude/skills
   git clone https://github.com/SpillwaveSolutions/pr-reviewer-skill.git pr-reviewer
   ```

4. **Install Python dependencies** (if needed):
   ```bash
   cd pr-reviewer
   pip install requests  # Only needed for add_inline_comment.py
   ```

## Quick Start

### Basic PR Review

1. **Fetch PR data**:
   ```bash
   python scripts/fetch_pr_data.py https://github.com/owner/repo/pull/123
   ```

2. **Analyze the PR** by reading the generated files:
   ```
   /tmp/PRs/<repo-name>/123/SUMMARY.txt
   /tmp/PRs/<repo-name>/123/diff.patch
   /tmp/PRs/<repo-name>/123/metadata.json
   ```

3. **Generate review files** with your findings:
   ```bash
   python scripts/generate_review_files.py /tmp/PRs/<repo-name>/123 --findings findings.json
   ```

4. **MANDATORY: open the review in your IDE**:
   ```bash
   /show  # Opens review directory in VS Code, writes .human_reviewed sentinel
   ```
   Read `pr/human.md` - that's what gets posted under your name. Edit anything
   that doesn't sound like you.

5. **Approve and post** (refuses to run unless step 4 was done):
   ```bash
   /send          # Approve PR and post review
   # or
   /send-decline  # Request changes and post review
   ```

## Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Fetch PR Data                                                │
│    python scripts/fetch_pr_data.py <pr_url>                     │
│    → Collects metadata, diff, comments, commits, issues         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Analyze PR                                                   │
│    → Read SUMMARY.txt, diff.patch, metadata.json               │
│    → Apply review criteria (security, testing, etc.)           │
│    → Create findings JSON with your analysis                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Generate Review Files                                        │
│    python scripts/generate_review_files.py <dir> --findings ... │
│    → Creates review.md, human.md, inline.md                    │
│    → Generates /show, /send, /send-decline commands            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. MANDATORY: Human Review (/show)                              │
│    /show → Opens in VS Code, writes .human_reviewed sentinel    │
│    → Read pr/human.md (this gets posted under your name)        │
│    → Edit anything that doesn't sound like you                  │
│    → Review pr/inline.md for proposed comments                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Approve & Post (gated on the sentinel)                       │
│    /send (approve) or /send-decline (request changes)           │
│    → Refuses to run unless .human_reviewed exists               │
│    → Posts pr/human.md as review comment                        │
│    → Optionally post inline comments from pr/inline.md          │
└─────────────────────────────────────────────────────────────────┘
```

## Review Criteria

This skill reviews PRs against comprehensive industry-standard criteria:

### 1. Functionality & Correctness
- Does code solve the intended problem?
- Are there bugs or logical errors?
- Edge cases and error handling covered?

### 2. Security & Best Practices
- Common vulnerabilities (SQL injection, XSS, CSRF)?
- Secrets not hardcoded?
- Dependencies justified and secure?

### 3. Testing & Quality Assurance
- Tests exist for new code?
- Tests cover happy paths, errors, edge cases?
- CI/CD checks pass?

### 4. Readability & Maintainability
- Code clarity and meaningful names?
- Functions follow Single Responsibility?
- Code duplication avoided (DRY)?

### 5. Performance & Efficiency
- Algorithm efficiency (avoid O(n²) where possible)?
- Scalability under load?

### 6. Style & Conventions
- Follows project linter rules?
- Consistent with existing codebase?

### 7. Overall PR Quality
- PR scope focused (single feature/fix)?
- Clean commit history?
- Clear PR description?

**See `references/review_criteria.md` for complete checklist.**

## Scripts

### `fetch_pr_data.py`

Automated PR data collection and organization.

```bash
python scripts/fetch_pr_data.py <pr_url> [options]

Options:
  --output-dir DIR    Base output directory (default: /tmp)
  --no-clone         Skip cloning repository (faster)
```

**Output structure**:
```
/tmp/PRs/<repo-name>/<PR-NUMBER>/
├── metadata.json           # PR metadata (title, author, branches, etc.)
├── diff.patch             # PR diff from gh CLI
├── git_diff.patch         # Git diff (if cloned)
├── comments.json          # Review comments on code
├── commits.json           # Commit history
├── related_issues.json    # Linked GitHub issues
├── ticket_numbers.json    # Extracted ticket references
├── SUMMARY.txt            # Human-readable summary
└── source/                # Cloned repository (if not --no-clone)
```

### `generate_review_files.py`

Generates structured review documents from analysis findings.

```bash
python scripts/generate_review_files.py <pr_review_dir> --findings <findings_json> [--metadata <metadata_json>]
```

**Creates**:
- `pr/review.md` - Detailed internal review with emojis and line numbers
- `pr/human.md` - Clean review for posting (no emojis, em-dashes, line numbers)
- `pr/inline.md` - Proposed inline comments with posting commands
- `.claude/commands/send.md` - Slash command to approve and post
- `.claude/commands/send-decline.md` - Slash command to request changes
- `.claude/commands/show.md` - Slash command to open in VS Code

**Example findings JSON**:
```json
{
  "summary": "Overall assessment of the PR",
  "metadata": {
    "repository": "owner/repo",
    "number": 123,
    "title": "PR title",
    "author": "username"
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
      "end_line": 43
    }
  ]
}
```

### `add_inline_comment.py`

Posts inline comments to specific lines in a PR.

```bash
python scripts/add_inline_comment.py <owner> <repo> <pr_number> <commit_id> <file_path> <line> "<comment>" [options]

Options:
  --side RIGHT|LEFT       Side of diff (default: RIGHT)
  --start-line N         Starting line for multi-line comment
  --start-side RIGHT|LEFT Starting side for multi-line comment
```

**Example**:
```bash
python scripts/add_inline_comment.py facebook react 28476 latest "packages/react/src/React.js" 42 "Consider edge case handling here"
```

## Usage with Claude Code

When you install this skill, Claude Code can automatically use it when you:

1. Provide a GitHub PR URL and request a review
2. Say "review this PR" or "code review"
3. Ask to check PR quality before merging
4. Mention GitHub PR review in any context

**Trigger phrases**:
- "review pr"
- "human pr review"
- "human review"
- "code review"
- "review pull request"
- "check pr"
- "github.com/*/pull/*" (any PR URL)

## Examples

### Example 1: Quick Review

```
User: Can you review this PR? https://github.com/facebook/react/pull/28476

Claude Code:
1. Runs fetch_pr_data.py to collect all PR data
2. Reads SUMMARY.txt and metadata.json for context
3. Scans diff.patch for critical issues
4. Applies security, functionality, and testing criteria
5. Creates findings JSON with analysis
6. Runs generate_review_files.py to create review files
7. Tells you to review pr/review.md and pr/human.md
8. Reminds you to use /show to edit, then /send or /send-decline
```

### Example 2: Comprehensive Review with Inline Comments

```
User: Do a thorough review and add inline comments where needed

Claude Code:
1. Fetches complete PR data including cloned repository
2. Analyzes all files against full review_criteria.md checklist
3. Identifies blockers, important issues, and nits
4. Creates findings JSON with detailed inline_comments array
5. Generates all review files (review.md, human.md, inline.md)
6. Provides /show, /send, /send-decline commands
7. You review, edit, approve, and optionally post inline comments
```

### Example 3: Security-Focused Review

```
User: Check this PR for security issues

Claude Code:
1. Fetches PR data
2. Focuses on security criteria (SQL injection, XSS, secrets, etc.)
3. Examines dependencies and authentication changes
4. Reports security findings with severity levels
5. Generates review with security-focused recommendations
```

## Best Practices

### Communication
- **Be constructive** - Frame as suggestions, not criticism
- **Explain why** - Don't just say what's wrong, explain why it matters
- **Acknowledge good work** - Call out excellent practices
- **Prioritize** - Focus on blockers first, style issues last

### Review Efficiency
- **Use scripts** - Automate data fetching and comment posting
- **Reference criteria** - Use `review_criteria.md` as checklist
- **Focus review** - Critical issues > Important > Nice-to-have
- **Be timely** - Review promptly (within 24 hours if possible)

### Inline Comments
- **Be specific** - Reference exact lines and files
- **Provide examples** - Show better alternatives
- **Test first** - Try inline comments on test PRs
- **Use sparingly** - Too many inline comments can overwhelm

## Troubleshooting

### "gh CLI not found"
Install GitHub CLI: https://cli.github.com/

### "Permission denied" errors
Check authentication:
```bash
gh auth status
gh auth refresh -s repo
```

### "Invalid PR URL"
Ensure URL format: `https://github.com/owner/repo/pull/NUMBER`

### Rate limit errors
```bash
# Check rate limit
gh api /rate_limit

# Authenticated users get higher limits
gh auth login
```

## Reference Documentation

- **`references/human_review_principles.md`** - How to phrase feedback (severity tags, question approach, sandwich method, handling disagreements)
- **`references/review_criteria.md`** - What to look for: complete checklist with examples
- **`references/gh_cli_guide.md`** - GitHub CLI commands and patterns
- **`references/scenarios.md`** - Common review workflows
- **`references/troubleshooting.md`** - Common issues and fixes
- **`SKILL.md`** - Detailed skill documentation for Claude Code

## Resources

- [GitHub PR Review Documentation](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests)
- [Google Engineering Practices](https://google.github.io/eng-practices/review/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub CLI Documentation](https://cli.github.com/manual/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Forked from [SpillwaveSolutions/pr-reviewer-skill](https://github.com/SpillwaveSolutions/pr-reviewer-skill)
- Communication patterns adapted from [`code-review-excellence`](https://github.com/wshobson/agents/blob/main/plugins/developer-essentials/skills/code-review-excellence/SKILL.md)
- Built for [Claude Code](https://claude.ai/code)
- Uses [GitHub CLI](https://cli.github.com/) for API interactions

## Support

For issues, questions, or suggestions:
- Consult `SKILL.md` and the `references/` directory
- Upstream issues belong in the original [pr-reviewer-skill repo](https://github.com/SpillwaveSolutions/pr-reviewer-skill/issues)

---

**Made with care for better code reviews - by humans, for humans**
