# Contributing to SQUAD

Thank you for your interest in contributing to SQUAD! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

Please be respectful and inclusive in all interactions. We welcome contributions from everyone.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/SQUAD.git`
3. Create a branch: `git checkout -b feature/your-feature-name`

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd squad_local_refactored
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
npm install
```

## How to Contribute

### Reporting Bugs

- Use GitHub Issues
- Include steps to reproduce
- Add expected vs actual behavior
- Include environment details (OS, Python version, etc.)

### Feature Requests

- Open a GitHub Issue with the "enhancement" label
- Describe the use case
- Explain why this feature would be valuable

### Code Contributions

1. Choose an open issue or create one
2. Comment on the issue to claim it
3. Implement your changes
4. Write/update tests
5. Submit a pull request

## Coding Standards

### Python

- Follow PEP 8 style guide
- Use type hints
- Write docstrings for all public functions/classes
- Maximum line length: 88 characters

### TypeScript/React

- Follow ESLint configuration
- Use TypeScript strict mode
- Write functional components with hooks
- Use meaningful variable/function names

## Testing

### Backend Tests

```bash
pytest tests/
```

### Frontend Tests

```bash
npm test
```

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add your changes to CHANGELOG.md (if applicable)
4. Request review from maintainers
5. Address review feedback
6. Once approved, your PR will be merged

## Questions?

Feel free to open an issue for any questions or concerns.
