{
    inputs = {
        nixpkgs.url = "github:nixos/nixpkgs/release-22.05";

        flake-utils.url = "github:numtide/flake-utils";

        flake-compat = {
        url = "github:edolstra/flake-compat";
        flake = false;
        };

        devshell = {
        url = "github:numtide/devshell";
        inputs.nixpkgs.follows = "nixpkgs";
        };

  };

    outputs = {
        self,
        nixpkgs,
        flake-utils,
        devshell,
        ...
    }:
        flake-utils.lib.eachDefaultSystem (system: let
            pkgs = import nixpkgs {
                inherit system;
                overlays = [devshell.overlay];
            };
        in {
            devShell = pkgs.devshell.mkShell {
                imports = [(pkgs.devshell.importTOML ./devshell.toml)];
            };
        });
}