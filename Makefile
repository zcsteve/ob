build:
	python -m grpc_tools.protoc -Isp_proto/ --python_out=. --pyi_out=. --grpc_python_out=. ./sp_proto/*.proto
