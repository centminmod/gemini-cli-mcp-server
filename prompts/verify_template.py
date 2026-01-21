"""
Solution verification templates.

This module provides templates for the gemini_verify_solution tool.
"""
from typing import Optional
from .base_template import BaseTemplate


def get_verify_solution_prompt(
    solution: str,
    requirements: Optional[str] = None,
    test_criteria: Optional[str] = None,
    context: Optional[str] = None
) -> str:
    """
    Generate a solution verification prompt.

    Args:
        solution: Complete solution to verify
        requirements: Original requirements
        test_criteria: Testing and performance criteria
        context: Deployment context

    Returns:
        Complete prompt string
    """
    requirements_section = ""
    if requirements:
        requirements_section = f"""

Original Requirements:
{requirements}
"""

    criteria_section = ""
    if test_criteria:
        criteria_section = f"""

Test Criteria:
{test_criteria}
"""

    context_section = ""
    if context:
        context_section = f"""

Deployment Context:
{context}
"""

    return f"""Please perform a comprehensive verification of the following solution.{requirements_section}{criteria_section}{context_section}

Solution:
{solution}

Please verify the solution against the following criteria:

## 1. Requirements Compliance

### Requirements Checklist
| Requirement | Status | Evidence | Notes |
|-------------|--------|----------|-------|
| [List each requirement] | [Met/Partially Met/Not Met] | [Where addressed] | [Comments] |

### Coverage Score: [0-100%]

## 2. Code Correctness

### Functional Verification
- Does the code do what it's supposed to do?
- Are all use cases handled?
- Are error conditions managed?

### Logic Analysis
- Algorithm correctness
- Data flow integrity
- State management

## 3. Security Assessment

### Vulnerability Scan
| Category | Risk Level | Finding | Remediation |
|----------|------------|---------|-------------|
| [Category] | [Critical/High/Medium/Low] | [Issue] | [Fix] |

### Security Score: [1-10]

## 4. Performance Evaluation

### Performance Metrics
- Time complexity analysis
- Space complexity analysis
- Scalability assessment

### Performance Concerns
- Potential bottlenecks
- Resource usage issues

### Performance Score: [1-10]

## 5. Test Coverage

### Test Analysis
- Unit test coverage estimate
- Integration test coverage
- Edge cases covered

### Missing Tests
- List of untested scenarios
- Critical paths without tests

### Test Score: [1-10]

## 6. Production Readiness

### Checklist
- [ ] Error handling complete
- [ ] Logging implemented
- [ ] Configuration externalized
- [ ] Documentation adequate
- [ ] Monitoring hooks in place
- [ ] Graceful degradation
- [ ] Rollback strategy

### Readiness Level: [Production Ready/Needs Work/Not Ready]

## 7. Code Quality

### Quality Metrics
- Maintainability index
- Code duplication
- Complexity assessment

## 8. Documentation Review
- API documentation
- Code comments
- README/setup instructions

## 9. Deployment Considerations
- Environment requirements
- Dependencies
- Configuration needs
- Migration requirements

## 10. Final Verdict

### Overall Assessment
| Aspect | Score | Status |
|--------|-------|--------|
| Requirements | [1-10] | [Pass/Fail] |
| Security | [1-10] | [Pass/Fail] |
| Performance | [1-10] | [Pass/Fail] |
| Testing | [1-10] | [Pass/Fail] |
| Quality | [1-10] | [Pass/Fail] |

### Recommendation: [Approve/Approve with Conditions/Reject]

### Required Actions Before Deployment
1. [List critical items]

### Summary
[2-3 sentence summary of the verification results]"""


class VerifyTemplate(BaseTemplate):
    """Template class for solution verification prompts."""

    @staticmethod
    def get_prompt(
        solution: str,
        requirements: Optional[str] = None,
        test_criteria: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """Get the solution verification prompt."""
        return get_verify_solution_prompt(solution, requirements, test_criteria, context)
