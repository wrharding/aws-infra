# Using the Competition VPN

1. You need an account within the competition AD.
	* note: at this time anyone with an account can use the VPN (including students), so this is authorization by obscurity.
2. Run the following command to launch the VPN Self Service Page (you obviously need AWS API keys for this step):
```bash
open `aws cloudformation describe-stacks --stack-name Corporate-VPN --query 'Stacks[0].Outputs[?OutputKey==\`SelfServicePortal\`].OutputValue' --output text`
```
3. Login with your AD Credentials
4. Download the proper client for your OS and the Client Configuration file
5. Install client, then add the configuration file as a profile
6. When connecting, login with your AD Credentials
7. You're now on the network and should be able to route to any system in the competition. This includes _all_ the systems in the team ServerSubnets.