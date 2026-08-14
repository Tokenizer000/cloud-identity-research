# MS vs Keycloak Token Comparison
**Phase 1 — Build First Exercise**
**Lab:** `/labs/01-token-attacks/README.md`

---

## How Each Token Was Obtained

| | Microsoft | Keycloak |
|---|---|---|
| **Method** | `az account get-access-token --resource https://graph.microsoft.com` | Login as alice/alice123 at http://localhost:5000, captured JWT from /dashboard |
| **Resource** | Microsoft Graph API | victim-app (Flask lab) |
| **Realm/Tenant** | `a9b4c09e-f456-4983-a3df-c41dcbde1b80` | `victim-corp` |
| **Decoded at** | jwt.io | jwt.io |

---

## Header Comparison

| Claim | Microsoft | Keycloak | Notes |
|---|---|---|---|
| `alg` | `RS256` | `RS256` | Both use asymmetric signing — the attack surface for RS256→HS256 confusion exists on both |
| `typ` | `JWT` | `JWT` | Standard |
| `kid` | `fEtqrhKT1bXAGafSdQoN1vXTRpI` | `dT36zOmUDghjEBCFSUvS58_8bBCBQLuKjnxD0wmunO4` | Key ID — used to look up the public key for verification. This is the field JKU injection targets |
| `nonce` | ✅ Present (`awqyTtF4...`) | ❌ Absent | Microsoft includes a server-generated nonce in the header to prevent token replay. Keycloak does not |
| `x5t` | ✅ Present (`fEtqrhKT...`) | ❌ Absent | X.509 certificate thumbprint — another key identifier. Microsoft uses both `kid` and `x5t`; Keycloak uses only `kid` |

**Key observation:** Microsoft's header carries two key identifiers (`kid` + `x5t`) plus a replay-prevention `nonce`. Keycloak uses only `kid`. The `nonce` in the Microsoft header is what makes raw token replay harder — a replayed token carries the original nonce, which STS can reject.

---

## Payload Comparison — Standard OIDC/JWT Claims

These claims exist in both tokens (RFC 7519 standard claims):

| Claim | Microsoft Value | Keycloak Value | Notes |
|---|---|---|---|
| `iss` | `https://sts.windows.net/a9b4c09e-f456-4983-a3df-c41dcbde1b80/` | `http://localhost:8080/realms/victim-corp` | **Issuer**. MS includes the tenant ID in the issuer URL — it is tenant-scoped at the issuer level itself |
| `aud` | `https://graph.microsoft.com/` | `account` | **Audience**. MS scopes to a specific resource URI. Keycloak uses a short client ID string. A Microsoft token for Graph cannot be replayed against ARM — different `aud` |
| `sub` | `2zMo5nJUGGafKI2UBWGqUdxsEItMLZAMB9_PLocVtNk` | `6989718c-cfc3-4005-ac2b-d60dd58b3629` | **Subject**. MS `sub` is pairwise-pseudonymous (different per application — changes if the same user accesses a different app). Keycloak `sub` is a stable UUID across clients |
| `iat` | `1785877150` (2026-08-04 20:59 UTC) | `1785876539` (2026-08-04 20:48 UTC) | Issued at |
| `exp` | `1785881884` (2026-08-04 22:18 UTC) | `1785876839` (2026-08-04 20:53 UTC) | Expiry |
| `acr` | `1` | `1` | Authentication context class reference. `1` = password authentication |
| `sid` | `006cac6a-3377-9b08-4540-f2758380ab5d` | `6843992e-aca9-4d12-a157-46aa46da4657` | Session ID — used to correlate tokens to an auth session. Revocation targets the session |
| `email` | `ghostmane2026@outlook.com` | `alice@gmail.com` | User email |
| `scope` / `scp` | (see below) | `openid profile email` | Authorized scopes |

---

## Payload Comparison — Token Lifetime

| | Microsoft | Keycloak |
|---|---|---|
| **Lifetime** | ~79 minutes | **5 minutes** |
| **`nbf`** | Present (same as `iat`) | Absent |

**Key observation:** The Microsoft token is valid for nearly 80 minutes. The Keycloak lab token is valid for only 5 minutes. This matters for attack windows: a stolen Microsoft access token gives an attacker almost 80 minutes of uninterrupted access to Graph API before it expires. This is why access token theft (AiTM, token replay) is so effective against Microsoft environments — the tokens are long-lived by design.

The `nbf` (not before) claim in the Microsoft token is redundant here (same value as `iat`) but exists. RFC 7519 specifies it as optional. Keycloak omits it entirely for short-lived tokens.

---

## Payload Comparison — Microsoft-Only Claims

These claims are absent from the Keycloak token entirely:

### Identity & Tenant

| Claim | Value | What It Means |
|---|---|---|
| `tid` | `a9b4c09e-f456-4983-a3df-c41dcbde1b80` | **Tenant ID** — the Azure AD tenant this token belongs to. Every resource in Azure validates `tid` to ensure cross-tenant token replay is rejected. This is the primary isolation boundary in multi-tenant Entra |
| `oid` | `3b1c4d34-760b-4e6c-a65e-c286bfe8ca8f` | **Object ID** — the user's stable, immutable identifier in the directory. Unlike `sub` (which is pairwise), `oid` is the same across all apps in the tenant. Azure RBAC assignments, audit logs, and directory objects use `oid` as the canonical user reference. If you're forging a token, wrong `oid` = wrong identity |
| `puid` | `10032005F4DDE016` | **Passport UID** — Microsoft Account (MSA) identifier. Present because this user authenticated via live.com (personal MSA), not a pure work/school account |
| `unique_name` | `live.com#ghostmane2026@outlook.com` | Canonical login name. The `live.com#` prefix indicates MSA federation — this is a guest/external identity, not a native Entra account |
| `idp` | `live.com` | **Identity Provider** — who authenticated the user. `live.com` = Microsoft personal account. A native Entra account would show the tenant's domain here. This indicates the user is an MSA-backed identity using B2B or consumer federation |
| `altsecid` | `1:live.com:00030001AF7AC358` | Alternate security ID for MSA-linked accounts |
| `idtyp` | `user` | Identity type. Can be `user` or `app`. For application-only tokens (client credentials flow), this would be `app` and `scp` would be absent, replaced by `roles` |

### Authorization

| Claim | Value | What It Means |
|---|---|---|
| `scp` | `AuditLog.Read.All Directory.ReadWrite.All email Group.ReadWrite.All IdentityProvider.ReadWrite.All openid profile User.Invite.All` | **Delegated scopes** — what the app is authorized to do *on behalf of the user*. These are OAuth2 permissions. The user consented to these. Contrast with `roles` (application permissions, no user involved) |
| `wids` | `["62e90394-69f5-4237-9190-012177145e10", "b79fbf4d-3ef9-4689-8143-76b194e85509"]` | **Directory role IDs** assigned to this user. Decoded: **Global Administrator** + **Privileged Role Administrator**. This token belongs to a Global Admin. This is why stealing it would be catastrophic — the `scp` combined with `wids` gives full tenant control |

### Authentication Method & State

| Claim | Value | What It Means |
|---|---|---|
| `amr` | `["pwd", "mfa"]` | **Authentication Method References** — how the user proved identity. `pwd` = password, `mfa` = MFA completed. If MFA was not completed, `mfa` would be absent, and Conditional Access policies requiring MFA would block access |
| `acrs` | `["p1", "pfdr"]` | Authentication context class references. `p1` = Conditional Access policy 1 satisfied. `pfdr` = Phishing-resistant device requirement met |
| `signin_state` | `["kmsi"]` | **Keep Me Signed In** — the user checked "stay signed in." This affects session persistence |
| `platf` | `3` | Platform. `3` = Windows |
| `ipaddr` | `102.91.78.122` | IP address at authentication time. Used by Conditional Access for location-based policies. If you replay a token from a different IP, some policies will flag it |

### Microsoft Internal / `xms_` Claims

These are Microsoft-private extended claims. They are not standardized and vary by token version and service:

| Claim | Value | What It Means |
|---|---|---|
| `xms_tcdt` | `1780680505` | Tenant creation date (Unix timestamp). Used internally |
| `xms_pftexp` | `1785968284` (2026-08-05 22:18 UTC) | **Primary Refresh Token (PRT) expiry**. This is the expiry of the underlying PRT that was used to mint this access token. The PRT survives for ~24 hours after the access token expires. This is the high-value artifact in PRT attacks |
| `xms_st` | `{"sub": "lhBoikCyK8Q3gkUrZ49KFWy8F99Kt6gGZiMuyxsdc6I"}` | Shadow token subject — a secondary `sub` claim for internal Microsoft use |
| `xms_idrel` | `30 1` | Internal identity relationship flag |
| `xms_acd` | `1490315001` | Account creation date |
| `xms_ftd` | `OTorOz_yDhP7idwx0yEFL7...` | Internal feature/flight data |
| `ver` | `1.0` | Token schema version. v1.0 is the older format; v2.0 tokens use the `/v2.0` endpoint and have slightly different claim names |
| `uti` | `9pVx6syvlUy4JBSFXFVcAA` | Unique token identifier — a per-token opaque ID used in audit logs and telemetry |
| `rh` | `1.AUEBnsC0...` | Refresh hash — internal claim used to invalidate tokens when the session changes |
| `aio` | `AaQAW/8cAAAA...` | Azure AD internal opaque token — used for caching and session management |

### Application Identity

| Claim | Value | What It Means |
|---|---|---|
| `appid` | `b677c290-cf4b-4a8e-a60e-91ba650a4abe` | **Application ID** (client ID) of the app that requested this token. Here: AzurePortal Console App. Every token carries which app minted it |
| `app_displayname` | `AzurePortal Console App` | Human-readable name of the requesting app |
| `appidacr` | `0` | How the app authenticated. `0` = public client (no client secret/certificate). `1` = client secret. `2` = certificate |

---

## Payload Comparison — Keycloak-Only Claims

These claims are present in the Keycloak token but absent from the Microsoft token:

| Claim | Value | What It Means |
|---|---|---|
| `jti` | `fa47c8df-28f6-4491-9427-fb8d1a05224b` | **JWT ID** — a unique identifier for this specific token. RFC 7519 says `jti` can be used to prevent replay by tracking used token IDs. Microsoft uses `uti` for a similar purpose |
| `azp` | `victim-app` | **Authorized party** — the client that requested the token. Equivalent to Microsoft's `appid`. Keycloak uses `azp`; Microsoft uses `appid` |
| `typ` | `Bearer` | Explicit token type in the payload. Microsoft doesn't include this in the payload (only in the header) |
| `session_state` | `6843992e-...` | Keycloak's session reference. Microsoft uses `sid` for the same purpose (both present in this comparison, but the claim name differs) |
| `allowed-origins` | `["http://localhost:5000"]` | CORS origin restriction — which origins are allowed to use this token. Not a standard JWT claim; Keycloak-specific |
| `realm_access` | `{"roles": ["offline_access", "uma_authorization", "default-roles-victim-corp"]}` | **Realm-level roles** — roles assigned at the Keycloak realm level. This is how Keycloak encodes authorization. Microsoft uses `wids` for directory roles and `roles` (in app tokens) |
| `resource_access` | `{"account": {"roles": ["manage-account", "manage-account-links", "view-profile"]}}` | **Client-level roles** — roles for a specific client (here: the built-in `account` client). Keycloak nests roles per resource; Microsoft flattens them |
| `email_verified` | `false` | Whether the email address has been verified. Standard OIDC claim. Microsoft does not include this in access tokens (it appears in ID tokens) |

---

## Role/Authorization Model — The Critical Difference

This is the most important structural difference for an attacker:

**Keycloak:**
```json
"realm_access": {
  "roles": ["offline_access", "uma_authorization", "default-roles-victim-corp"]
},
"resource_access": {
  "account": {
    "roles": ["manage-account", "manage-account-links", "view-profile"]
  }
}
```
Roles are embedded directly in the token payload, nested by scope (realm vs resource). If an app reads `realm_access.roles` to make authorization decisions and doesn't verify the signature, **role claim forgery directly grants escalated access**. Attack 4 in Phase 1 (Role Claim Forgery) targets exactly this.

**Microsoft:**
```json
"scp": "AuditLog.Read.All Directory.ReadWrite.All email Group.ReadWrite.All IdentityProvider.ReadWrite.All openid profile User.Invite.All",
"wids": ["62e90394-69f5-4237-9190-012177145e10", "b79fbf4d-3ef9-4689-8143-76b194e85509"]
```
Microsoft separates delegated permissions (`scp`) from directory role assignments (`wids`). The `wids` claim encodes which Entra directory roles this user holds — decoded here as **Global Administrator** and **Privileged Role Administrator**. The authorization model is more layered: Microsoft resources validate the token signature, check `aud`, check `tid`, check `scp`, and then separately consult the directory for role assignments.

**Attacker implication:** Forging a Keycloak token with elevated `realm_access.roles` is straightforward if signature validation is broken. Forging a Microsoft token to claim `wids` roles is harder — Microsoft's resource servers don't blindly trust `wids` from the token; they cross-reference the directory. But the `scp` claim is trusted from the token directly and defines what API endpoints are accessible.

---

## `scope` / `scp` — Delegated Permissions Comparison

| | Microsoft | Keycloak |
|---|---|---|
| **Claim name** | `scp` (space-separated string) | `scope` (space-separated string) |
| **Value** | `AuditLog.Read.All Directory.ReadWrite.All email Group.ReadWrite.All IdentityProvider.ReadWrite.All openid profile User.Invite.All` | `openid profile email` |
| **Scope of access** | Extremely broad — read audit logs, read/write the entire directory, manage groups, manage identity providers, invite users | Minimal — basic OIDC profile scopes only |

The Microsoft token here has **Directory.ReadWrite.All** and **IdentityProvider.ReadWrite.All** — combined with the Global Admin `wids`, this token would allow an attacker to read/write any object in the tenant directory and modify identity providers (e.g., add a rogue IdP for persistent access). This is a highly privileged token.

---

## Token Lifetime — Attack Window Comparison

| | Microsoft | Keycloak (lab) |
|---|---|---|
| **Access token lifetime** | ~79 minutes | 5 minutes |
| **Underlying session** | PRT expiry: ~24 hours after (`xms_pftexp`) | Session state ID in `session_state` |

**Why this matters:** A 5-minute Keycloak token stolen via AiTM gives an attacker a 5-minute window before the token expires and they need to steal another one. A 79-minute Microsoft Graph token gives an attacker 79 minutes to enumerate the directory, exfiltrate data, or establish persistence before they need a new token. Microsoft's longer-lived tokens are a deliberate usability tradeoff — and a significant part of why token theft is the dominant initial access technique in cloud identity attacks.

The `xms_pftexp` claim reveals that the underlying PRT (Primary Refresh Token) that minted this access token doesn't expire until 24 hours later. AiTM attacks (Evilginx2, Muraena) target PRTs specifically because stealing the PRT means continuous token minting — you get a fresh access token every time you need one, for 24 hours, without re-authenticating the user.

---

## Summary — What's the Same

- Both use **RS256** asymmetric signing (public/private key pair)
- Both use `kid` in the header to reference the signing key
- Both encode standard claims: `iss`, `aud`, `sub`, `iat`, `exp`, `acr`, `sid`, `email`
- Both include user profile info (`name`, `email`, `family_name`, `given_name`)
- Both use space-separated scope strings
- Both are **bearer tokens** — possession = access, no proof of possession required

---

## Summary — What's Different (Attacker Perspective)

| Dimension | Microsoft | Keycloak |
|---|---|---|
| **Tenant isolation** | `tid` + tenant-scoped `iss` — hard boundary | No equivalent — single-realm deployment |
| **User identity** | `oid` (stable) + `sub` (pairwise per-app) | `sub` only (stable UUID) |
| **Role encoding** | `wids` (directory role GUIDs) + `scp` (delegated) | `realm_access.roles` + `resource_access` (inline strings) |
| **App identity** | `appid` + `appidacr` + `app_displayname` | `azp` only |
| **Auth method** | `amr` (pwd, mfa) + `acrs` + `signin_state` | `acr` only |
| **Token lifetime** | ~79 minutes | 5 minutes |
| **Replay protection** | Header `nonce` + `uti` per-token | `jti` per-token |
| **Underlying session** | PRT (`xms_pftexp`) — 24h validity | `session_state` — shorter lived |
| **External IdP chain** | `idp: live.com` + `altsecid` + `puid` (MSA federation visible) | No federation chain in token |
| **Private extensions** | 10+ `xms_` claims (internal telemetry, PRT data) | None |
| **Header key IDs** | `kid` + `x5t` (two identifiers) | `kid` only |

---

## Notes on Token Validity

The Keycloak token payload contains a JSON formatting artifact (`"name":"alice ae":"alice"`) from the copy-paste — this is a paste corruption, not present in the actual token. The underlying payload bytes decoded correctly; the malformation is in the base64-encoded string as pasted.

The Microsoft token was issued today (2026-08-04) and has since expired (`exp: 22:18 UTC`). The Keycloak token expired 5 minutes after issuance. Neither token is currently valid. Do not attempt to use either for API access.
