# gRPC

## Scripts to convet the proto file into grpc.py file
python -m grpc_tools.protoc --proto_path=.  ./inventory.proto --python_out=. --grpc_python_out=.
