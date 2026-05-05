#!/usr/bin/env python3
"""
Generate structured review files from PR analysis.

Creates three review files:
- pr/review.md: Detailed review for internal use
- pr/human.md: Short, clean review for posting (no emojis, em-dashes, line numbers)
- pr/inline.md: List of inline comments with code snippets

Usage:
    python generate_review_files.py <pr_review_dir> --findings <findings_json> [--project-dir <project_dir>]

Example:
    python generate_review_files.py /tmp/PRs/myrepo/123 --findings findings.json --project-dir /path/to/project
"""

import argparse
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


def create_pr_directory(pr_review_dir: Path) -> Path:
    """Create the pr/ subdirectory for review files."""
    pr_dir = pr_review_dir / "pr"
    pr_dir.mkdir(parents=True, exist_ok=True)
    return pr_dir


def load_findings(findings_file: str) -> Dict[str, Any]:
    """
    Load review findings from JSON file.

    Expected structure:
    {
        "summary": "Overall assessment...",
        "blockers": [{
            "category": "Security",
            "issue": "SQL injection vulnerability",
            "file": "src/db/queries.py",
            "line": 45,
            "details": "Using string concatenation...",
            "fix": "Use parameterized queries",
            "code_snippet": "result = db.execute(...)"
        }],
        "important": [...],
        "nits": [...],
        "suggestions": [...],
        "questions": [...],
        "praise": [...],
        "inline_comments": [{
            "file": "src/app.py",
            "line": 42,
            "comment": "Consider edge case handling",
            "code_snippet": "def process(data):\n    return data.strip()",
            "start_line": 41,
            "end_line": 43
        }]
    }
    """
    with open(findings_file, 'r') as f:
        return json.load(f)


def generate_detailed_review(findings: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    """Generate detailed review.md with full analysis."""

    review = f"""# Pull Request Review - Detailed Analysis

## PR Information

**Repository**: {metadata.get('repository', 'N/A')}
**PR Number**: #{metadata.get('number', 'N/A')}
**Title**: {metadata.get('title', 'N/A')}
**Author**: {metadata.get('author', 'N/A')}
**Branch**: {metadata.get('head_branch', 'N/A')} → {metadata.get('base_branch', 'N/A')}

## Summary

{findings.get('summary', 'No summary provided')}

"""

    # Add blockers
    blockers = findings.get('blockers', [])
    if blockers:
        review += "## 🔴 [blocking] Critical Issues\n\n"
        review += "**These MUST be fixed before merging.**\n\n"
        for i, blocker in enumerate(blockers, 1):
            review += f"### {i}. [blocking] {blocker.get('category', 'Issue')}: {blocker.get('issue', 'Unknown')}\n\n"
            if blocker.get('file'):
                review += f"**File**: `{blocker['file']}"
                if blocker.get('line'):
                    review += f":{blocker['line']}"
                review += "`\n\n"
            review += f"**Problem**: {blocker.get('details', 'No details')}\n\n"
            if blocker.get('fix'):
                review += f"**Solution**: {blocker['fix']}\n\n"
            if blocker.get('code_snippet'):
                review += f"**Current Code**:\n```\n{blocker['code_snippet']}\n```\n\n"
            review += "---\n\n"

    # Add important issues
    important = findings.get('important', [])
    if important:
        review += "## 🟡 [important] Issues\n\n"
        review += "**Should be addressed before merging.**\n\n"
        for i, issue in enumerate(important, 1):
            review += f"### {i}. [important] {issue.get('category', 'Issue')}: {issue.get('issue', 'Unknown')}\n\n"
            if issue.get('file'):
                review += f"**File**: `{issue['file']}"
                if issue.get('line'):
                    review += f":{issue['line']}"
                review += "`\n\n"
            review += f"**Impact**: {issue.get('details', 'No details')}\n\n"
            if issue.get('fix'):
                review += f"**Suggestion**: {issue['fix']}\n\n"
            if issue.get('code_snippet'):
                review += f"**Code**:\n```\n{issue['code_snippet']}\n```\n\n"
            review += "---\n\n"

    # Add nits
    nits = findings.get('nits', [])
    if nits:
        review += "## 🟢 [nit] Minor Issues\n\n"
        review += "**Nice to have, but not blocking.**\n\n"
        for i, nit in enumerate(nits, 1):
            review += f"{i}. [nit] **{nit.get('category', 'Style')}**: {nit.get('issue', 'Unknown')}\n"
            if nit.get('file'):
                review += f"   - File: `{nit['file']}`\n"
            if nit.get('details'):
                review += f"   - {nit['details']}\n"
            review += "\n"

    # Add suggestions
    suggestions = findings.get('suggestions', [])
    if suggestions:
        review += "## 💡 [suggestion] For future consideration\n\n"
        for i, suggestion in enumerate(suggestions, 1):
            review += f"{i}. {suggestion}\n"
        review += "\n"

    # Add learning notes
    learning = findings.get('learning', [])
    if learning:
        review += "## 📚 [learning] Notes\n\n"
        review += "**Educational context. No action required.**\n\n"
        for i, note in enumerate(learning, 1):
            review += f"{i}. {note}\n"
        review += "\n"

    # Add questions
    questions = findings.get('questions', [])
    if questions:
        review += "## ❓ [question] Clarifications needed\n\n"
        for i, question in enumerate(questions, 1):
            review += f"{i}. {question}\n"
        review += "\n"

    # Add praise
    praise = findings.get('praise', [])
    if praise:
        review += "## 🎉 [praise] Positive notes\n\n"
        for item in praise:
            review += f"- {item}\n"
        review += "\n"

    # Add overall recommendation
    review += "## Overall Recommendation\n\n"
    if blockers:
        review += "**Request Changes** - Critical issues must be addressed.\n"
    elif important:
        review += "**Request Changes** - Important issues should be fixed.\n"
    else:
        review += "**Approve** - Looks good! Minor nits can be addressed optionally.\n"

    return review


def generate_human_review(findings: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    """
    Generate short, clean human.md for posting.

    Rules:
    - No emojis
    - No em dashes (use regular hyphens)
    - No code line numbers
    - Concise and professional
    """

    def clean_text(text: str) -> str:
        """Remove em-dashes and replace with regular hyphens."""
        if not text:
            return text
        # Replace em dash (—) with regular hyphen (-)
        # Also replace en dash (–) with regular hyphen
        return text.replace('—', '-').replace('–', '-')

    title = clean_text(metadata.get('title', 'N/A'))
    summary = clean_text(findings.get('summary', 'No summary provided'))

    review = f"""# Code Review

**PR #{metadata.get('number', 'N/A')}**: {title}

## Summary

{summary}

"""

    # Add blockers - no emojis, but keep bracketed [blocking] tag
    blockers = findings.get('blockers', [])
    if blockers:
        review += "## [blocking] Critical Issues - Must Fix\n\n"
        for i, blocker in enumerate(blockers, 1):
            # No emojis, no em dashes, no line numbers
            issue = clean_text(blocker.get('issue', 'Issue'))
            details = clean_text(blocker.get('details', 'No details'))
            fix = clean_text(blocker.get('fix', ''))

            review += f"{i}. [blocking] **{issue}**\n"
            if blocker.get('file'):
                # File path without line number
                review += f"   - File: `{blocker['file']}`\n"
            review += f"   - {details}\n"
            if fix:
                review += f"   - Fix: {fix}\n"
            review += "\n"

    # Add important issues
    important = findings.get('important', [])
    if important:
        review += "## [important] Issues - Should Fix\n\n"
        for i, issue_item in enumerate(important, 1):
            issue = clean_text(issue_item.get('issue', 'Issue'))
            details = clean_text(issue_item.get('details', 'No details'))
            fix = clean_text(issue_item.get('fix', ''))

            review += f"{i}. [important] **{issue}**\n"
            if issue_item.get('file'):
                review += f"   - File: `{issue_item['file']}`\n"
            review += f"   - {details}\n"
            if fix:
                review += f"   - Suggestion: {fix}\n"
            review += "\n"

    # Add nits - keep brief
    nits = findings.get('nits', [])
    if nits and len(nits) <= 3:  # Only include if few
        review += "## [nit] Minor Issues\n\n"
        for i, nit in enumerate(nits, 1):
            issue = clean_text(nit.get('issue', 'Issue'))
            review += f"{i}. [nit] {issue}"
            if nit.get('file'):
                review += f" in `{nit['file']}`"
            review += "\n"
        review += "\n"

    # Add praise
    praise = findings.get('praise', [])
    if praise:
        review += "## [praise] Positive Notes\n\n"
        for item in praise:
            clean_item = clean_text(item)
            review += f"- {clean_item}\n"
        review += "\n"

    # Add overall recommendation - no emojis
    if blockers:
        review += "## Recommendation\n\nRequest changes - critical issues need to be addressed before merging.\n"
    elif important:
        review += "## Recommendation\n\nRequest changes - please address the important issues listed above.\n"
    else:
        review += "## Recommendation\n\nApprove - the code looks good. Minor items can be addressed optionally.\n"

    return review


def generate_inline_comments_file(findings: Dict[str, Any]) -> str:
    """
    Generate inline.md with list of proposed inline comments.

    Includes code snippets with line number headers.
    """

    inline_comments = findings.get('inline_comments', [])

    if not inline_comments:
        return "# Inline Comments\n\nNo inline comments proposed.\n"

    content = "# Proposed Inline Comments\n\n"
    content += f"**Total Comments**: {len(inline_comments)}\n\n"
    content += "Review these before posting. Edit as needed.\n\n"
    content += "---\n\n"

    for i, comment in enumerate(inline_comments, 1):
        content += f"## Comment {i}\n\n"
        content += f"**File**: `{comment.get('file', 'unknown')}`\n"
        content += f"**Line**: {comment.get('line', 'N/A')}\n"

        if comment.get('start_line') and comment.get('end_line'):
            content += f"**Range**: Lines {comment['start_line']}-{comment['end_line']}\n"

        content += f"\n**Comment**:\n{comment.get('comment', 'No comment')}\n\n"

        if comment.get('code_snippet'):
            # Add line numbers in header
            start = comment.get('start_line', comment.get('line', 1))
            end = comment.get('end_line', comment.get('line', 1))

            if start == end:
                content += f"**Code (Line {start})**:\n"
            else:
                content += f"**Code (Lines {start}-{end})**:\n"

            content += f"```\n{comment['code_snippet']}\n```\n\n"

        # Add command to post this comment
        owner = comment.get('owner', 'OWNER')
        repo = comment.get('repo', 'REPO')
        pr_num = comment.get('pr_number', 'PR_NUM')

        content += "**Command to post**:\n```bash\n"
        content += f"python scripts/add_inline_comment.py {owner} {repo} {pr_num} latest \\\n"
        content += f"  \"{comment.get('file', 'file.py')}\" {comment.get('line', 42)} \\\n"
        content += f"  \"{comment.get('comment', 'comment')}\"\n"
        content += "```\n\n"
        content += "---\n\n"

    return content


def resolve_repo(metadata: Dict[str, Any]) -> Tuple[str, str]:
    """Resolve owner and repo from explicit fields or an owner/repo repository."""
    owner = metadata.get('owner')
    repo = metadata.get('repo')
    repository = metadata.get('repository')

    if (not owner or not repo) and isinstance(repository, str) and "/" in repository:
        resolved_owner, resolved_repo = repository.split("/", 1)
        owner = owner or resolved_owner
        repo = repo or resolved_repo

    return str(owner or 'owner'), str(repo or 'repo')


def build_claude_command_contents(
    pr_review_dir: Path,
    metadata: Dict[str, Any],
    show_command: str,
    send_command: str,
    send_decline_command: str,
) -> Dict[str, str]:
    """Build slash command content using absolute review file paths."""
    owner, repo = resolve_repo(metadata)
    pr_number = str(metadata.get('number', '123'))

    review_file = pr_review_dir / "pr" / "review.md"
    human_file = pr_review_dir / "pr" / "human.md"
    inline_file = pr_review_dir / "pr" / "inline.md"
    sentinel_file = pr_review_dir / ".human_reviewed"

    pr_review_dir_q = shlex.quote(str(pr_review_dir))
    review_file_q = shlex.quote(str(review_file))
    human_file_q = shlex.quote(str(human_file))
    inline_file_q = shlex.quote(str(inline_file))
    sentinel_file_q = shlex.quote(str(sentinel_file))

    gate_refusal = (
        f"This review has not been opened in your IDE. Run {show_command} first, "
        f"read {review_file} and {human_file}, edit anything that doesn't sound "
        "like you, then come back. The byline on this review is going to say "
        "it's from you - make sure it actually is."
    )

    send_cmd = f"""Post the human-friendly review and approve the PR.

This command is gated: it will refuse to run unless the reviewer has opened the
review in their IDE via {show_command}. The point is to make sure a human
actually looked at the review before it gets posted under their name.

Steps:
1. Check that `{sentinel_file}` exists.
   - You can verify this with `test -f {sentinel_file_q}`.
   - If it does NOT exist, STOP. Tell the user verbatim:
     "{gate_refusal}"
     Do not proceed to any of the steps below.
2. Read the file `{human_file}`.
3. Post the review content as a PR comment using:
   `gh pr comment {pr_number} --repo {owner}/{repo} --body-file {human_file_q}`
4. Approve the PR using:
   `gh pr review {pr_number} --repo {owner}/{repo} --approve`
5. Confirm to the user that the review was posted and PR was approved.
"""

    send_decline_cmd = f"""Post the human-friendly review and request changes on the PR.

This command is gated: it will refuse to run unless the reviewer has opened the
review in their IDE via {show_command}. The point is to make sure a human
actually looked at the review before it gets posted under their name.

Steps:
1. Check that `{sentinel_file}` exists.
   - You can verify this with `test -f {sentinel_file_q}`.
   - If it does NOT exist, STOP. Tell the user verbatim:
     "{gate_refusal}"
     Do not proceed to any of the steps below.
2. Read the file `{human_file}`.
3. Post the review content as a PR comment using:
   `gh pr comment {pr_number} --repo {owner}/{repo} --body-file {human_file_q}`
4. Request changes on the PR using:
   `gh pr review {pr_number} --repo {owner}/{repo} --request-changes`
5. Confirm to the user that the review was posted and changes were requested.
"""

    show_cmd = f"""Open the PR review directory in your IDE for human review.

This step is mandatory. {send_command} and {send_decline_command} are gated on
the `.human_reviewed` sentinel that this command writes - they will refuse to
post anything until you have run {show_command}.

Steps:
1. Run `code {pr_review_dir_q} {review_file_q} {human_file_q} {inline_file_q}` to
   open the review directory and review files in VS Code (or whichever editor
   the user prefers - the goal is that a human actually looks at the review).
2. Write a sentinel file `{sentinel_file}` containing:
   - The line `Reviewed by human at <ISO 8601 timestamp>` using the current time.
   - The line `Files opened: {review_file}, {human_file}, {inline_file}`.
3. Tell the user:
   - The review files are now open: {review_file}, {human_file}, {inline_file}.
   - They should read {human_file} (this is what gets posted) and edit anything
     that doesn't sound like them.
   - When they are satisfied that the review represents their own judgement,
     they can run {send_command} (approve) or {send_decline_command} (request changes).
"""

    return {
        "show": show_cmd,
        "send": send_cmd,
        "send-decline": send_decline_cmd,
    }


def write_claude_commands(
    claude_dir: Path,
    command_contents: Dict[str, str],
    command_filenames: Dict[str, str],
) -> None:
    """Write command content into a .claude/commands directory."""
    claude_dir.mkdir(parents=True, exist_ok=True)

    for command_key, filename in command_filenames.items():
        with open(claude_dir / filename, 'w') as f:
            f.write(command_contents[command_key])


def generate_claude_commands(
    pr_review_dir: Path,
    metadata: Dict[str, Any],
    project_dir: Optional[Path] = None,
):
    """Generate .claude directory with custom slash commands."""
    pr_number = str(metadata.get('number', '123'))

    claude_dir = pr_review_dir / ".claude" / "commands"
    command_contents = build_claude_command_contents(
        pr_review_dir,
        metadata,
        show_command="/show",
        send_command="/send",
        send_decline_command="/send-decline",
    )
    write_claude_commands(
        claude_dir,
        command_contents,
        {
            "show": "show.md",
            "send": "send.md",
            "send-decline": "send-decline.md",
        },
    )

    print(f"✅ Created slash commands in {claude_dir}")
    print("   - /show (MANDATORY - open in IDE, writes .human_reviewed sentinel)")
    print("   - /send (approve and post; refuses without sentinel)")
    print("   - /send-decline (request changes and post; refuses without sentinel)")

    if project_dir:
        project_claude_dir = project_dir / ".claude" / "commands"
        project_command_contents = build_claude_command_contents(
            pr_review_dir,
            metadata,
            show_command=f"/pr-{pr_number}-show",
            send_command=f"/pr-{pr_number}-send",
            send_decline_command=f"/pr-{pr_number}-send-decline",
        )
        write_claude_commands(
            project_claude_dir,
            project_command_contents,
            {
                "show": f"pr-{pr_number}-show.md",
                "send": f"pr-{pr_number}-send.md",
                "send-decline": f"pr-{pr_number}-send-decline.md",
            },
        )

        print(f"✅ Created project slash commands in {project_claude_dir}")
        print(f"   - /pr-{pr_number}-show (MANDATORY - open in IDE, writes .human_reviewed sentinel)")
        print(f"   - /pr-{pr_number}-send (approve and post; refuses without sentinel)")
        print(f"   - /pr-{pr_number}-send-decline (request changes and post; refuses without sentinel)")


def generate_review_ready_summary(
    pr_review_dir: Path,
    metadata: Dict[str, Any],
    project_dir: Optional[Path] = None,
) -> str:
    """Generate REVIEW_READY.txt content."""
    pr_number = str(metadata.get('number', '123'))

    if project_dir:
        command_section = f"""Slash commands from the project directory (run in this order):
1. /pr-{pr_number}-show           - MANDATORY: open the review in your IDE so a human (you)
                                    actually reads it. Writes a `.human_reviewed` sentinel.
2. /pr-{pr_number}-send           - Post human.md and approve PR (refuses without sentinel)
   /pr-{pr_number}-send-decline   - Post human.md and request changes (refuses without sentinel)

Legacy slash commands from the review directory:
- /show
- /send
- /send-decline
"""
        next_steps = f"""Next steps:
1. From {project_dir}, run /pr-{pr_number}-show. Read {pr_review_dir / "pr" / "human.md"} -
   this is what will be posted under your name. Edit anything that doesn't sound like you.
2. When you're satisfied, run /pr-{pr_number}-send or /pr-{pr_number}-send-decline.
"""
        important = (
            f"IMPORTANT: Nothing will be posted until you run /pr-{pr_number}-show, "
            f"then /pr-{pr_number}-send or /pr-{pr_number}-send-decline."
        )
    else:
        command_section = """Slash commands (run in this order):
1. /show           - MANDATORY: open the review in your IDE so a human (you)
                     actually reads it. Writes a `.human_reviewed` sentinel.
2. /send           - Post human.md and approve PR (refuses without sentinel)
   /send-decline   - Post human.md and request changes (refuses without sentinel)
"""
        next_steps = """Next steps:
1. Run /show. Read pr/human.md - this is what will be posted under your name.
   Edit anything that doesn't sound like you.
2. When you're satisfied, run /send or /send-decline.
"""
        important = "IMPORTANT: Nothing will be posted until you run /show, then /send or /send-decline."

    return f"""PR Review Files Generated
========================

Directory: {pr_review_dir}

Files created:
- pr/review.md      - Detailed analysis for your review
- pr/human.md       - Clean version for posting (no emojis, no line numbers)
- pr/inline.md      - Proposed inline comments with code snippets

{command_section}
Why the show command is mandatory:
   If a human is named as the reviewer, they should actually look at the code.
   The send commands will refuse to post anything until the show command has
   run. This makes the human-in-the-loop step explicit instead of optional.

{next_steps}
{important}
"""


def main():
    parser = argparse.ArgumentParser(
        description='Generate structured review files from PR analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('pr_review_dir', help='PR review directory path')
    parser.add_argument('--findings', required=True, help='JSON file with review findings')
    parser.add_argument('--metadata', help='JSON file with PR metadata (optional)')
    parser.add_argument(
        '--project-dir',
        help='Project root where PR-specific slash commands should be deployed (optional)'
    )

    args = parser.parse_args()

    try:
        # Load findings
        findings = load_findings(args.findings)

        # Load metadata if provided
        metadata = {}
        if args.metadata and os.path.exists(args.metadata):
            with open(args.metadata, 'r') as f:
                metadata = json.load(f)

        # Extract metadata from findings if not provided
        if not metadata:
            metadata = findings.get('metadata', {})

        # Resolve directories
        pr_review_dir = Path(args.pr_review_dir).expanduser().resolve()
        project_dir = None
        if args.project_dir:
            project_dir = Path(args.project_dir).expanduser().resolve()
            if not project_dir.is_dir():
                raise ValueError(f"--project-dir must exist and be a directory: {project_dir}")

        # Create pr directory
        pr_dir = create_pr_directory(pr_review_dir)

        print(f"📝 Generating review files in {pr_dir}...")

        # Generate detailed review
        detailed_review = generate_detailed_review(findings, metadata)
        review_file = pr_dir / "review.md"
        with open(review_file, 'w') as f:
            f.write(detailed_review)
        print(f"✅ Created detailed review: {review_file}")

        # Generate human-friendly review
        human_review = generate_human_review(findings, metadata)
        human_file = pr_dir / "human.md"
        with open(human_file, 'w') as f:
            f.write(human_review)
        print(f"✅ Created human review: {human_file}")

        # Generate inline comments file
        inline_comments = generate_inline_comments_file(findings)
        inline_file = pr_dir / "inline.md"
        with open(inline_file, 'w') as f:
            f.write(inline_comments)
        print(f"✅ Created inline comments: {inline_file}")

        # Generate Claude slash commands
        generate_claude_commands(pr_review_dir, metadata, project_dir)

        # Create summary file
        summary = generate_review_ready_summary(pr_review_dir, metadata, project_dir)

        summary_file = pr_review_dir / "REVIEW_READY.txt"
        with open(summary_file, 'w') as f:
            f.write(summary)

        print(f"\n{summary}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
