THREAT ACTOR STUDY
1.Where else in an enterprise identity stack is there an authentication decision point that a post-compromise 
attacker could influence? What are the equivalent of ADFS in cloud-native environments?

2.For any target organization, what is the MFA recovery procedure? What information is required? What does an 
attacker need to provide? Can that information be derived from LinkedIn and OSINT?

3.What signals in an organization's culture or financial situation make insider recruitment more likely?

4.For any target environment, who has vendor, support, monitoring, or contractor access to the identity 
infrastructure? What is the identity security of that third party?

5.What other signing key boundaries exist in Microsoft's token validation architecture? What other boundaries 
between consumer and enterprise identity flows are assumed by the code but not explicitly enforced? What does 
the validation code actually check, and what does it assume is checked elsewhere?

JWT REASEARCH 
1.x5u:What happens if a server fails to verify the x5u against a whitelist of accepted uris? If I 
inject my own x5u pointing to my x.509 certificate and sign it with the corresponding private key, if the 
reciepient server fails to verify the x5u could i have successfully forged a valid jwt? what impact could that 
cause? what action can i perform and what damage could i cause?

2.x5c: What happens if a server fails to verify the x5c i injected and blindly uses it to verify my forged token?

3.'CRIT' header parameter
What happens if a 'crit' parameter contains '[]' as opposed by the specs?

