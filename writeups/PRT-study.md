What is a PRT? A PRT is a jwt artifact issued to an entra id joined device to enable them to perform SSO on 
apps. It is encrypted and paired with a session key and has a lifetime of 90 days.

How a PRT is issued: A user logs in to theri windows machine and cloudAP collects their login credentials and 
request a nonce from microsoft, then it signs the nonce with the device key issued during registration, then it 
sends the credentials together with the nonce and then sends it to entra id and then entra id verifies the nonce 
with the corresponding device public key and then also verifies the users credentials and if both steps succeeds 
then it issues an encrypted prt with an encrypted session key which cloudAP now recieves, decrypt using the 
transport key and then store them in lsass process memory.

How a PRT is used to obtain access token: When a user opens a microsoft app or visit an enterprise website the 
app checks if there is an active session, if there isnt then it sends an authentication request to entra id 
which is then intercepted by WAM if it had no access tokens then it sends a request to cloudAP which then 
recieves an nonce from entra id and then signs the nonce using the PRTs session key and then sends it to entra 
id along with the encrypted prt and then the entra id decrypt the prt with the public transprt key and then 
extract the session key from the prt and then uses it to verify the nonce if both process are successful it then 
returns with an access token and refresh token.

Pass the PRT: Its an attack where an attacker tricks cloudAP into issuing a prt cookie (Encryted prt+signed 
nonce) then the attacker copies the cookie to the own device and then sends it to entra id which issues then 
access and refresh token and they can use the refresh token to obtain more access token and refresh token
