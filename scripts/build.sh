#!/bin/bash
# build.sh - compile the eBPF program, generate the skeleton, build the loader
set -e
cd "$(dirname "$0")/.."
mkdir -p build

clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I bpf \
  -c bpf/ringbuf.bpf.c -o build/ringbuf.bpf.o

bpftool gen skeleton build/ringbuf.bpf.o > build/ringbuf.skel.h

gcc -g -O2 -Wall -I bpf -I build src/loader.c -o build/loader -lbpf -lelf -lz
echo "build OK -> build/loader"
