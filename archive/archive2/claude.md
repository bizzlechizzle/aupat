# Claude AI Development Guidelines for AUPAT

Version: 1.0.0
Last Updated: 2025-11-18

---

## THE RULES

### KISS - Keep It Simple, Stupid
Write simple, readable, maintainable code. Avoid over-engineering. Choose clarity over cleverness. If a solution feels complex, step back and find a simpler approach.

**Examples:**
- Use clear variable names instead of abbreviations
- Prefer straightforward logic over nested conditionals
- Break complex functions into smaller, single-purpose functions
- Avoid premature optimization

### FAANG PE - FAANG-Level Engineering for Small Teams
Apply enterprise-grade engineering practices at startup scale. Write production-ready code with proper error handling, logging, testing, and documentation.

**Standards:**
- Code reviews for all changes
- Automated testing with minimum 70% coverage
- Comprehensive error handling
- Structured logging with context
- API versioning and backward compatibility
- Security best practices (input validation, SQL injection prevention, XSS protection)
- Performance monitoring and optimization

### BPL - Bulletproof Long-Term (3-10+ years)
Design for longevity. Code should be maintainable, upgradeable, and understandable by future developers. Prioritize sustainability over quick fixes.

**Practices:**
- Use stable, well-maintained dependencies
- Document design decisions and trade-offs
- Write self-documenting code with clear comments
- Create upgrade paths for breaking changes
- Use semantic versioning
- Plan for database migrations
- Design for backward compatibility

### BPA - Best Practices Always
Always check up-to-date official documentation for tools, frameworks, CLIs, and Python standards. Never rely on outdated patterns or deprecated APIs.

**Resources to Check:**
- Python: PEP 8, typing, asyncio best practices
- Flask: Official documentation, security guidelines
- SQLite: Query optimization, transaction handling
- Electron: Security best practices, IPC patterns
- Svelte: Reactivity patterns, store management
- Docker: Multi-stage builds, security scanning

**Before implementing, verify:**
- Is this the recommended approach in 2025?
- Are there newer, better alternatives?
- What are the known pitfalls?
- What security considerations apply?

### NME - No Emojis Ever
Professional code and documentation. No emojis in code, comments, commit messages, or user-facing text unless explicitly requested.

**Exceptions:**
- User explicitly requests emojis
- Third-party documentation being quoted

### WWYDD - What Would You Do Differently
Always consider improvements and suggest alternatives. The user is a generalist, not a specialist. Proactive suggestions are encouraged.

**When to apply:**
- Before writing new code
- When reviewing existing code
- When planning architecture
- When choosing dependencies
- When designing APIs

**Suggestion format:**
```
Current approach: [description]
Alternative: [your suggestion]
Trade-offs: [pros and cons]
Recommendation: [your opinion with reasoning]
```

### DRETW - Don't Re-Invent The Wheel
Check GitHub, known scripts, Reddit, Stack Overflow before writing from scratch. If a well-maintained solution exists, use or adapt it. Credit sources.

**Search strategy:**
1. Check Python Package Index (PyPI)
2. Search GitHub for similar implementations
3. Check Stack Overflow for common patterns
4. Review Reddit discussions for real-world experiences
5. Examine existing codebase for similar code

**If borrowing code:**
- Add comment with source URL
- Check license compatibility
- Understand the code before using
- Adapt to project style
- Test thoroughly

### LILBITS - Always Write Scripts in Little Bits
One script = One function. Break functionality into small, testable, reusable modules. Document each new script in lilbits.md.

**Guidelines:**
- Maximum 200 lines per file (excluding tests)
- Each function does ONE thing
- Clear input/output contracts
- No side effects unless explicit
- Easy to test in isolation
- Reusable across project

**Example structure:**
```python
def parse_exif_data(image_path: str) -&gt; dict:
    """
    Extract EXIF metadata from image.

    Args:
        image_path: Absolute path to image file

    Returns:
        Dictionary with GPS, camera, date metadata

    Raises:
        FileNotFoundError: If image doesn't exist
        ExifToolError: If exiftool fails
    """
    # Single-purpose implementation
    pass
```

---

## CORE PROCESS

Follow this 10-step process for every task: fixing bugs, troubleshooting, coding, brainstorming, optimizing, or WWYDD analysis.

### Step 1: Read Context
Read and understand:
- User prompt (what is being asked)
- claude.md (this file - rules and process)
- techguide.md (technical architecture and file map)
- lilbits.md (existing scripts and their purposes)

**Output:** Clear understanding of the request and project context

### Step 2: Research Referenced Files
Search for and read:
- Any files/folders mentioned in the user prompt
- Related files outlined in techguide.md
- Dependent files from the file dependency map
- Similar code already in the codebase

**Tools:**
- Use Glob to find files by pattern
- Use Grep to search for keywords
- Use Read to examine file contents
- Use Task/Explore agent for broad searches

**Output:** Complete context of relevant code

### Step 3: Make a Plan
Create a detailed plan to:
- Fix the bug
- Troubleshoot the issue
- Write new code
- Brainstorm solutions
- Optimize performance
- Apply WWYDD analysis

**Plan should include:**
- Problem statement
- Root cause analysis (if applicable)
- Proposed solution
- Alternative approaches
- Files to modify/create
- Tests to write/update
- Documentation to update

**Make core logic for each type:**

**Fix plan:**
1. Identify bug location
2. Understand root cause
3. Design fix
4. Plan tests to verify fix
5. Plan regression tests

**Troubleshoot plan:**
1. Reproduce issue
2. Gather diagnostic info
3. Form hypotheses
4. Test hypotheses
5. Identify solution

**Code plan:**
1. Define requirements
2. Design architecture
3. Break into LILBITS
4. Plan test strategy
5. Plan integration

**Brainstorm plan:**
1. Understand constraints
2. Research options
3. List alternatives
4. Evaluate trade-offs
5. Recommend approach

**Optimize plan:**
1. Measure current performance
2. Identify bottlenecks
3. Research optimizations
4. Design improvements
5. Plan benchmarks

**Output:** Detailed plan document

### Step 4: Audit the Plan
Review plan against:
- Findings from Step 1 (rules and context)
- Findings from Step 2 (existing code)
- Best practices (BPA)
- Simplicity (KISS)
- Long-term maintainability (BPL)
- Existing patterns (DRETW)

**Questions to ask:**
- Does this follow project conventions?
- Is this the simplest solution?
- Will this be maintainable in 5 years?
- Are there better alternatives?
- Does this introduce technical debt?
- Are there security implications?

**Output:** Updated plan with improvements

### Step 5: Write Implementation Guide
Create a guide for a new coder to implement the plan. Assume they understand programming but don't know this codebase.

**Include:**
- Step-by-step instructions
- File locations with absolute paths
- Code snippets with context
- Expected inputs/outputs
- Error handling requirements
- Testing instructions
- Rollback procedures

**Format:**
```markdown
## Implementation Guide: [Feature Name]

### Prerequisites
- Tools required
- Dependencies to install
- Environment setup

### Step 1: [Action]
Location: /absolute/path/to/file.py
Action: [detailed description]
Code:
```python
# code here
```

### Step 2: [Action]
...

### Verification
1. Run tests: pytest tests/test_feature.py
2. Manual test: [instructions]
3. Expected output: [description]

### Rollback
If implementation fails:
1. [rollback step 1]
2. [rollback step 2]
```

**Output:** Complete implementation guide

### Step 6: Audit the Guide
Review implementation guide against:
- Step 1 findings (context)
- Step 2 findings (existing code)
- Step 4 (audited plan)
- Best practices for any program/script/tool used
- Official documentation for all tools

**Check:**
- Are paths correct?
- Are commands accurate?
- Are there missing steps?
- Are there security issues?
- Are there edge cases?
- Is error handling complete?

**Update guide based on findings**

**Output:** Audited and updated implementation guide

### Step 7: Write Technical Guide
Transform implementation guide into technical documentation with:
- Architecture diagrams
- Code examples
- Logic flow explanations
- API contracts
- Database schemas
- Error scenarios

**Include:**
- Why decisions were made
- Trade-offs considered
- Performance characteristics
- Security considerations
- Testing strategy
- Monitoring approach

**Output:** Technical documentation

### Step 8: Write/Update/Create
Execute the plan:
- Write new code
- Update existing code
- Create new files
- Modify configurations
- Write tests
- Update documentation

**Standards:**
- Follow LILBITS (small, focused files)
- Add type hints
- Include docstrings
- Handle errors gracefully
- Log important events
- Write tests first (TDD when possible)

**Output:** Working implementation

### Step 9: Audit the Fix
Review implementation against:
- Step 1 (context and rules)
- Step 2 (existing code patterns)
- Step 4 (audited plan)
- Step 6 (audited guide)
- Step 7 (technical guide)

**Testing checklist:**
- Unit tests pass
- Integration tests pass
- Manual testing complete
- Edge cases handled
- Error paths tested
- Performance acceptable
- Security verified
- Documentation accurate

**Update code based on findings**

**Output:** Production-ready code

### Step 10: Update Documentation
Update project documentation:
- techguide.md: Add/update file descriptions, dependencies, key rules
- lilbits.md: Document new scripts and their purposes
- README.md: Update if user-facing changes
- Inline comments: Explain complex logic
- Commit message: Clear description of changes

**Include:**
- What changed and why
- How it relates to other files
- Any breaking changes
- Migration guide if needed
- Performance impact
- Security considerations

**Output:** Complete, up-to-date documentation

---

## PROCESS APPLICATION

### For Every Task

1. Create task list with TodoWrite
2. Execute Core Process (Steps 1-10)
3. Update task list as you progress
4. Mark tasks complete when fully done
5. Never skip steps

### For Small Changes

Even for small changes, at minimum:
- Step 1: Read context
- Step 2: Check related files
- Step 3: Quick plan
- Step 8: Make change
- Step 10: Update docs

### For Large Features

Full 10-step process required:
- Document each step thoroughly
- Create separate files for guides
- Include architecture diagrams
- Comprehensive testing
- Full documentation update

---

## CODE QUALITY STANDARDS

### Python Code

**Type hints required:**
```python
from typing import Optional, List, Dict, Any

def get_location(uuid: str) -&gt; Optional[Dict[str, Any]]:
    """Get location by UUID."""
    pass
```

**Error handling required:**
```python
try:
    result = operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise
except Exception as e:
    logger.exception("Unexpected error")
    raise
```

**Logging required:**
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Starting operation", extra={"uuid": uuid})
logger.error("Operation failed", extra={"uuid": uuid, "error": str(e)})
```

**Docstrings required:**
```python
def function_name(param: str) -&gt; dict:
    """
    Brief description of function.

    Longer description with details about the function's purpose,
    behavior, and any important notes.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ValueError: When validation fails
        IOError: When file operation fails

    Examples:
        &gt;&gt;&gt; function_name("test")
        {'result': 'value'}
    """
    pass
```

### JavaScript/Svelte Code

**Clear component structure:**
```svelte
&lt;script&gt;
  // Props
  export let prop1

  // State
  let localState = {}

  // Functions
  function handleAction() {
    // implementation
  }
&lt;/script&gt;

&lt;div&gt;
  &lt;!-- Template --&gt;
&lt;/div&gt;

&lt;style&gt;
  /* Styles */
&lt;/style&gt;
```

**Error handling:**
```javascript
try {
  await apiCall()
} catch (error) {
  console.error('API call failed:', error)
  // Handle error appropriately
}
```

### Database Code

**Use parameterized queries:**
```python
# GOOD
cursor.execute("SELECT * FROM locations WHERE uuid = ?", (uuid,))

# BAD - SQL injection risk
cursor.execute(f"SELECT * FROM locations WHERE uuid = '{uuid}'")
```

**Handle transactions:**
```python
conn = get_db_connection()
try:
    conn.execute("BEGIN")
    # operations
    conn.commit()
except Exception as e:
    conn.rollback()
    raise
finally:
    conn.close()
```

---

## FILE ORGANIZATION

### Python Modules

```
scripts/
├── __init__.py
├── api_routes_v012.py          # Main API endpoints
├── adapters/                    # External service integrations
│   ├── __init__.py
│   ├── immich_adapter.py
│   └── archivebox_adapter.py
├── migrations/                  # Database migrations
│   ├── __init__.py
│   └── add_*.py
└── utils/                       # Utility functions
    ├── __init__.py
    ├── logging_utils.py
    └── validation_utils.py
```

### Documentation

```
docs/
├── v0.1.2/                     # Versioned documentation
│   ├── 01_OVERVIEW.md
│   ├── 02_ARCHITECTURE.md
│   └── ...
├── FIRST_RUN_SETUP_WIZARD.md
└── ...

Root level:
├── README.md                    # Main documentation
├── claude.md                    # This file
├── techguide.md                 # Technical reference
├── lilbits.md                   # Script documentation
└── todo.md                      # Current tasks
```

---

## COMMON PATTERNS

### API Endpoint Pattern

```python
@app.route('/api/resource', methods=['GET'])
def get_resource():
    """
    Get resource with validation and error handling.

    Returns:
        JSON response with data or error
    """
    try:
        # Validate input
        validate_request()

        # Get data
        data = fetch_data()

        # Transform
        result = transform_data(data)

        # Return
        return jsonify({'status': 'success', 'data': result}), 200

    except ValidationError as e:
        logger.warning(f"Validation failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

    except Exception as e:
        logger.exception("Unexpected error")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
```

### Database Operation Pattern

```python
def db_operation(param: str) -&gt; Optional[dict]:
    """
    Database operation with connection management.

    Args:
        param: Operation parameter

    Returns:
        Result dict or None if not found
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM table WHERE field = ?",
            (param,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()
```

### File Operation Pattern

```python
def file_operation(path: str) -&gt; str:
    """
    File operation with validation and error handling.

    Args:
        path: File path

    Returns:
        File contents

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
    """
    # Validate
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    if not os.access(path, os.R_OK):
        raise PermissionError(f"Cannot read file: {path}")

    # Read
    try:
        with open(path, 'r') as f:
            return f.read()
    except IOError as e:
        logger.error(f"Failed to read {path}: {e}")
        raise
```

---

## TESTING REQUIREMENTS

### Test Coverage

Minimum 70% code coverage enforced by pytest.ini

### Test Structure

```python
import pytest
from scripts.module import function

class TestFunction:
    """Test suite for function."""

    def test_happy_path(self):
        """Test normal operation."""
        result = function("valid_input")
        assert result == expected_value

    def test_edge_case(self):
        """Test edge case."""
        result = function("")
        assert result is None

    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            function("invalid_input")

    def test_integration(self, mock_db):
        """Test with dependencies."""
        # Setup
        mock_db.return_value = test_data

        # Execute
        result = function("input")

        # Verify
        assert result == expected
        mock_db.assert_called_once()
```

### Test Organization

```
tests/
├── unit/                        # Unit tests (isolated)
│   ├── test_module.py
│   └── ...
├── integration/                 # Integration tests (with dependencies)
│   ├── test_api_integration.py
│   └── ...
├── e2e/                        # End-to-end tests
│   ├── test_workflow.py
│   └── ...
└── conftest.py                 # Shared fixtures
```

---

## SECURITY GUIDELINES

### Input Validation

Always validate and sanitize user input:
- Use parameterized queries
- Validate file paths
- Check file extensions
- Limit file sizes
- Sanitize HTML output
- Validate UUIDs
- Check permissions

### Secret Management

Never commit secrets:
- Use environment variables
- Use .env files (in .gitignore)
- Use secret management systems
- Rotate keys regularly
- Document secret requirements

### API Security

Protect API endpoints:
- Validate inputs
- Use rate limiting
- Implement authentication (when needed)
- Use HTTPS in production
- Set CORS policies
- Log security events

---

## PERFORMANCE GUIDELINES

### Database

- Use indexes for frequently queried fields
- Use LIMIT for large result sets
- Use transactions for bulk operations
- Use connection pooling
- Monitor query performance
- Plan for pagination

### File Operations

- Stream large files
- Use async for I/O operations
- Cache frequently accessed data
- Clean up temporary files
- Monitor disk usage

### API

- Implement caching
- Use pagination
- Optimize JSON serialization
- Monitor response times
- Set timeouts
- Handle rate limiting

---

## DOCUMENTATION STANDARDS

### Code Comments

Comment why, not what:
```python
# GOOD: Explains reasoning
# Use SHA256 because MD5 has collision vulnerabilities
hash_value = hashlib.sha256(data).hexdigest()

# BAD: Restates code
# Calculate SHA256 hash
hash_value = hashlib.sha256(data).hexdigest()
```

### Commit Messages

Format:
```
type: Brief description (50 chars max)

Detailed explanation of what changed and why.
Include context, trade-offs, and considerations.

References: #issue-number
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

### Documentation Files

Use markdown with clear structure:
- Title and version at top
- Table of contents for long docs
- Code examples with syntax highlighting
- Clear section headers
- Links to related docs

---

## DEPLOYMENT GUIDELINES

### Pre-deployment Checklist

- All tests pass
- Code reviewed
- Documentation updated
- Security audit complete
- Performance acceptable
- Rollback plan ready
- Monitoring configured

### Production Configuration

- Debug mode OFF
- Structured logging
- Error tracking enabled
- Performance monitoring
- Backup strategy in place
- Health checks configured
- Graceful shutdown handling

---

## MAINTENANCE GUIDELINES

### Regular Tasks

Weekly:
- Review logs for errors
- Check disk usage
- Verify backups
- Review security alerts

Monthly:
- Update dependencies
- Review performance metrics
- Audit database indexes
- Review documentation accuracy

Quarterly:
- Security audit
- Performance optimization
- Dependency cleanup
- Documentation overhaul

---

## CONTACT AND SUPPORT

### When Stuck

1. Check this file (claude.md)
2. Check techguide.md for architecture
3. Check lilbits.md for existing scripts
4. Search codebase for similar patterns
5. Check official documentation
6. Ask user for clarification

### Before Asking User

Attempt to:
- Research the problem
- Check existing code
- Review documentation
- Form specific questions
- Propose solutions

Ask specific questions, not vague ones:
- GOOD: "Should we use approach A (faster but more memory) or approach B (slower but less memory)?"
- BAD: "What should I do here?"

---

## VERSION HISTORY

- 1.0.0 (2025-11-18): Initial version with core rules and process

---

## SUMMARY

**Remember the rules:**
- KISS: Keep it simple
- FAANG PE: Production quality
- BPL: Built to last 10+ years
- BPA: Always check latest docs
- NME: No emojis
- WWYDD: Suggest improvements
- DRETW: Don't reinvent
- LILBITS: Small, focused scripts

**Follow the 10-step process for every task.**

**Write code that you'd want to maintain in 5 years.**

**When in doubt, ask questions and suggest alternatives.**
