Technique: help desk vishing to MFA reset or new device registration. 
Mental model: they did not attack cryptography. They attacked the human process for replacing a cryptographic device. The weakest link in any MFA deployment is not the authenticator — it is the recovery process. Specifically: what does a help desk agent need to hear before they will reset MFA for a caller they cannot see?

Technique: immediate pivot to Okta / Azure AD after initial access. 
Mental model: compromise the identity provider, not the application. One Okta or Azure AD compromise equals access to every downstream application in the tenant. The architectural leverage is in the IdP. Individual application compromises are multiplicatively less valuable.

Technique: MFA fatigue — push notification spam at 2am. 
Mental model: human attention is finite and predictable. At 2am, a user receiving the 20th push notification will approve it to make their phone stop buzzing. This is not a technical attack. It is a cognitive attack with a near-deterministic success rate. The MFA implementation is perfect. The human using it is not.
