# GitHub Strategy - Tick-Tock Widget v0.1.0 Alpha

## Overview

This document outlines the GitHub workflow and branching strategy for the Tick-Tock Widget project during the initial v0.1.0 alpha development phase.

**Current Version:** 0.1.0 (Alpha)  
**Development Phase:** Solo development, rapid iteration  
**Repository:** Will-cz/tick-tock

## Branch Structure

### Active Branches

- **`main`** - Stable milestones and releases only
- **`dev`** - Active development branch (primary working branch)

### Workflow

1. **Primary Development**: All active development happens on `dev` branch
2. **Feature Development**: Continue working directly on `dev` for alpha features
3. **Milestone Merges**: Merge `dev` → `main` only at stable milestones

## Commit Message Convention

Use clear, descriptive commit messages with conventional prefixes:

```
feat: add project management functionality
fix: resolve widget minimization issue
docs: update README with installation steps
test: add unit tests for time tracking
refactor: cleanup project data handling
build: update PyInstaller configuration
style: improve code formatting
```

## Development Workflow

### Daily Development
1. Work on `dev` branch
2. Commit frequently with descriptive messages
3. Push to `origin/dev` regularly for backup

### Milestone Releases
1. Ensure all tests pass
2. Update version in `pyproject.toml` if needed
3. Merge `dev` → `main`
4. Create version tag
5. Push changes and tags

## Version Tagging

Tag stable alpha milestones:

```bash
git tag -a v0.1.0-alpha.1 -m "Alpha release 1 - core functionality"
git push origin v0.1.0-alpha.1
```

## When to Merge to Main

Merge `dev` → `main` when you have:

- ✅ Working, testable version
- ✅ Major milestone completion  
- ✅ All critical bugs resolved
- ✅ Documentation updated
- ✅ Ready for potential distribution

## Branch Protection

Currently **no branch protection** is configured, suitable for solo development.

Consider enabling branch protection later when:
- Adding collaborators
- Moving to beta/stable versions
- Requiring code reviews

## Project Status

**Current Focus:** Core functionality development  
**Next Milestone:** Feature-complete alpha release  
**Target:** Stable v0.1.0 alpha with all planned features

---

*Last Updated: August 10, 2025*  
*Document Version: 1.0*
