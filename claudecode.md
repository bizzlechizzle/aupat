# AUPAT Development Methodology

## Purpose

This document defines the bulletproof workflow for all code development, troubleshooting, planning, and brainstorming in the AUPAT project. Follow these steps religiously to maintain code quality, reliability, and long-term maintainability.

---

## Core Principles (In Order of Importance)

### 1. BPA - Best Practices Always
- Never compromise on industry best practices
- Code must follow established patterns and standards
- Security, performance, and maintainability come first
- Research best practices before implementing anything new
- When in doubt, choose the battle-tested approach

### 2. BPL - Bulletproof Longterm
- Code must survive years of use without modification
- Anticipate future edge cases and failure modes
- Build defensive systems that fail gracefully
- Prioritize data integrity above all else
- No technical debt - do it right the first time

### 3. KISS - Keep It Simple Stupid
- Simplicity trumps cleverness
- If it requires extensive comments to understand, it's too complex
- Prefer readable code over performant code (unless performance is critical)
- One function, one purpose
- Avoid over-engineering

### 4. FAANG PE - FAANG-Level Engineering (Personal Edition)
- Production-grade code quality without enterprise bloat
- Scalable architecture appropriate for small business needs
- Proper error handling, logging, and monitoring
- Code review standards (self-review thoroughly)
- Think like a senior engineer at a top tech company, but stay pragmatic

### 5. WWYDD - What Would You Do Differently Logic
- Only invoke when there's an urgent, major, or fatal flaw
- Challenge the plan when something feels fundamentally wrong
- Ask: "If I had to rebuild this in 5 years, what would I regret?"
- Don't be afraid to scrap and restart if the foundation is broken
- Trust your instincts when code smells bad

### 6. NEE - NO EMOJIS EVER
- Professional documentation only
- Emojis are distracting and unprofessional
- Use clear, concise language instead
- Markdown formatting for emphasis (bold, italic, code blocks)

### 7. No Self-Credit
- Don't credit tooling in code comments or documentation
- Code speaks for itself
- Focus on what the code does, not who/what wrote it
- Attribution is tacky and adds noise

---

## When-Applicable Rules

### Transaction Safety (Database Operations)
- Wrap all database modifications in BEGIN/COMMIT/ROLLBACK
- Define clear transaction boundaries
- Implement rollback procedures for every operation
- Test rollback scenarios explicitly
- Never leave database in inconsistent state

### PRAGMA foreign_keys = ON (SQLite)
- Always enable foreign key constraints
- Verify cascade behavior is correct (DELETE, UPDATE)
- Test foreign key violations explicitly
- Document all relationships in foreign-keys.md

### Error Handling (All Code)
- Try/except blocks for every external call
- Specific exception types, not bare except
- Log errors with context (what failed, why, what was attempted)
- Graceful degradation when possible
- Fail fast when data integrity at risk

### Input Validation (All User Input)
- Never trust user input
- Validate types, ranges, formats, lengths
- Sanitize for SQL injection, path traversal, XSS
- Fail early with clear error messages
- Document validation rules

---

## The Bulletproof Workflow

### Step 1: Audit the Code
**Purpose**: Verify current state and identify gaps

Tasks:
- Read all relevant .py script files completely
- Read all related .md documentation files
- Read all .json configuration files
- Read implementation guides and best practices documentation
- Compare code against documentation (are they in sync?)
- Identify what's complete vs incomplete
- List all dependencies and verify they exist
- Check for obvious bugs, security issues, or logic flaws

Output:
- Audit report listing:
  - Files reviewed
  - Current implementation status
  - Gaps between documentation and code
  - Identified issues (bugs, security, logic, style)
  - Missing components

### Step 2: Draft the Plan
**Purpose**: Create clear, actionable plan to fix/implement

Tasks:
- Define the goal (what are we trying to accomplish?)
- List all files that need to be created/modified
- Outline the changes needed in each file
- Define success criteria (how do we know it works?)
- Identify risks and mitigation strategies
- Estimate complexity (simple, moderate, complex)
- Sequence operations in logical order

Output:
- Written plan with:
  - Objective statement
  - File-by-file change list
  - Sequencing/dependencies
  - Success criteria
  - Risk assessment

### Step 3: Audit the Plan (First Pass)
**Purpose**: Ensure plan follows all core principles

Tasks:
- Check against BPA: Does it follow best practices?
- Check against BPL: Will this work in 5 years?
- Check against KISS: Is it as simple as possible?
- Check against FAANG PE: Is it production-grade?
- Check against WWYDD: Any fatal flaws?
- Check Python best practices (PEP 8, typing, docstrings)
- Check database best practices (indexes, transactions, normalization)
- Check security best practices (input validation, SQL injection, etc.)
- Verify transaction safety for database operations
- Verify error handling for all failure modes

Output:
- Updated plan incorporating feedback
- List of principle violations fixed
- Rationale for any deviations from principles

### Step 4: Deep Review and Re-Audit
**Purpose**: Catch errors before implementation

Tasks:
- Re-read ALL related files (.py, .md, .json, .pdf) again
- Verify plan matches reality (no stale assumptions)
- Check for consistency across all documentation
- Look for edge cases not covered in plan
- Verify dependencies are correctly identified
- Confirm file paths, variable names, function names are accurate
- Double-check SQL queries for correctness
- Review error handling paths

Output:
- Final audited plan
- Confirmation that plan is accurate and complete
- List of edge cases to test

### Step 5: Write Implementation Guide
**Purpose**: Create clear instructions for implementation

Tasks:
- Write step-by-step guide for less-experienced coder
- Explain WHY each change is needed, not just WHAT
- Include code examples with explanations
- Document core logic and algorithms
- Explain tricky parts in detail
- Include links to relevant documentation
- Add warnings for common pitfalls
- Describe expected behavior at each step

Output:
- Implementation guide with:
  - Prerequisites/setup
  - Step-by-step instructions
  - Code snippets with explanations
  - Expected outcomes
  - Troubleshooting tips

### Step 6: Audit Implementation Guide
**Purpose**: Ensure guide is clear and complete

Tasks:
- Read guide from perspective of junior developer
- Verify all steps are clear and unambiguous
- Check that core logic is explained thoroughly
- Ensure code examples are correct and complete
- Confirm troubleshooting section covers likely issues
- Fix any confusing language or gaps
- Add diagrams/examples if helpful

Output:
- Refined implementation guide
- Confirmation guide is comprehensive and clear

### Step 7: Write/Update the Code
**Purpose**: Implement the planned changes

Tasks:
- Follow implementation guide exactly
- Write clean, readable code
- Add docstrings for all functions/classes
- Add inline comments for complex logic only
- Follow naming conventions consistently
- Implement error handling for all external calls
- Add logging at appropriate levels
- Include input validation
- Implement transaction safety where applicable
- Keep functions small and focused

Output:
- Updated .py files
- Updated .md documentation if needed
- Updated .json configuration if needed

### Step 8: Test End-to-End
**Purpose**: Verify code works as intended

Tasks:
- Test happy path (everything works perfectly)
- Test error paths (files missing, bad input, etc.)
- Test edge cases identified in audit
- Test rollback/recovery procedures
- Verify logging output is useful
- Check database state before/after operations
- Test with small dataset first, then larger
- Verify no data corruption
- Test idempotency (can it run twice safely?)
- Performance check (is it reasonably fast?)

Output:
- Test results document with:
  - What was tested
  - Expected vs actual results
  - Any issues found and fixed
  - Performance metrics
  - Confirmation all tests pass

### Step 9: Final Audit and Documentation
**Purpose**: Ensure everything is production-ready

Tasks:
- Re-read all modified code
- Verify code matches documentation
- Check for any remaining TODO comments
- Verify all imports are used
- Check for unused variables/functions
- Update version tracking if applicable
- Update changelog/commit message draft
- Confirm all principles were followed
- Final check for emojis or self-credit (remove them)

Output:
- Production-ready code
- Updated documentation
- Commit message describing changes
- Confidence that code is bulletproof

---

## Troubleshooting Workflow

When code isn't working:

1. Read error messages completely and carefully
2. Verify input data is valid and expected format
3. Check logs for detailed error context
4. Isolate the failing component (which function/step fails?)
5. Test that component in isolation
6. Verify assumptions (does file exist? Is database writable?)
7. Check recent changes (what changed since it last worked?)
8. Add more logging if needed to understand state
9. Fix root cause, not symptoms
10. Test fix thoroughly before moving on
11. Document the issue and solution

---

## Planning Workflow

When planning new features:

1. Define the problem clearly (what are we solving?)
2. Research existing solutions and best practices
3. Draft multiple approaches (at least 2-3 options)
4. Evaluate each against core principles
5. Choose best approach (simplest that meets all principles)
6. Follow full 9-step workflow for implementation

---

## Brainstorming Workflow

When exploring ideas:

1. State the goal/challenge clearly
2. Generate ideas without filtering (quantity over quality)
3. After exhausting ideas, apply principle filters:
   - Which are BPA?
   - Which are BPL?
   - Which are KISS?
   - Which meet FAANG PE standards?
4. Narrow to top 2-3 ideas
5. Prototype or deeply analyze finalists
6. Choose winner based on principles + feasibility
7. Proceed with planning workflow

---

## Code Review Checklist

Before committing any code, verify:

- [ ] Code follows all core principles (BPA, BPL, KISS, FAANG PE)
- [ ] No emojis anywhere
- [ ] No self-credit or tool attribution
- [ ] All functions have docstrings
- [ ] Error handling for all external calls
- [ ] Input validation for all user input
- [ ] Transaction safety for database operations
- [ ] PRAGMA foreign_keys = ON in database code
- [ ] Logging at appropriate levels
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] No TODO comments left
- [ ] No dead code or unused imports
- [ ] Naming follows conventions
- [ ] Code is readable without excessive comments
- [ ] Edge cases handled
- [ ] Rollback procedures implemented

---

## Documentation Standards

All .md files should:
- Use clear, concise language
- Avoid marketing speak or hype
- Focus on facts and implementation details
- Include examples where helpful
- Follow consistent formatting
- Link to related documentation
- Specify versions/dependencies where applicable
- Be accurate and up-to-date with code

All .py files should:
- Include module-level docstring describing purpose
- Include function/class docstrings (Google style)
- Use type hints for function parameters and returns
- Follow PEP 8 style guide
- Use meaningful variable/function names
- Keep line length under 100 characters
- Avoid magic numbers (use named constants)

All .json files should:
- Use consistent indentation (2 or 4 spaces)
- Include version field where applicable
- Validate against schema if one exists
- Document structure in corresponding .md file

---

## Emergency Override

If you discover a critical flaw (data loss risk, security vulnerability, fundamental design error):

1. STOP immediately
2. Invoke WWYDD
3. Document the flaw clearly
4. Assess impact (how bad is it?)
5. Draft emergency fix plan
6. Get approval before proceeding (if applicable)
7. Fix with extreme care
8. Test exhaustively
9. Document in post-mortem

Data integrity always trumps deadlines.

---

## Principle Conflict Resolution

If principles conflict:

1. BPA overrides all (best practices are non-negotiable)
2. BPL overrides KISS when long-term reliability is at stake
3. KISS overrides FAANG PE when simplicity prevents bugs
4. WWYDD can override anything if flaw is critical
5. When truly stuck, choose the option that protects data integrity

---

## Success Metrics

Good code following this methodology will have:
- Zero data loss or corruption incidents
- Clear, understandable implementation
- Comprehensive error handling
- Thorough logging for debugging
- High test coverage
- Accurate documentation
- Easy maintenance and modification
- Graceful failure modes
- Predictable behavior

---

## Version History

Track major methodology changes here:
- v1.0 - Initial methodology document

---

## References

Internal documentation:
- All .md files in logseq/pages/
- All .json schema files
- All .py implementation files

External references:
- PEP 8 - Python Style Guide
- SQLite Best Practices
- OWASP Top 10 Security
- Python typing module documentation
- SQLite JSON1 extension documentation
