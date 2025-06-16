{
  description = "LeRobot - nix flake environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      #inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, uv2nix, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

        uv2nix-lib = uv2nix.lib.${system};
        # Converts pyproject.toml to a python package environment using uv
        pythonEnv = uv2nix-lib.toPythonPackage {
          pyprojectToml = ./pyproject.toml;
          #poetryLock = ./poetry.lock; # optional if you use poetry.lock
          python = pkgs.python310;
        };

        # extra native dependencies
        nativeDeps = with pkgs; [
          cmake
          pkg-config
          ffmpeg
          libGL
          libGLU
          libGLU.dev
          libGL.dev
          libjpeg
          libv4l
          zlib
          xorg.libX11
          xorg.libXi
          xorg.libXrandr
          xorg.libXxf86vm
          xorg.libXcursor
          xorg.libXinerama
          xorg.libXext
          glew
          glfw
        ];
      in
      {
        devShells.default = pkgs.mkShell {
          name = "lerobot-dev-shell";

          buildInputs = [
            pythonEnv
          ] ++ nativeDeps;

          # Simulate conda activate by setting environment variables (optional)
          shellHook = ''
            echo "🐍 LeRobot dev shell activated (Python 3.10 with Poetry dependencies)"
            export PYTHONPATH=${pythonEnv}/lib/python3.10/site-packages:$PYTHONPATH
          '';
        };
      });
}

