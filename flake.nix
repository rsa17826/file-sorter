{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in
    {
      # ── nix run / nix build ──────────────────────────────────────────────
      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python3.withPackages (ps: [ ps.commentjson ]);
        in
        {
          default = pkgs.writeShellApplication {
            name = "browser-selector";
            runtimeInputs = [ python ];
            text = ''
              exec python3 "${./sorter.py}" "$@"
            '';
          };
        }
      );

      # ── nix develop / direnv ─────────────────────────────────────────────
      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              xdg-utils
              basedpyright
              (python3.withPackages (ps: with ps; [ commentjson ]))
            ];
          };
        }
      );
    };
}
