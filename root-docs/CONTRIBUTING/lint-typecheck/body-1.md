>>>>> lang=en
### Lint + typecheck

```
make lint         # ruff check + ruff format --check
make typecheck    # mypy --strict
make rust-lint    # cargo fmt --check + cargo clippy -D warnings
make all          # lint + typecheck + rust-lint + test
```

CI runs the same commands; run `make all` locally before pushing.

>>>>> lang=ru
### Lint + typecheck

```
make lint         # ruff check + ruff format --check
make typecheck    # mypy --strict
make rust-lint    # cargo fmt --check + cargo clippy -D warnings
make all          # lint + typecheck + rust-lint + test
```

В CI выполняются те же команды; прогоните `make all` локально перед
пушем.

>>>>> lang=zh
### Lint + typecheck

```
make lint         # ruff check + ruff format --check
make typecheck    # mypy --strict
make rust-lint    # cargo fmt --check + cargo clippy -D warnings
make all          # lint + typecheck + rust-lint + test
```

CI 运行相同的命令；推送前请在本地运行 `make all`。

