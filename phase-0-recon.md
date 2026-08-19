Entra id tenant recon

-----UNAUTHENTICATED RECON-----
Command: 'curl -s "https://login.microsoftonline.com/ghostmane2026outlook.onmicrosoft.com/.well-known/openid-configuration"'
Info obtained: We got the tenant id, the token endpoint, supported auth flow, device code endpoint, userinfo endpoint and the kerberos endpoint

Command: 'curl -s "https://login.microsoftonline.com/ghostmane2026outlook.onmicrosoft.com/v2.0/.wellknown/openid-configuration"
Infos obtained: Same infos as the previous but the supported token scope are wider, eg; offline access (return with refresh+access token"'

Command: 'curl -s "https://login.microsoftonline.com/userrealm?login=james@ghostmane2026outlook.onmicrosoft.com"&xml=1"'  OR   curl -s "https://login.microsoftonline.com/common/userrealm/ghostmane2026outlook.onmicrosoft.com?api-version=2.1"
Infos obtained:We found out that tenant is managed not federated

Command: curl -s "https://login.microsoftonline.com/common/GetCredentialType" -H "Content-Type:application/json" -d '{"username":"james@ghostmane2026outlook.onmicrosoft.com"}'
Infos: We got a target users credential if the user is available ( "IfExistsResult": 0) and found out that the target user is available and the credenial type they use is password


