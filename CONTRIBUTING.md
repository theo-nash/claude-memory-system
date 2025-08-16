# Contributing to Claude Subagent Memory System

Thank you for your interest in contributing! This project aims to solve the persistent memory problem for Claude Code subagents.

## How to Contribute

### Reporting Issues
- Check existing issues first
- Provide clear reproduction steps
- Include your Claude Code version
- Describe expected vs actual behavior

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly with Claude Code
5. Commit with clear messages
6. Push to your branch
7. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/claude-memory-system.git
cd claude-memory-system

# Install dependencies
npm install

# Test installation locally
npm run setup
```

### Testing Changes

1. Install locally in a test project:
   ```bash
   node /path/to/your/fork/bin/install.js
   ```

2. Test all slash commands work
3. Verify hooks fire correctly
4. Ensure memory persistence works

### Code Guidelines

- Keep code simple and readable
- Follow existing patterns
- Document new features
- Update README for user-facing changes
- Ensure backwards compatibility

### Areas Needing Help

- **Memory Optimization**: Better token efficiency
- **Search Enhancement**: Semantic search capabilities
- **Hook Improvements**: More robust error handling
- **Documentation**: More examples and use cases
- **Testing**: Automated test suite

## Questions?

Open an issue for discussion or reach out to the maintainers.

Thank you for helping make Claude Code subagents smarter!