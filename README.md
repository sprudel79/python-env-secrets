# python-env-secrets

Keep sensitive configuration **out of your project directory** during local development.

> Heavily inspired by .NET's `dotnet user-secrets`.

`python-env-secrets` decouples secrets from your source tree by storing them in
a central, user-scoped directory and linking each project via a GUID. Your
`.env` file contains only the reference — never the secrets themselves.

## The problem

Most Python projects store secrets in `.env` files alongside source code.
Even with `.gitignore`, this is fragile: secrets end up in backups, editor
caches, Docker contexts, and — inevitably — in commits.

There is also a growing risk from **AI-powered coding assistants**. Many of those tools integrated in your IDE routinely scan your
entire workspace for context. If your `.env` file sits in the project
directory, your API keys, database credentials, and tokens may be sent to
third-party AI services as part of the context window — especially on free
tiers where your data may be used for model training. Moving secrets outside
the workspace eliminates this exposure entirely.

Cloud-based solutions like HashiCorp Vault, AWS Secrets Manager, or Azure Key
Vault are the right answer for staging and production. But during **local
development**, you need something simpler — a lightweight tool that keeps
secrets out of the project directory without requiring infrastructure.

## How it works

```
Your Project/
├── .env                          # contains only: USER_SECRETS_ID=<guid>
├── ...

~/.python/usersecrets/
└── <guid>/
    └── .secrets                  # actual secrets live here (key=value)
```

1. A `USER_SECRETS_ID` (UUID) is stored in your project's `.env` file
2. The actual secrets live in `~/.python/usersecrets/<guid>/.secrets`
3. On initialisation, secrets are loaded into `os.environ`

The `.secrets` file uses plain-text key=value format — the same syntax as
`.env` — so you can edit it directly with any text editor.

## Features

- **GUID-based project linking** — each project gets an isolated secret namespace
- **Drop-in replacement** — secrets are injected into `os.environ`, works with any framework
- **CLI and Python API** — manage secrets from the terminal or programmatically
- **python-dotenv compatible** — layer secrets on top of your existing `.env` workflow
- **No external services** — pure Python, zero dependencies, runs entirely offline
- **File-level security** — restrictive permissions (`0600`) on Linux and macOS

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/sprudel79/python-env-secrets.git
```

With optional [python-dotenv](https://github.com/theskumar/python-dotenv) integration:

```bash
pip install "python-env-secrets[dotenv] @ git+https://github.com/sprudel79/python-env-secrets.git"
```

Once published to PyPI, it will also be available via:

```bash
pip install python-env-secrets
```

**Requires Python 3.11 or later.**

## Quick start

### In your application

```python
from python_env_secrets import init_user_secrets
import os

# Initialise at startup — creates GUID + directory on first run,
# loads existing secrets on subsequent runs
init_user_secrets()

# Secrets are now in os.environ
database_url = os.environ["DATABASE_URL"]
api_key = os.environ["API_KEY"]
```

### From the command line

```bash
# Initialise for the current project
user-secrets init

# Manage secrets
user-secrets set DATABASE_URL "postgresql://localhost/mydb"
user-secrets set API_KEY "sk-secret-value"
user-secrets get DATABASE_URL
user-secrets list
user-secrets delete API_KEY
user-secrets clear

# Show configuration
user-secrets info
```

## Usage

### Direct manager usage

```python
from python_env_secrets import UserSecretsManager

manager = UserSecretsManager()          # auto-initialises

manager.set("API_KEY", "sk-...")
manager.set("DB_URL", "postgres://...")

print(manager.get("API_KEY"))           # sk-...
print(manager.list())                   # {"API_KEY": "sk-...", "DB_URL": "..."}

manager.delete("API_KEY")
manager.clear()
```

### Convenience functions

```python
from python_env_secrets import init_user_secrets, get_secret, set_secret

init_user_secrets()

set_secret("API_KEY", "sk-...")
print(get_secret("API_KEY"))
```

### With python-dotenv

Load `.env` defaults first, then layer secrets on top — non-sensitive
configuration stays in `.env` (committable), sensitive values override
from user secrets:

```python
from python_env_secrets import integrate_with_dotenv

# Loads .env first, then layers secrets on top
integrate_with_dotenv()
```

### Framework integration

**Django:**

```python
# settings.py
from python_env_secrets import integrate_with_dotenv
import os

integrate_with_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
```

**Flask:**

```python
from flask import Flask
from python_env_secrets import init_user_secrets
import os

init_user_secrets()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
```

**FastAPI with Pydantic Settings:**

```python
from python_env_secrets import init_user_secrets

init_user_secrets()  # call before Settings() is instantiated

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False
```

## Secret storage locations

| OS      | Path                                          |
|---------|-----------------------------------------------|
| Linux   | `~/.python/usersecrets/<guid>/.secrets`       |
| macOS   | `~/.python/usersecrets/<guid>/.secrets`       |
| Windows | `%APPDATA%\Python\UserSecrets\<guid>\.secrets`|

## Security considerations

- Secrets live **outside** your project tree — they won't be caught by `git add .`, copied into Docker build contexts, or included in backups of your source directory
- **AI coding assistants** (Copilot, Cursor, Codeium, etc.) that index your workspace will never see the actual secret values — only the GUID reference in `.env`
- On Linux/macOS the `.secrets` file is created with `0600` permissions (owner read/write only)
- Each project gets its own isolated GUID namespace — secrets don't leak between projects
- The `.env` file in your project contains **only** the GUID reference, not the secrets

### Limitations

- Secrets are stored as **unencrypted plain text** on disk. File permissions limit access, but this is not an encrypted-at-rest solution. For production deployments, use a proper secrets manager (Vault, AWS Secrets Manager, etc.)
- This tool is designed for **local development only**. It does not handle distribution of secrets to remote systems or across teams
- There is no built-in secret rotation or expiry mechanism

> **Tip:** Add `.env` to your `.gitignore`. While the GUID alone doesn't expose secrets, keeping it out of version control is good practice.

## Related projects

The Python ecosystem has several tools for managing secrets, each targeting
different use cases:

| Package | Focus |
|---------|-------|
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Load `.env` files into `os.environ`. The de facto standard, but keeps secrets inside the project directory. `python-env-secrets` complements it by moving the sensitive values elsewhere. |
| [python-secrets](https://pypi.org/project/python-secrets/) (`psec`) | Full-featured CLI for managing typed secrets across multiple environments, with GPG email sharing, Ansible/Terraform integration, and group-based organisation. Designed for sysadmins and DevOps managing complex deployments. |
| [secrets.env](https://pypi.org/project/secrets.env/) | Connects external credential stores (Vault, Keyring, Teleport) to environment variables. Focused on bridging cloud secret managers to local dev. |
| [django-encrypted-secrets](https://pypi.org/project/django-encrypted-secrets/) | Rails-style encrypted credentials for Django. Secrets are encrypted in the repo with a master key. |

`python-env-secrets` sits in a specific niche: it's for developers who want
the simplicity of `.env` files but need the secrets to live **outside** the
project directory — without adding infrastructure, encryption keys, or cloud
service dependencies.

## Development

```bash
git clone https://github.com/sprudel79/python-env-secrets.git
cd python-env-secrets
pip install -e ".[dev]"
pytest
```

## License

MIT
