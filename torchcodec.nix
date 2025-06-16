{ lib
, buildPythonPackage
, fetchFromGitHub
, cmake
, pytorch
, numpy
, pytest
, pillow
, cudaPackages
, cudatoolkit
, ninja
, pkg-config
, ffmpeg
}:

buildPythonPackage rec {
  stdenv = cudaPackages.backendStdenv;

  pname = "torchcodec";
  version = "0.4.0";
  format = "pyproject";

  src = fetchFromGitHub {
    owner = "pytorch";
    repo = "torchcodec";
    rev = "v${version}";  # Adjust to actual tag or commit hash
    sha256 = "sha256-3v4UpE8jw7av6qLI5/bpHwinvAlSTeJJIRnvduGa+Ig=";
  };

  nativeBuildInputs = [
    ninja
    cmake
    pkg-config
    cudatoolkit
  ];

  buildInputs = [
    ffmpeg
  ] ++ (with cudaPackages; [
    cuda_cudart # cuda_runtime.h
    cuda_cccl # <thrust/*>
    libcublas # cublas_v2.h
    libcusolver # cusolverDn.h
    libcusparse # cusparse.h
  ]);

  propagatedBuildInputs = [
    pytorch
  ];

  # Optional dependencies
  checkInputs = [
    numpy
    pytest
    pillow
  ];

  # Disable build isolation as specified in the original setup.py comments
  dontUsePipInstallCheck = true;
  pipInstallFlags = [ "--no-build-isolation" ];

  # Set environment variables needed for the build
  preBuild = ''
    export CMAKE_PREFIX_PATH=${pytorch}/share/cmake:$CMAKE_PREFIX_PATH
    # Create version.txt file if it doesn't exist
    if [ ! -f version.txt ]; then
      echo "${version}" > version.txt
    fi
    # Create the version.py file
    mkdir -p src/torchcodec
    echo "# Note that this file is generated during install." > src/torchcodec/version.py
    echo "__version__ = '${version}'" >> src/torchcodec/version.py
  '';

  # We're only enabling standard build - set ENABLE_CUDA explicitly if needed
  cmakeBuildType = "Release";
  
  # Add any needed environment variables from the original setup
  # Uncomment and set appropriate value if CUDA build is needed
  # ENABLE_CUDA = "ON";
  
  # Force confirmation for license compliance (as required in setup.py)
  I_CONFIRM_THIS_IS_NOT_A_LICENSE_VIOLATION = "1";

  # Python imports to check after installation
  pythonImportsCheck = [ "torchcodec" ];

  # Since the build process is complex, we might want to disable tests initially
  doCheck = false;

  meta = with lib; {
    description = "A video decoder for PyTorch";
    homepage = "https://github.com/pytorch/torchcodec";
    license = licenses.bsd3;  # Based on the license file mention in the pyproject.toml
    maintainers = with maintainers; [ ];  # Add yourself if appropriate
    platforms = platforms.unix;
  };
}
