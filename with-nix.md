# Use disputable monitor via NIX-SHELL

##### Install Nix
- Linux:
```sh
sh <(curl -L https://nixos.org/nix/install) --daemon
````
<!-- - MacOS: sh <(curl -L https://nixos.org/nix/install) -->

##### Then:
```sh
nix-shell
```

```sh
uv sync
```

(uv always creates `.venv/` in the project directory)

```sh
mv vars.example.sh vars.sh
```

fill in variables with appropriate values see [README](./README.md)

```sh
source vars.sh
```

```sh
uv run telliot config init
```

Add project id to ~/telliot/endpoints.yaml

```sh
uv run cli
```
