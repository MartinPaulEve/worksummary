{
  description = "Log daily work items and produce a Teams-ready summary.";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs =
    { self, nixpkgs }:
    let
      # The systems we build for. Inlined instead of pulling in flake-utils —
      # this is all that `eachDefaultSystem` did for a single-package flake.
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          # Single source of truth for name/version/description — read straight
          # from pyproject.toml so the package never drifts from the project
          # metadata (the repo's __version__.py has lagged behind before).
          pyproject = (pkgs.lib.importTOML ./pyproject.toml).project;
        in
        {
          default = pkgs.python3Packages.buildPythonApplication {
            pname = pyproject.name;
            version = pyproject.version;
            src = self;
            pyproject = true;

            build-system = with pkgs.python3Packages; [ hatchling ];
            dependencies = with pkgs.python3Packages; [ click ];
            nativeCheckInputs = with pkgs.python3Packages; [ pytestCheckHook ];

            # Ship the hand-maintained fish completion with the package so it
            # travels wherever worksummary is installed. fish auto-loads files
            # in share/fish/vendor_completions.d from packages on XDG_DATA_DIRS.
            postInstall = ''
              install -Dm644 completions/worksummary.fish \
                "$out/share/fish/vendor_completions.d/worksummary.fish"
            '';

            meta = {
              inherit (pyproject) description;
              homepage = pyproject.urls.Homepage;
              # pyproject [project.license] is an SPDX string ("MIT"); map it to
              # the matching nixpkgs license attrset.
              license = pkgs.lib.getLicenseFromSpdxId pyproject.license;
              mainProgram = "worksummary";
              # pyproject [project.authors] entries are { name, email } — exactly
              # the shape nixpkgs expects for a maintainer, so reuse them directly.
              maintainers = pyproject.authors;
            };
          };
        }
      );

      # Enables `nix run github:MartinPaulEve/worksummary`. `getExe` resolves the
      # binary via meta.mainProgram above — the one line `mkApp` saved us.
      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = nixpkgs.lib.getExe self.packages.${system}.default;
        };
      });
    };
}
