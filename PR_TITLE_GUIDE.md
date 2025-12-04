# Pull Request Title Guide

## Overview

This guide explains the proper format for pull request titles in the Polars repository.

## Format Requirements

Pull request titles must follow the [Conventional Commits](https://www.conventionalcommits.org/) format using the [Angular convention](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#type).

### Pattern

```
<type>(<scope>): <Description>
```

### Components

#### Type (required)
One of the following:
- `build` - Changes to build system or dependencies
- `chore` - Maintenance tasks
- `ci` - CI/CD changes
- `depr` - Deprecations
- `docs` - Documentation changes
- `feat` - New features
- `fix` - Bug fixes
- `perf` - Performance improvements
- `refactor` - Code refactoring
- `release` - Release-related changes
- `test` - Test additions or modifications

#### Scope (optional)
Indicates which part of the codebase is affected:
- `(python)` - Python-specific changes
- `(rust)` - Rust-specific changes
- `(python,rust)` - Changes affecting both
- Omit scope if change affects both languages equally

#### Breaking Changes (optional)
Add `!` after the scope or type to indicate breaking changes:
- `feat!: Description` or `feat(python)!: Description`

#### Description (required)
- Must start with an **uppercase letter**
- Use **active voice** (e.g., "Add feature" not "Added feature")
- Use single backticks for code references: `` `DataFrame.top_k` ``
- Must **NOT** end with punctuation (`.`, `!`, `?`, `,`)
- Must **NOT** end with a space
- Must **NOT** include PR number references like `(#12345)`

## Examples

### Good PR Titles ✓

```
fix(python): Fix `DataFrame.top_k` not handling nulls correctly
feat(rust): Add parquet file write pipeline for new IO sinks
refactor: Simplify expression evaluation logic
docs: Update installation guide for Windows users
perf(python)!: Optimize groupby operations with breaking API changes
```

### Bad PR Titles ✗

```
fix(python): Fix DataFrame.top_k not handling nulls correctly.     ❌ Ends with period
feat(rust): Add parquet file write pipeline for new IO sinks (#25618) ❌ Includes PR number
refactor: simplify expression evaluation logic  ❌ Description doesn't start with uppercase
docs: updated installation guide  ❌ Uses past tense
Fix bug  ❌ Missing scope and proper description
```

## Validation

PR titles are automatically validated using the configuration in `.github/pr-title-checker-config.json`.

The validation regex is:
```
^(build|chore|ci|depr|docs|feat|fix|perf|refactor|release|test)(\\((python|rust)\\!?(,(python|rust)\\!?)?\\))?\\!?\\: [A-Z].*[^\\.\\!\\?,… ]$
```

## References

- [Contributing Guide](docs/source/development/contributing/index.md)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Angular Commit Convention](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#type)
