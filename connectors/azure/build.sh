tag=${1:-Dev_0}  # override tag name with arg 1 (default: Dev_0)
repoUrl=${2:-"sec-isc-team-isc-icp-docker-local.artifactory.swg-devops.com/isc-car-connector-azure"}  # override repo url name with arg 2

docker build . -t $repoUrl:$tag
docker push $repoUrl:$tag