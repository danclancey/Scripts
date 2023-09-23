#!/bin/bash

# Prepare directory
mkdir -p /tmp/opensearch_certs
cd /tmp/opensearch_certs

# Collect certificate information
echo "Enter Cluster Name:"
read CLUSTER_NAME
echo "Enter Country (e.g., US):"
read CSR_COUNTRY
echo "Enter State (e.g., California):"
read CSR_STATE
echo "Enter City (e.g., San Francisco):"
read CSR_CITY
echo "Enter Organization (e.g., MyOrganization):"
read CSR_ORGANIZATION

# Create Root CA
openssl genrsa -out root-ca-key.pem 2048
openssl req -new -x509 -sha256 -key root-ca-key.pem -subj "/C=${CSR_COUNTRY}/ST=${CSR_STATE}/L=${CSR_CITY}/O=${CSR_ORGANIZATION}/OU=UNIT/CN=root" -out root-ca.pem -days 730

# Create Admin cert
openssl genrsa -out admin-key-temp.pem 2048
openssl pkcs8 -inform PEM -outform PEM -in admin-key-temp.pem -topk8 -nocrypt -v1 PBE-SHA1-3DES -out admin-key.pem
openssl req -new -key admin-key.pem -subj "/C=${CSR_COUNTRY}/ST=${CSR_STATE}/L=${CSR_CITY}/O=${CSR_ORGANIZATION}/OU=UNIT/CN=A" -out admin.csr
openssl x509 -req -in admin.csr -CA root-ca.pem -CAkey root-ca-key.pem -CAcreateserial -sha256 -out admin.pem -days 730

# Ask for number of nodes
echo "Enter number of nodes:"
read nodeCount

declare -a nodeNames
# Loop to read each node name
for ((i=1;i<=nodeCount;i++));
do
  echo "Enter name for node $i:"
  read nodeName
  nodeNames+=($nodeName)
done

# Create Node certs
for NODE in "${nodeNames[@]}";
do
	openssl genrsa -out ${NODE}-key-temp.pem 2048
	openssl pkcs8 -inform PEM -outform PEM -in ${NODE}-key-temp.pem -topk8 -nocrypt -v1 PBE-SHA1-3DES -out ${NODE}-key.pem
	openssl req -new -key ${NODE}-key.pem -subj "/C=$CSR_COUNTRY/ST=${CSR_STATE}/L=${CSR_CITY}/O=${CSR_ORGANIZATION}/OU=UNIT/CN=${NODE}" -out ${NODE}.csr
	echo "subjectAltName=DNS:${NODE}" > ${NODE}.ext
	openssl x509 -req -in ${NODE}.csr -CA root-ca.pem -CAkey root-ca-key.pem -CAcreateserial -sha256 -out ${NODE}.pem -days 730 -extfile ${NODE}.ext
	rm -f *-temp.pem *.csr *.ext

	# Create a comma-separated list of quoted node names
	seed_hosts=$(printf ',"%s"' "${nodeNames[@]}")
	seed_hosts=${seed_hosts:1} 
	initial_master_nodes=$seed_hosts

	YML_CONFIG="cluster.name: ${CLUSTER_NAME}\n"
	YML_CONFIG+="node.name: ${NODE}\n"
	YML_CONFIG+="\npath.data: /var/lib/opensearch\n"
	YML_CONFIG+="path.logs: /var/log/opensearch\n"
	YML_CONFIG+="\ntransport.host: 0.0.0.0\n"
	YML_CONFIG+="transport.tcp.port: 9300\n"
	YML_CONFIG+="\nnetwork.host: 0.0.0.0\n"
	YML_CONFIG+="http.port: 19200\n"
	YML_CONFIG+="\naction.auto_create_index: true\n"
	YML_CONFIG+="\ndiscovery.seed_hosts: [ ${seed_hosts} ]\n"
	YML_CONFIG+="cluster.initial_master_nodes: [ ${initial_master_nodes} ]\n"
	YML_CONFIG+="node.master: true\n"
	YML_CONFIG+="plugins.security.disabled: false\n"
	YML_CONFIG+="\nplugins.security.ssl.transport.enforce_hostname_verification: false\n"
	YML_CONFIG+="plugins.security.ssl.transport.enabled: true\n"
	YML_CONFIG+="plugins.security.ssl.transport.pemcert_filepath: /etc/opensearch/${NODE}.pem\n"
	YML_CONFIG+="plugins.security.ssl.transport.pemkey_filepath: /etc/opensearch/${NODE}-key.pem\n"
	YML_CONFIG+="plugins.security.ssl.transport.pemtrustedcas_filepath: /etc/opensearch/root-ca.pem\n"
	YML_CONFIG+="plugins.security.ssl.http.enabled: true\n"
	YML_CONFIG+="plugins.security.ssl.http.pemcert_filepath: /etc/opensearch/${NODE}.pem\n"
	YML_CONFIG+="plugins.security.ssl.http.pemkey_filepath: /etc/opensearch/${NODE}-key.pem\n"
	YML_CONFIG+="plugins.security.ssl.http.pemtrustedcas_filepath: /etc/opensearch/root-ca.pem\n"
	YML_CONFIG+="plugins.security.allow_default_init_securityindex: true\n"
	YML_CONFIG+="\nplugins.security.authcz.admin_dn:\n"
	YML_CONFIG+=" - \"CN=A,OU=UNIT,O=${CSR_ORGANIZATION},L=${CSR_CITY},ST=${CSR_STATE},C=${CSR_COUNTRY}\"\n"
	YML_CONFIG+="\nplugins.security.nodes_dn:\n"

	for NODE_DN in "${nodeNames[@]}";
	do
    		YML_CONFIG+=" - \"CN=${NODE_DN},OU=UNIT,O=${CSR_ORGANIZATION},L=${CSR_CITY},ST=${CSR_STATE},C=${CSR_COUNTRY}\"\n"
	done

	YML_CONFIG+="\nplugins.security.audit.type: internal_opensearch\n"
	YML_CONFIG+="plugins.security.enable_snapshot_restore_privilege: true\n"
	YML_CONFIG+="plugins.security.check_snapshot_restore_write_privileges: true\n"
	YML_CONFIG+="plugins.security.restapi.roles_enabled: [\"all_access\", \"security_rest_api_access\"]\n"

	mkdir ${NODE}
	mv ${NODE}.pem ${NODE}-key.pem ${NODE}/
	cp -p root-ca.pem ${NODE}/
	echo -e "${YML_CONFIG}" > ${NODE}/opensearch.yml
done