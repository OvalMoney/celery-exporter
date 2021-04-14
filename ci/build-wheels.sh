#!/bin/bash
set -ex

curl -o rustup-init https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init
chmod +x rustup-init
./rustup-init -y --no-modify-path --default-toolchain stable
export PATH="$HOME/.cargo/bin:$PATH"

cd /io

for PYBIN in /opt/python/{cp35-cp35m,cp36-cp36m,cp37-cp37m,cp38-cp38}/bin; do
    export PYTHON_SYS_EXECUTABLE="$PYBIN/python"

    "${PYBIN}/pip" install -U maturin
    "${PYBIN}/maturin" build --release -i "${PYBIN}/python" -o dist/
done

PYBIN=/opt/python/cp37-cp37m/bin
"${PYBIN}/pip" install auditwheel
for whl in dist/*.whl; do
    "${PYBIN}/auditwheel" repair "$whl" -w dist/
done
