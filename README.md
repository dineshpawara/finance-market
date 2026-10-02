# Finance Market

Indian Stock Market Finance Platform with FastAPI, React (TypeScript + Vite), PostgreSQL/TimescaleDB, and Redis.

## Monorepo Layout

```text
finance-market/
├── .github/
│   ├── workflows/
│   │   ├── ci-backend.yml     # Backend CI (Ruff, pytest, compileall, alembic)
│   │   ├── ci-frontend.yml    # Frontend CI (ESLint, build, tests)
│   │   └── cd-main.yml        # CD deployment skeleton for main releases
│   └── dependabot.yml         # Automated dependency updates
├── backend/                   # FastAPI backend managed with uv
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Backend pytest test suite
│   ├── pyproject.toml         # Dependencies and tool configs (ruff, pytest)
│   └── uv.lock
├── frontend/                  # React + TypeScript + Vite UI
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── config/                    # Configuration templates
├── docker-compose.yml         # Local & production stack orchestration
├── .env.example
└── README.md
```

---

## Contributing & Git Workflow

### 1. Branching Strategy (GitFlow-style)
- **`develop`**: Primary integration branch (default branch). All feature, fix, and chore branches branch from `develop`.
- **`main`**: Production-ready branch. Only updated via release PRs from `develop` or critical `hotfix/*` branches.

### 2. Branch Naming Conventions
- `feature/<name>`: New features or enhancements.
- `fix/<name>`: Bug fixes targeting `develop`.
- `chore/<name>`: Build, CI/CD, dependency, or repository restructuring.
- `hotfix/<name>`: Critical production bug fixes targeting `main`.

### 3. Pull Request & Merge Rules
- **Merging into `develop`**:
  - Always use **Squash and merge**.
  - All feature/fix commits are squashed into a single clean commit on `develop`.
- **Merging `develop` into `main` (Releases)**:
  - Always use **Merge commit** (`git merge --no-ff`).
  - Never squash `develop` into `main`, which causes commit histories to diverge.
- **Hotfix Workflow**:
  1. Branch off `main`: `git checkout -b hotfix/critical-fix main`.
  2. Open PR into `main` and merge via **Merge commit**.
  3. **Crucial**: Immediately back-merge `main` into `develop` (`git checkout develop && git merge main && git push origin develop`), ensuring the fix is never lost in development.

### 4. Releases & Versioning
- After merging a release PR into `main`, create a semantic version tag:
  ```bash
  git checkout main
  git pull origin main
  git tag -a v0.1.0 -m "Release v0.1.0"
  git push origin v0.1.0
  ```
- Formal `release/*` branches can be introduced when multiple release trains occur as the team expands.
