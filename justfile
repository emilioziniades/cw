data_dir := "~/.local/share/cw"
cache_dir := "~/.cache/cw"

lint:
    ty check
    ruff check

clean:
    rm -rf {{ data_dir }}

clean-cache:
    rm -rf {{ cache_dir }}

db-shell cmd="":
    nix run nixpkgs#sqlite {{ data_dir }}/cw.sqlite "{{ cmd }}"
