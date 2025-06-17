{
lib,
python,
fetchFromGitHub,
buildPythonPackage,
cmake,
pkg-config,
cudaPackages,
torch, 
ffmpeg,
numpy,
setuptools,
wheel,
pip,
pytest,
pillow,
...
}:
buildPythonPackage rec {
  pname = "torchcodec";
  version = "0.2.1";
  format = "pyproject";
  
  src = fetchFromGitHub {
    owner = "pytorch";
    repo = "torchcodec";
    rev = "v${version}";
    sha256 = "sha256-LeaeVWJ0N8QWuzjANgRwhH0yr/oMqk7PBneBkyqgYNg=";
  };

  dontUseCmakeConfigure = true;

  env = {
    I_CONFIRM_THIS_IS_NOT_A_LICENSE_VIOLATION=1;
  };
  
  nativeBuildInputs = [
    cmake
    pkg-config
    cudaPackages.cuda_nvcc
  ] ++ [
    setuptools
    wheel
    pip
  ];
  
  buildInputs = [
    torch
    ffmpeg
    cudaPackages.cuda_cudart
    cudaPackages.cuda_nvrtc
    cudaPackages.cuda_nvtx
    cudaPackages.libcublas
    cudaPackages.libcufft
    cudaPackages.libcurand
    cudaPackages.libcusolver
    cudaPackages.libcusparse
  ];
  
  propagatedBuildInputs = [
    numpy
  ];
  
  checkInputs = [
    pytest
    pillow
  ];

  # Skip tests during build as they require test resources
  doCheck = false;
  
  pythonImportsCheck = [ "torchcodec" ];
  
  meta = with lib; {
    description = "A video decoder for PyTorch";
    homepage = "https://github.com/pytorch/torchcodec";
    license = licenses.bsd3;
    platforms = platforms.linux ++ platforms.darwin;
  };
}
