#!/bin/sh

CONNECTORS=(
    atp 
    aws 
    azure 
    proofpoint 
    reference_connector
)

for i in "${CONNECTORS[@]}"
do
    echo "------ Testing connectors/$i"
    cd "connectors/$i"
    
    echo "Installing Dependencies..."
    pip install -r requirements.txt
    echo "Running Unit Tests..."
    python -m pytest -s

    echo "End Unit Tests for $i
    
    
    
    "

   cd -
done