"""
Git diff review templates.

This module provides templates for the gemini_git_diff_review tool.
"""
from typing import Optional
from .base_template import BaseTemplate


def get_git_diff_review_prompt(
    diff: str,
    context_lines: int = 3,
    review_type: str = "comprehensive",
    base_branch: Optional[str] = None,
    commit_message: Optional[str] = None
) -> str:
    """
    Generate a git diff review prompt.

    Args:
        diff: Git diff content
        context_lines: Number of context lines
        review_type: Type of review
        base_branch: Base branch
        commit_message: Commit message

    Returns:
        Complete prompt string
    """
    branch_section = f"\nBase Branch: {base_branch}" if base_branch else ""
    commit_section = f"\nCommit Message: {commit_message}" if commit_message else ""

    review_focus = {
        "comprehensive": """
Review Focus: Comprehensive
- Code quality
- Security implications
- Performance impact
- Best practices
- Test coverage""",
        "security_only": """
Review Focus: Security Only
- Vulnerability introduction
- Authentication/authorization changes
- Data exposure risks
- Input validation
- Secure coding practices""",
        "performance_only": """
Review Focus: Performance Only
- Algorithm efficiency
- Database query changes
- Memory usage
- I/O operations
- Caching implications""",
        "quick": """
Review Focus: Quick Review
- Critical issues only
- Breaking changes
- Obvious bugs"""
    }.get(review_type, "")

    return f"""Review the following git diff and provide feedback.{branch_section}{commit_section}
{review_focus}

Git Diff:
```diff
{diff}
```

Please provide:

## 1. Change Summary
- What changes are being made?
- Files affected
- Type of change (feature, bugfix, refactor, etc.)

## 2. Code Quality Assessment

### Added Code
- Quality of new code
- Consistency with existing style
- Documentation

### Removed Code
- Impact of removals
- Potential regressions

### Modified Code
- Appropriateness of changes
- Side effects

## 3. Issues Found

| Severity | File | Line | Issue | Suggestion |
|----------|------|------|-------|------------|
| [Critical/High/Medium/Low] | [file] | [line] | [issue] | [fix] |

## 4. Security Analysis
- New vulnerabilities introduced?
- Security improvements?
- Sensitive data handling

## 5. Performance Impact
- Potential performance changes
- Optimization opportunities

## 6. Test Considerations
- New tests needed?
- Existing tests affected?
- Edge cases to consider

## 7. Recommendations
### Must Address
- Critical items before merge

### Should Consider
- Important improvements

### Nice to Have
- Optional enhancements

## 8. Verdict
- [ ] Approve
- [ ] Approve with suggestions
- [ ] Request changes
- [ ] Reject

**Summary:** [Brief assessment]"""


class GitDiffReviewTemplate(BaseTemplate):
    """Template class for git diff review."""

    @staticmethod
    def get_prompt(
        diff: str,
        context_lines: int = 3,
        review_type: str = "comprehensive",
        base_branch: Optional[str] = None,
        commit_message: Optional[str] = None
    ) -> str:
        """Get the git diff review prompt."""
        return get_git_diff_review_prompt(
            diff, context_lines, review_type, base_branch, commit_message
        )
