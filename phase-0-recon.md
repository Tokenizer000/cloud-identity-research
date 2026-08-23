# Phase 0 — Entra ID Tenant Reconnaissance
**Target:** ghostmane2026outlook.onmicrosoft.com  
**Date:** 2026-08-20  
**Tenant ID:** a9b4c09e-f456-4983-a3df-c41dcbde1b80

---

## Unauthenticated Reconnaissance

### 1. OpenID Configuration v1.0
**Command:**
curl -s "https://login.microsoftonline.com/ghostmane2026outlook.onmicrosoft.com/.well-known/openid-configuration" | jq

**Findings:**
- Tenant ID extracted without authentication
- Token endpoint confirmed: /oauth2/token
- Device authorization endpoint confirmed — device code flow available
- Kerberos endpoint present — potential hybrid configuration signal
- Supported grant types and response types enumerated
- Signing algorithm: RS256

**Offensive significance:**
Device code endpoint confirmed available. No Conditional Access
on Business Basic/Standard means device code phishing is 
unblocked. Kerberos endpoint warrants further hybrid investigation.

---

### 2. OpenID Configuration v2.0
**Command:**
curl -s "https://login.microsoftonline.com/ghostmane2026outlook.onmicrosoft.com/v2.0/.well-known/openid-configuration" | jq

**Findings:**
- Wider scope support including offline_access
- tls_client_auth supported

**Offensive significance:**
offline_access scope means device code phishing returns both
access token AND refresh token. Refresh token valid up to 90
days — durable persistence without re-authentication.

---

### 3. Namespace/Realm Identification
**Command:**
curl -s "https://login.microsoftonline.com/getuserrealm.srf?login=james@ghostmane2026outlook.onmicrosoft.com&xml=1"

**Findings:**
- NameSpaceType: Managed
- IsFederatedNS: false
- State: 4 for both existing and non-existing users

**Offensive significance:**
Managed namespace — authentication happens directly in Entra ID,
no ADFS to attack. GetUserRealm user enumeration is patched on
managed onmicrosoft.com domains — State 4 returned regardless
of account existence. Enumeration via this endpoint unreliable.
Alternative: GetCredentialType endpoint.

---

### 4. User Enumeration via GetCredentialType
**Command:**
curl -s "https://login.microsoftonline.com/common/GetCredentialType" \
-H "Content-Type: application/json" \
-d '{"username":"james@ghostmane2026outlook.onmicrosoft.com"}' | jq

**Findings:**
- IfExistsResult: 0 = user exists
- IfExistsResult: 1 = user does not exist
- Credential type: password confirmed for existing users

**Offensive significance:**
Valid user enumeration primitive against managed tenants.
Use for building spray target list before Phase 1 password spray.

---

## Phase 0.3 — Perimeter Reconnaissance

**Tool:** Shodan  
**Date:** 2026-08-22

**Queries run:**
- ssl:"ghostmane2026outlook.onmicrosoft.com" → No results
- org:"Microsoft" hostname:"ghostmane2026outlook.onmicrosoft.com" → No results
- http.title:"ghostmane2026" country:"NG" → No results

**Conclusion:**
No internet-exposed infrastructure detected. No VPN appliances,
RDP, or on-premises services indexed. Phase 1.6 network perimeter
initial access eliminated as attack path. Attack surface is 100%
identity-based.

**Primary initial access paths confirmed:**
- Password spray against legacy auth endpoints
- Device code phishing
- Credential exposure hunting (GitHub, config files, RMM stores)

---

## Authenticated Reconnaissance

### Prerequisites
**Token acquisition:**
curl -s -X POST \
"https://login.microsoftonline.com/$tid/oauth2/v2.0/token" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "client_id=$cid&client_secret=$secret\
&scope=https://graph.microsoft.com/.default\
&grant_type=client_credentials" | jq

Grant type: client_credentials — no user involved, no MFA,
no Conditional Access evaluation. Silent authentication.

---

### 1. Tenant/License Enumeration
**Command:**
curl -s "https://graph.microsoft.com/v1.0/organization" \
-H "Authorization: Bearer $TOKEN" | jq

**Findings:**
- Tenant confirmed managed
- assignedPlans: empty — no M365 licenses
- No Defender for Endpoint, no Entra ID P2, no Conditional Access

**Offensive significance:**
No security monitoring products active. Operating environment
is unmonitored. No behavioral analytics or identity protection alerts.

---

### 2. User Enumeration
**Command:**
curl -s "https://graph.microsoft.com/v1.0/users" \
-H "Authorization: Bearer $TOKEN" | jq

**Findings:**
- 7 users total
- Guest accounts identifiable via #EXT# suffix in UPN
- Two Global Admins identified by cross-referencing role assignments
- Backup Admin Service account — no mail, likely no MFA
- Frank (guest) holds Global Admin — misconfiguration
- Ghost Mane — tenant owner account (also guest/external)

**Key targets:**
- backupadmin@ghostmane2026outlook.onmicrosoft.com — service
  account, no MFA likely, high value spray target
- Frank — guest Global Admin, authentication controlled by
  external tenant, not directly attackable from within

---

### 3. Role Assignment Enumeration
**Command:**
curl -s "https://graph.microsoft.com/v1.0/roleManagement/directory/roleAssignments?\$expand=principal" \
-H "Authorization: Bearer $TOKEN" | jq

**Findings:**
- Role GUID 62e90394-69f5-4237-9190-012177145e10 = Global Administrator
- Two principals hold Global Admin
- One principal (Frank) holds three roles simultaneously
- Guest account holding Global Admin = misconfiguration

---

### 4. Service Principal Enumeration
**Command:**
curl -s "https://graph.microsoft.com/v1.0/servicePrincipals?\$select=displayName,appId,appOwnerOrganizationId,keyCredentials,passwordCredentials" \
-H "Authorization: Bearer $TOKEN" | jq \
'.value[] | select(.appOwnerOrganizationId == "a9b4c09e-f456-4983-a3df-c41dcbde1b80")'

**Note:** appOwnerOrganizationId filter not supported server-side
by Graph API — client-side filtering with jq required.

**Findings:**
- One tenant-owned principal: Test-App
- passwordCredentials and keyCredentials: empty arrays
- Secret exists but Graph never returns secret values post-creation
- Secret retrievable only at creation time

**Offensive significance:**
Cannot extract existing secrets via Graph. Can add new credentials
to existing high-privilege principals — stealthier than creating
new principals as no new object appears in directory.

---

## Key Findings Summary

| Finding | Offensive Significance |
|---------|----------------------|
| Managed namespace | No ADFS attacks available |
| Device code endpoint active | Phishing unblocked — no CA |
| offline_access on v2.0 | Refresh token obtainable — 90 day persistence |
| No assigned licenses | Unmonitored environment |
| Guest Global Admin | Misconfiguration — external account with tenant-wide privilege |
| Backup Admin service account | High value spray target — likely no MFA |
| No Shodan results | Phase 1.6 eliminated — identity-only attack surface |
