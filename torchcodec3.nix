{ lib
, buildPythonPackage
, fetchFromGitHub
, cmake
, torch
, python
, stdenv
, writeText
, substituteAll
, ffmpeg-full
, pkg-config
, autoPatchelfHook
, makeWrapper
}:

buildPythonPackage rec {
  pname = "torchcodec";
  version = "0.2.1"; # 적절한 버전으로 변경하세요
  format = "setuptools";

  src = fetchFromGitHub {
    owner = "pytorch"; # 실제 소유자로 변경하세요
    repo = "torchcodec"; # 실제 레포지토리 이름으로 변경하세요
    rev = "v${version}"; # 또는 적절한 커밋 해시
    sha256 = "sha256-LeaeVWJ0N8QWuzjANgRwhH0yr/oMqk7PBneBkyqgYNg=";
  };

  nativeBuildInputs = [
    cmake
    pkg-config
    autoPatchelfHook
    makeWrapper
  ];

  buildInputs = [
    ffmpeg-full
  ];

  propagatedBuildInputs = [
    torch
  ];

  # CMake 빌드를 위한 환경 변수 설정
  CMAKE_BUILD_TYPE = "Release";
  ENABLE_CUDA = if stdenv.isx86_64 && stdenv.isLinux then "ON" else "OFF";

  # version.txt 파일 생성
  prePatch = ''
    echo "${version}" > version.txt
  '';

  # CMake 빌드 설정
  dontUseCmakeConfigure = true;
  
  buildPhase = ''
    runHook preBuild
    
    # version.py 파일 생성
    mkdir -p src/torchcodec
    cat > src/torchcodec/version.py << EOF
# Note that this file is generated during install.
__version__ = '${version}'
EOF
    
    # CMAKE 빌드 디렉토리 생성
    mkdir -p build
    cd build
    
    # CMake 설정
    cmake .. \
      -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE} \
      -DCMAKE_INSTALL_PREFIX=$out \
      -DTorch_DIR=${torch}/lib/python*/site-packages/torch/share/cmake/Torch \
      -DPYTHON_VERSION=${python.pythonVersion} \
      -DENABLE_CUDA=${ENABLE_CUDA} \
      -DCMAKE_VERBOSE_MAKEFILE=ON \
      -DFFMPEG_ROOT=${ffmpeg-full} \
      -DPkgConfig_EXECUTABLE=${pkg-config}/bin/pkg-config \
      -DCMAKE_PREFIX_PATH="${ffmpeg-full}"
    
    # 빌드 실행
    cmake --build .
    
    cd ..
    
    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall
    
    # CMake install 실행
    cd build
    cmake --install .
    cd ..
    
    # Python 패키지 설치
    ${python.interpreter} setup.py install --prefix=$out
    
    # FFmpeg 라이브러리 경로를 런타임에 사용할 수 있도록 설정
    if [ -d "$out/lib/python${python.pythonVersion}/site-packages/torchcodec" ]; then
      for so_file in $out/lib/python${python.pythonVersion}/site-packages/torchcodec/*.so; do
        if [ -f "$so_file" ]; then
          wrapProgram $so_file \
            --prefix LD_LIBRARY_PATH : ${lib.makeLibraryPath [ ffmpeg-full ]}
        fi
      done
    fi
    
    runHook postInstall
  '';

  # 런타임 라이브러리 경로 설정
  postFixup = ''
    # Python 바이너리들에 대해 FFmpeg 라이브러리 경로 설정
    for file in $out/bin/* $out/lib/python*/site-packages/torchcodec/*.so; do
      if [ -f "$file" ]; then
        echo "Patching $file"
        patchelf --set-rpath "${lib.makeLibraryPath [ ffmpeg-full ]}:$(patchelf --print-rpath $file 2>/dev/null || echo "")" "$file" 2>/dev/null || true
      fi
    done
  '';

  # 테스트 비활성화 (필요에 따라 활성화)
  doCheck = false;

  # 라이센스 관련 환경 변수 설정
  BUILD_AGAINST_ALL_FFMPEG_FROM_S3 = "1";

  # 런타임에 FFmpeg을 찾을 수 있도록 환경 변수 설정
  setupHook = writeText "torchcodec-setup-hook" ''
    export LD_LIBRARY_PATH="${lib.makeLibraryPath [ ffmpeg-full ]}''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    export PKG_CONFIG_PATH="${ffmpeg-full}/lib/pkgconfig''${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
  '';

  meta = with lib; {
    description = "A library for video and audio processing with PyTorch";
    homepage = "https://github.com/pytorch/torchcodec"; # 실제 홈페이지로 변경하세요
    license = licenses.bsd3; # 실제 라이센스로 변경하세요
    maintainers = with maintainers; [ ]; # 메인테이너 추가
    platforms = platforms.linux ++ platforms.darwin;
    # CUDA는 Linux x86_64에서만 지원
    broken = stdenv.isDarwin && (ENABLE_CUDA == "ON");
  };
}
