# Contributing to Snort3-AI-Ops

Thank you for your interest in contributing to Snort3-AI-Ops! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Harassment, insults, or derogatory comments
- Trolling or inflammatory comments
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Snort3 3.1.0 or higher
- Git
- Docker (optional, for containerized development)
- C++ compiler (for plugin development)

### Areas to Contribute

- **Core Features**: Enhance the AI-Ops engine
- **Agents**: Develop new specialized agents
- **Integrations**: Add support for new security tools
- **Documentation**: Improve guides and examples
- **Testing**: Increase test coverage
- **Bug Fixes**: Fix reported issues
- **Performance**: Optimize processing and analysis

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/snort3-ai-ops.git
cd snort3-ai-ops

# Add upstream remote
git remote add upstream https://github.com/original/snort3-ai-ops.git
```

### 2. Create Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Build Snort3 Plugin

```bash
cd snort3-plugins/event_exporter
mkdir build && cd build
cmake ..
make
```

### 4. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=agents --cov=core --cov=connectors tests/

# Run specific test file
pytest tests/agents/test_threat_intel_agent.py -v
```

## How to Contribute

### Reporting Bugs

Before submitting a bug report:
1. Check existing issues to avoid duplicates
2. Use the latest version
3. Collect relevant information

**Bug Report Should Include:**
- Clear, descriptive title
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, Python version, Snort3 version)
- Logs and error messages
- Screenshots if applicable

**Template:**

```markdown
**Bug Description**
A clear description of what the bug is.

**To Reproduce**
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.10.5]
- Snort3: [e.g., 3.1.45.0]
- Version: [e.g., 1.0.0]

**Logs**
```
Paste relevant logs here
```

**Additional Context**
Any other context about the problem.
```

### Suggesting Enhancements

**Enhancement Proposal Should Include:**
- Clear title and description
- Use case and motivation
- Proposed solution
- Alternative solutions considered
- Implementation complexity estimate

### Contributing Code

1. **Find or Create an Issue**
   - For bugs: Find existing issue or create new one
   - For features: Discuss in an issue first

2. **Create a Branch**
   ```bash
   git checkout -b feature/amazing-feature
   # or
   git checkout -b fix/bug-description
   ```

3. **Make Changes**
   - Write clean, documented code
   - Follow coding standards
   - Add/update tests
   - Update documentation

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```
   
   **Commit Message Format:**
   ```
   <type>: <description>
   
   [optional body]
   
   [optional footer]
   ```
   
   **Types:**
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation only
   - `style`: Code style (formatting, etc.)
   - `refactor`: Code refactoring
   - `test`: Adding tests
   - `chore`: Maintenance

5. **Push and Create PR**
   ```bash
   git push origin feature/amazing-feature
   ```
   Then create a Pull Request on GitHub.

## Coding Standards

### Python Code Style

We follow PEP 8 with some modifications:

```python
# Maximum line length: 100 characters
# Use type hints
def process_event(event: Dict[str, Any]) -> EventResult:
    """
    Process a security event.
    
    Args:
        event: Event data dictionary
        
    Returns:
        EventResult object with analysis
        
    Raises:
        ValueError: If event format is invalid
    """
    pass

# Use descriptive variable names
threat_score = calculate_threat_score(indicators)

# Use list comprehensions for simple iterations
malicious_ips = [ip for ip in ip_list if is_malicious(ip)]

# Document complex algorithms
# This uses the Isolation Forest algorithm to detect anomalies
# based on the assumption that anomalies are easier to isolate
model = IsolationForest(contamination=0.1)
```

### C++ Code Style

For Snort3 plugins:

```cpp
// Use camelCase for variables
int eventCount = 0;

// Use PascalCase for classes
class AIEventExporter : public Inspector
{
public:
    // Clear function names
    void exportAlert(Packet* p);
    void serializeEvent(const Event& event);
    
private:
    // Private members with prefix
    std::string m_endpoint;
    size_t m_bufferSize;
};

// Comment complex logic
// Calculate threat score using weighted average
// of multiple indicators
double threatScore = (ipReputation * 0.4) + 
                     (behavioralScore * 0.3) +
                     (ruleScore * 0.3);
```

### Code Organization

```
agents/
├── __init__.py
├── base_agent.py              # Base class for all agents
├── threat_intelligence_agent.py
└── behavioral_analysis_agent.py

tests/
├── agents/
│   ├── test_threat_intel_agent.py
│   └── test_behavioral_agent.py
└── integration/
    └── test_end_to_end.py
```

## Testing Guidelines

### Test Coverage Requirements

- Minimum 80% code coverage
- 100% coverage for critical paths
- All new features must include tests
- Bug fixes must include regression tests

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch

class TestThreatIntelAgent:
    """Test suite for Threat Intelligence Agent."""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        config = ThreatIntelConfig(enabled=True)
        return ThreatIntelligenceAgent(config)
    
    @pytest.mark.asyncio
    async def test_enrich_event(self, agent):
        """Test event enrichment functionality."""
        # Arrange
        event = {'type': 'alert', 'src_ip': '1.2.3.4'}
        
        # Act
        result = await agent.enrich_event(event)
        
        # Assert
        assert 'threat_intel' in result
        assert result['threat_intel']['checked']
    
    def test_edge_case_empty_event(self, agent):
        """Test handling of empty event."""
        with pytest.raises(ValueError):
            agent.validate_event({})
```

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/agents/

# With coverage
pytest --cov=agents --cov-report=html

# Parallel execution
pytest -n auto

# Verbose output
pytest -v -s
```

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] All tests passing
```

### Review Process

1. Automated checks run (tests, linting)
2. At least one maintainer review required
3. Address feedback and update PR
4. Once approved, maintainer will merge

### After Merge

- Delete your branch
- Update your fork:
  ```bash
  git checkout main
  git pull upstream main
  git push origin main
  ```

## Community

### Getting Help

- **Discord**: Join our Discord server
- **GitHub Discussions**: For questions and ideas
- **GitHub Issues**: For bugs and feature requests
- **Email**: community@snort3-ai-ops.io

### Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Invited to contributor meetings

## License

By contributing, you agree that your contributions will be licensed under the GNU General Public License v2.0.

---

**Thank you for contributing to Snort3-AI-Ops!** 🎉
