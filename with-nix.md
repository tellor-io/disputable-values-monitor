# Use disputable monitor via NIX-SHELL

##### Install Nix
- Ubuntu 22.04: 
```sh 
sh <(curl -L https://nixos.org/nix/install) --daemon 
````
<!-- - MacOS: sh <(curl -L https://nixos.org/nix/install) -->

##### Then:
```sh
nix-shell
```

`poetry config virtualenvs.in-project true` (optional)

```sh
poetry install
```

```sh
mv vars.example.sh vars.sh
```

fill in variables with appropriate values see [README](./README.md)

```sh
source vars.sh
```

```sh
poetry run telliot config init
```

Add project id to ~/telliot/endpoints.yaml

```sh
poetry run cli
```
