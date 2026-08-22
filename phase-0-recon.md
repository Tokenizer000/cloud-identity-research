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

-----AUTHENTICATED RECON------ 
-Getting access token- 
Command: 'curl -s -X POST "https://login.microsoftonline.com/a9b4c09e-f456-4983-a3df-c41dcbde1b80/oauth2/v2.0/token" -H "Content-Type: application/x-www-form-urlencoded" -d "client_id=$cid" -d "client_secret=$secret" -d "scope=https://graph.microsoft.com/.default" -d "grant_type=client_credentials" | jq'

--The Recon--
Command: 'curl -s "https://graph.microsoft.com/v1.0/users" -H "Authorization: Bearer $token" | jq'
"Infos obtained: We got the lists of users, their infos and the ids

Command: 'curl -s "https://graph.microsoft.com/v1.0/organization" -H "Authorization: Bearer $token"' | jq
"Infos Obtained: We saw the tenents m365 subscription plan, that tenant is managed, tenant id and others"

Command: curl -s -X GET \
"https://graph.microsoft.com/v1.0/servicePrincipals?\$select=displayName,appId,appOwnerOrganizationId,keyCredentials,passwordCredentials" \
-H "Authorization: Bearer $TOKEN" | jq '.value[] | select(.appOwnerOrganizationId == "$tenant_id")'
Infos Obtained: We saw the list of service principals in the tenant and their permisions 
Command: 'curl -s "https://graph.microsoft.com/v1.0/roleManagement/directory/roleAssignments?$expand=principal"'
"Infos Obtained: We saw the roles assigned with the corrensponding user/sp object id

