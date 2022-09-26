#! /bin/bash
docker-compose -f ./validator-3/docker-compose.yaml down
docker-compose -f ./validator-2/docker-compose.yaml down
docker-compose -f ./validator-1/docker-compose.yaml down
docker-compose -f ./validator-0/docker-compose.yaml down
