#!/bin/bash

#
# Scripts are based on AWS directions:
# https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/client-authentication.html#mutual
#

CLIENT_ID=$1
if [ -z $CLIENT_ID ] ; then
	echo "Usage: $0 <client_cert_name>"
	exit 1
fi

git clone https://github.com/OpenVPN/easy-rsa.git
easy-rsa/easyrsa3/easyrsa init-pki
easy-rsa/easyrsa3/easyrsa build-ca nopass
easy-rsa/easyrsa3/easyrsa build-server-full server nopass
easy-rsa/easyrsa3/easyrsa build-client-full $CLIENT_ID nopass

echo "Importing the Server Certificate. You need this ARN In the VPN-Manifest.yaml as pCertificateArn"
aws acm import-certificate --output text \
	--certificate fileb://pki/issued/server.crt \
	--private-key fileb://pki/private/server.key \
	--certificate-chain fileb://pki/ca.crt

echo "Importing the Client Certificate. You need this ARN In the VPN-Manifest.yaml as pClientRootCertificateChainArn"
aws acm import-certificate --output text \
	--certificate fileb://pki/issued/${CLIENT_ID}.crt \
	--private-key fileb://pki/private/${CLIENT_ID}.key \
	--certificate-chain fileb://pki/ca.crt
