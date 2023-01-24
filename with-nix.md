# Use disputable monitor via NIX-SHELL

##### Install Nix
- Ubuntu 22.04: `sh <(curl -L https://nixos.org/nix/install) --daemon`
<!-- - MacOS: sh <(curl -L https://nixos.org/nix/install) -->

##### Then:
`nix-shell`

`poetry config virtualenvs.in-project true` (optional)

`poetry install`

`mv vars.example.sh vars.sh`

fill in variables with appropriate values see [README](./README.md)

`source vars.sh`

Add project id to ~/telliot/endpoints.yaml

