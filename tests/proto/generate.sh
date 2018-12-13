#!/bin/sh -e
protoc tests.proto --plugin=protoc-gen-custom=../../uprotobuf_plugin.py --custom_out=../client
protoc tests.proto --plugin=python --python_out=../server
