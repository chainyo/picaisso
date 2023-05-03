0. Fork the repository and clone it.

```bash
git clone https://github.com/chainyo/picaisso.git
```

1. Use an environment with Python 3.10 installed. You can use pyenv or any other tool to manage your Python environments.

2. Install pipx.

```bash
python -m pip install --user pipx
python -m pipx ensurepath
```

3. Install poetry.

```bash
pipx install poetry
```

4. Install Nox and inject nox-poetry.

```bash
pipx install nox
pipx inject nox nox-poetry
```

5. Install the pre-commit hooks.

```bash
nox --session=pre-commit -- install
```

6. Install the project dependencies.

```bash
poetry install
```

7. Activate the project virtual environment.

```bash
poetry shell
```

8. Create a new branch and start coding!

```bash
git checkout -b <branch-name>
code .
```
