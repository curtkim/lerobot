{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    pyproject-nix = {
      url = "github:nix-community/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:adisbladis/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix_hammer_overrides.url = "github:TyberiusPrime/uv2nix_hammer_overrides";
    uv2nix_hammer_overrides.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, pyproject-nix, uv2nix, pyproject-build-systems, uv2nix_hammer_overrides }:
    let
      inherit (nixpkgs) lib;

      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config = {
          allowUnfree = true;
          cudaSupport = false;
        };
      };

      workspace = uv2nix.lib.workspace.loadWorkspace {
        workspaceRoot = ./.;
      };

      overlay = workspace.mkPyprojectOverlay {
        sourcePreference = "wheel";
      };

      hacks = pkgs.callPackage pyproject-nix.build.hacks {};

      python = pkgs.python311;
      python3Packages = pkgs.python311Packages;

      torchcodec = python3Packages.callPackage ./torchcodec2.nix {};

      pyprojectOverrides = pkgs.lib.composeExtensions (uv2nix_hammer_overrides.overrides pkgs) (
        # use uv2nix_hammer_overrides.overrides_debug
        #   to see which versions were matched to which overrides
        #  use uv2nix_hammer_overrides.overrides_strict / overrides_strict_debug
        #  to use only overrides exactly matching your python package versions

        final: prev: {
          pyrealsense2 = hacks.nixpkgsPrebuilt {
            from = python3Packages.pyrealsense2;
            prev = prev.pyrealsense2;
          };
          torch = hacks.nixpkgsPrebuilt {
            from = python3Packages.torch;
            prev = prev.torch;
          };

          torchvision = hacks.nixpkgsPrebuilt {
            from = python3Packages.torchvision;
            prev = prev.torchvision;
          };

          # torchcodec = hacks.nixpkgsPrebuilt {
          #   from = torchcodec;
          #   prev = prev.torchcodec;
          # };

          opencv-python = hacks.nixpkgsPrebuilt {
            from = python3Packages.opencv-python;
            prev = prev.opencv-python;
          };
          # place additional overlays here.
          #a_pkg = prev.a_pkg.overrideAttrs (old: nativeBuildInputs = old.nativeBuildInputs ++ [pkgs.someBuildTool] ++ (final.resolveBuildSystems { setuptools = [];});

          feetech-servo-sdk = prev.feetech-servo-sdk.overrideAttrs (old: {
            nativeBuildInputs = old.nativeBuildInputs ++ (final.resolveBuildSystem {setuptools = [];});
          });
          gym-dora = prev.gym-dora.overrideAttrs (old: {
            nativeBuildInputs = old.nativeBuildInputs ++ (final.resolveBuildSystem { poetry-core = [];});
          });
          
          # Ignore missing RDMA dependencies for CUDA packages
          nvidia-cufile-cu12 = prev.nvidia-cufile-cu12.overrideAttrs (old: {
            autoPatchelfIgnoreMissingDeps = [ "libmlx5.so.1" "librdmacm.so.1" "libibverbs.so.1" ];
          });
          
          # Skip autopatchelf completely for torchcodec
          torchcodec = prev.torchcodec.overrideAttrs (old: {
            dontAutoPatchelf = true;
          });

        }
      );

      # pyprojectOverrides = final: prev: {
      #   #pyrealsense2 = pkgs.python3Packages.pyrealsense2;
      #   pyrealsense2 = hacks.nixpkgsPrebuilt {
      #     from = pkgs.python311Packages.pyrealsense2;
      #     prev = prev.pyrealsense2;
      #   };
      #
      #   aioserial = prev.aioserial.overrideAttrs (old: {
      #     buildInputs = (old.buildInputs or [ ]) ++ [ pkgs.python311Packages.poetry-core ];
      #   });
      #   antlr4-python3-runtime = prev.antlr4-python3-runtime.overrideAttrs (old: {
      #     buildInputs = (old.buildInputs or [ ]) ++ [ pkgs.python311Packages.setuptools ];
      #   });
      #
      # };


      pythonSet =
        (pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        }).overrideScope
          (
            lib.composeManyExtensions [
              pyproject-build-systems.overlays.default
              overlay
              pyprojectOverrides
            ]
          );
    in {
      #debug-deps = builtins.trace (builtins.attrNames workspace.deps.optionals.lerobot.feetech ) "deps attrs";

      packages.${system} = {
        default = pythonSet.mkVirtualEnv "lerobot-env" workspace.deps.default;
      };

      devShells.x86_64-linux = {
        default = 
          let
            editableOverlay = workspace.mkEditablePyprojectOverlay {
              root = ".";
            };

            editablePythonSet = pythonSet.overrideScope (
              lib.composeManyExtensions [
                editableOverlay
                (final: prev: {
                  lerobot = prev.lerobot.overrideAttrs (old: {
                    src = lib.fileset.toSource {
                      root = ./.;
                      fileset = lib.fileset.unions [
                        ./pyproject.toml
                        ./lerobot
                        ./README.md
                      ];
                    };
                    nativeBuildInputs =
                      old.nativeBuildInputs
                      ++ final.resolveBuildSystem {
                        editables = [ ];
                      };
                  });

                })
              ]
            );

            #virtualenv = editablePythonSet.mkVirtualEnv "lerobot-dev-env" workspace.deps.all;
            virtualenv = editablePythonSet.mkVirtualEnv "lerobot-dev-env" (
              workspace.deps.default 
              // {
                feetech-servo-sdk = [];
                #gym-pusht = [];
                transformers = [];
                num2words = [];
                accelerate = [];
              }
            );
          in
            pkgs.mkShell {
              packages = [
                virtualenv
                pkgs.uv

              ] ++ (with pkgs; [
                git
                cmake
                pkg-config
                gcc
                gnumake
                
                # System dependencies for multimedia and robotics
                ffmpeg
                #opencv
                gtk3
                glib
                gst_all_1.gstreamer
                gst_all_1.gst-plugins-base
                
                # HDF5 for datasets
                hdf5
                
                # Intel RealSense SDK
                librealsense
                
                # Rerun visualization tool
                rerun
                speechd
              ]);

              env = {
                UV_NO_SYNC = "1";
                UV_PYTHON = "${virtualenv}/bin/python";
                UV_PYTHON_DOWNLOADS = "never";
              };

              shellHook = ''
                unset PYTHONPATH
              '';
            };
      };
    };
}
