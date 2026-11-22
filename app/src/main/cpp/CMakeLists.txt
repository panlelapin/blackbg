cmake_minimum_required(VERSION 3.22.1)
project(blackbg LANGUAGES C)
add_library(blackbg_arm64 SHARED abi.c)
target_compile_options(blackbg_arm64 PRIVATE -fvisibility=hidden)
