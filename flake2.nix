{
  description = "LeRobot development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python version for LeRobot
        python = pkgs.python311;
        
      in {
        devShells.default = pkgs.mkShell {
          name = "lerobot-dev";
          
          packages = with pkgs; [
            # Python and package managers
            python
            uv
            
            # Development tools
            git
            cmake
            pkg-config
            gcc
            gnumake
            
            # System dependencies for multimedia and robotics
            ffmpeg
            opencv
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
            
          ] ++ lib.optionals pkgs.stdenv.isLinux [
            # Linux kernel headers for evdev
            linuxHeaders
            # Linux-specific packages
            mesa
            libGL
            libGLU
            xorg.libX11
            xorg.libXext
            xorg.libXrender
          ];
          
          shellHook = ''
            echo "🤖 LeRobot development environment"
            echo "Python: ${python}/bin/python --version"
            echo "UV: $(uv --version)"
            echo ""
            
            # Create and activate virtual environment
            if [ ! -d .venv ]; then
              echo "Creating virtual environment..."
              uv venv --python ${python}/bin/python
            fi
            
            echo "Activating virtual environment..."
            source .venv/bin/activate
            
            # Install dependencies
            if [ ! -f .venv/.installed ]; then
              echo "Installing dependencies..."
              uv pip install -e "."
              touch .venv/.installed
            fi
            
            echo ""
            echo "✅ Ready! Virtual environment activated."
            echo "  - Run 'python -c \"import lerobot; print(lerobot.__version__)\"' to test"
            echo "  - Use 'uv pip install <package>' to add new dependencies"
            echo ""
          '';
          
          # Environment variables
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath (with pkgs; [
            pkgs.stdenv.cc.cc.lib
            zlib
            glib
            gtk3
            cairo
            gdk-pixbuf
            atk
            pango
            ffmpeg
            hdf5
            opencv
            librealsense
          ] ++ lib.optionals pkgs.stdenv.isLinux [
            mesa
            libGL
            libGLU
            xorg.libX11
            xorg.libXext
            xorg.libXrender
          ]);
          
          PKG_CONFIG_PATH = pkgs.lib.makeSearchPathOutput "dev" "lib/pkgconfig" (with pkgs; [
            ffmpeg
            opencv
            hdf5
            gtk3
            glib
            librealsense
          ]);
          
          # Include paths for C compilation (needed for evdev)
          C_INCLUDE_PATH = pkgs.lib.makeSearchPathOutput "dev" "include" (with pkgs; [
            linuxHeaders
          ]);
        };
      });
}