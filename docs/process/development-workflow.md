# Development Workflow Guide

## Overview
This document outlines the development workflow, branching strategy, and processes for the tick-tock project to ensure consistent and organized development practices.

## Branch Strategy

### Branch Types

#### Main Branches
- **`main`** - Production-ready releases only
- **`develop`** - Integration branch for features, staging for next release

#### Supporting Branches
- **`feature/*`** - New features and enhancements
- **`bugfix/*`** - Non-critical bug fixes for current release
- **`hotfix/*`** - Critical fixes for production
- **`release/*`** - Preparation for production releases
- **`experiment/*`** - Research & prototypes

### Branch Naming Conventions

#### Feature Branches
```
feature/brief-description
feature/add-timer-functionality
feature/implement-settings-dialog
feature/dark-theme-support
```

#### Bug Fix Branches
```
bugfix/brief-description
bugfix/fix-timer-reset-issue
bugfix/resolve-window-sizing
bugfix/correct-sound-playback
```

#### Hotfix Branches
```
hotfix/brief-description
hotfix/critical-security-patch
hotfix/fix-crash-on-startup
```

#### Release Branches
```
release/version-number
release/v1.0.0
release/v1.2.1
```

#### Documentation Branches
```
docs/brief-description
docs/api-documentation
docs/user-guide-updates
docs/planning-documentation
```

#### Experimental Branches
```
experiment/brief-description
experiment/ui-redesign
experiment/performance-optimization
experiment/new-framework-test
```

## Development Workflow

### 1. Starting New Work

#### For Features
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

#### For Bug Fixes
```bash
git checkout develop
git pull origin develop
git checkout -b bugfix/your-bugfix-name
```

#### For Hotfixes
```bash
git checkout main
git pull origin main
git checkout -b hotfix/your-hotfix-name
```

### 2. Development Process

1. **Make atomic commits** with clear, descriptive messages
2. **Follow commit message conventions** (see below)
3. **Test thoroughly** before pushing
4. **Update documentation** as needed
5. **Keep branches focused** - one feature/fix per branch

### 3. Commit Message Format

Follow **Conventional Commits** specification for automated changelog generation:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Commit Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code change that neither fixes bug nor adds feature
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to build process or auxiliary tools

#### Examples
```
feat(timer): implement system sleep detection

Implement pause and resume buttons for the timer component.
Users can now pause the countdown and resume from where they left off.

- Add pause/resume buttons to UI
- Implement timer state management
- Update timer display logic
- Fixes #15
```

```
fix(data): resolve file corruption on concurrent access

Fix bug where timer window would not resize properly on high-DPI displays.

- Update window scaling calculations
- Add display DPI detection
- Test on various screen resolutions
- Fixes #28
```

## Merge Process

### Pull Request Requirements

#### Before Creating PR
- [ ] Branch is up to date with target branch
- [ ] All tests pass
- [ ] Code follows project style guidelines
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventions

#### PR Template Checklist
- [ ] Clear title and description
- [ ] Reference related issues
- [ ] Screenshots for UI changes
- [ ] Testing instructions provided
- [ ] Breaking changes documented

### Merge Strategy

#### Feature/Bugfix to Develop
- **Squash and merge** for clean history
- Delete feature branch after merge
- Update issue status

#### Develop to Main (Release)
- **Create merge commit** to preserve development history
- Tag with version number following semantic versioning
- Update changelog

#### Hotfix to Main
- **Fast-forward merge** if possible
- Also merge back to develop
- Tag with patch version immediately

### Code Review Process

#### Reviewer Responsibilities
- Check code quality and style
- Verify functionality works as described
- Test edge cases
- Ensure documentation is adequate
- Validate security implications

#### Review Criteria
- **Functionality**: Does it work as intended?
- **Code Quality**: Is it readable and maintainable?
- **Performance**: Any performance implications?
- **Security**: No security vulnerabilities?
- **Testing**: Adequate test coverage?

## Release Process

### Version Numbering
Follow **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in backward-compatible manner  
- **PATCH**: Backward-compatible bug fixes

**Current Project Versioning:**
- **v0.1.0**: Alpha release (Core timer functionality)
- **v0.2.0**: Enhanced project management
- **v0.3.0**: Advanced reporting features
- **v1.0.0**: Production-ready stable release

### Release Steps

1. **Create release branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b release/v1.2.0
   ```

2. **Prepare release**
   - Update version numbers
   - Update changelog
   - Run final tests
   - Update documentation

3. **Merge to main**
   ```bash
   git checkout main
   git merge --no-ff release/v1.2.0
   git tag -a v1.2.0 -m "Release version 1.2.0"
   ```

4. **Merge back to develop**
   ```bash
   git checkout develop
   git merge --no-ff release/v1.2.0
   ```

5. **Clean up**
   ```bash
   git branch -d release/v1.2.0
   git push origin main develop --tags
   ```

## Best Practices

### General Guidelines
- Keep branches small and focused
- Rebase feature branches regularly
- Write descriptive commit messages
- Test before pushing
- Review your own PRs first

### Branch Management
- Delete merged branches promptly
- Keep branch names short but descriptive
- Use consistent naming conventions
- Don't commit directly to main or develop

### Collaboration
- Communicate changes that affect others
- Ask for help when stuck
- Review others' code constructively
- Keep documentation current

## Tools and Integration

### Recommended Tools
- **Git GUI**: GitKraken, SourceTree, or VS Code Git integration
- **VS Code Extensions**: GitLens, GitHub Pull Requests, Python, Pylance, Test Explorer
- **Code Quality**: Pre-commit hooks, Black, Pylint, isort
- **Testing**: pytest with coverage reporting
- **Documentation**: Markdown preview, automated documentation generation

### Automation
- **CI/CD Pipeline**: Automated testing on PR creation
- **Code Quality Checks**: Pre-commit hooks with Black, Pylint, isort
- **Security Scanning**: GitHub Advanced Security integration
- **Documentation Generation**: Automated on releases
- **Release Automation**: GitHub Actions for builds and distribution

## Troubleshooting

### Common Issues

#### Merge Conflicts
```bash
git checkout feature/your-branch
git rebase develop
# Resolve conflicts
git add .
git rebase --continue
```

#### Accidental Commits to Wrong Branch
```bash
git reset --soft HEAD~1
git stash
git checkout correct-branch
git stash pop
git add .
git commit
```

#### Need to Update Feature Branch
```bash
git checkout feature/your-branch
git rebase develop
# or
git merge develop
```

---

*This workflow guide aligns with the project's Git & GitHub Strategy (see `git-github-strategy.md`) and should be reviewed regularly as the project evolves from solo development to small team collaboration.*

## Related Documentation

- **Git & GitHub Strategy**: `docs/process/git-github-strategy.md` - Comprehensive repository and collaboration strategy
- **Technical Architecture**: `docs/technical/technical-architecture.md` - System design and architecture decisions
- **Testing Strategy**: `docs/technical/testing-strategy.md` - Quality assurance and testing approaches
