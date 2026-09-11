data_dir := "~/.local/share/cw"
cache_dir := "~/.cache/cw"

all: format lint test

lint:
    ty check
    ruff check

test:
    uv run pytest

format:
    ruff check --select I --fix .
    ruff format .

clean:
    rm -rf {{ data_dir }}

clean-cache:
    rm -rf {{ cache_dir }}

db-shell cmd="":
    sqlite3 {{ data_dir }}/cw.sqlite "{{ cmd }}"

version v:
    test -z "$(git status --porcelain)"
    test "$(git branch --show-current)" = "main"
    uv version "{{ v }}"
    git commit -a -m "release {{ v }}"
    git tag "{{ v }}"
    git push
    git push --tags
