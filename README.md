# SpikedVodka - Automate FB Group Request Handling

If you're not from Ashoka University, the first two sections and the name of the repo are irrelevant to you.

## The Problem

The Ashoka University UG Facebook group had some uninvited guests that could jeopardize the safety of the group. Moreover, amnually verifying whether a person is from Ashoka university by cross-checking every request to the group with the LMS directory is cumbersome & unreliable. A system is required to verify that the person requesting to join the FB group is really an Ashokan. 

## The solution

One possible solution is to ask some open-ended questions. If the answers are v liberal, then one can assume that the person applying is an Ashokan. However, some right wing fellows can also fake liberal answers and get into the group, in order to peek into the evil soup these liberal Ashokans are cooking up.

How can someone joining prove they're an Ashokan? By proving they have something only Ashokans can have. All UG Ashokans have an `@ashoka.edu.in` email address. One can prove they're an Ashokan if they can prove they have access to this email account. Hence, if they prove that they can send an email from this account, they can prove that they're Ashokans.

Then, let's go one step further and automate the entire process, from sending an email to the accepting/rejecting of FB join requests.

## The Architecture

Let Bob be a moderator of the FB group & somebody with an email account (Bob is the automated system).

1. Alice wants to join the Facebook group. 
2. Alice emails Bob with her Ashoka ID -- showing that she has access to an Ashoka ID & consequently, must be an Ashokan -- and asks for a unique code. 
3. Bob verifies the email, checks that the email is indeed from Ashoka University & is an undergraduate email address.
4. Bob then encrypts Alice's email address with his secret key and emails this encrypted text. Let's call this encrypted text `S`. (Done using AES-256 in CBC mode using a random IV every time)
5. Alice copies and pastes `S` into the Facebook form that asks for this encrypted text, and submits it.
6. Bob reviews Alice's request, he decrypts her response (`S`) and finds the decrypted text to be a valid Ashoka email address. 
7. Bob makes a record of the fact that Alice's email address has been used, and accepts her request.

Now, let Mallory be some malicious person.

1. Mallory wants to join the Facebook group but does not have access to the right email account.
2. Scenario 1:
    - Through some means, she obtains Alice's code `S` and submits `S` on the Facebook form.
    - Bob reviews the request and finds it to be a valid email address.
    - However, as Bob made a record of this email being used when Alice joined the group, he finds this request to be a duplicate & rejects it.
3. Scenario 2:
    - Mallory enters some jibberish that decrypts successfully.
    - Bob reviews the request and finds it to be an invalid email address and hence, rejects it.
4. Scenario 3:
    - Alice gives her code to Mallory to join the group with.
    - Bob decrypts her response and finds the decrypted text to be a valid Ashoka email address. 
    - He then accepts the request.
    - Mallory can join the group with Alice's help. Don't be like Alice.

## Diving into the code

The code is documented & commented, you should not have too much of an issue understanding what's being done. 
Moreover, the code is divided into two independent sections:

1. __Email Verification__: sub-module to fetch, verify & respond to emails. It also generates & validates the codes sent out. See [verification.py](verification.py) and [gmail_utils.py](gmail_utils.py)
2. __FB Automation__: sub-module to run Selenium & login to Facebook, open the groups page, extract pending requests & respond to them based on a validation function. See [fb_automation.py](fb_automation.py)

Finally, these two sections are combined and run in [main.py](main.py).

### Python prerequisites

1. `pip3 install selenium`
2. `pip3 install chromedriver`
3. `pip3 install pycrypto`
4. `pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib`

### config.json

You must have a JSON file that contains all info about the FB credentials, Google client secret, which emails to respond to, regex to validate an email etc. It should be structured as follows:

``` javascript
{
    "fb": { 
        "email": "", // fb email to log in with 
        "password": "",  // fb password to log in with 
        "group_url": "https://www.facebook.com/groups/SomeGroupHere/requests/" // the url of the group
    },
    "valid_email_regex": "^[a-z0-9]{1,20}\\.[a-z0-9]{1,20}_(ug|asp)[0-9]{2}@ashoka.edu.in$", // regex to validate an email address
    "email_subject": "Join FB Group", // the subject of the email one must enter
    "datafile": "./data/emails_joined.csv", // data file to store all email addresses that have successfully joined the group
    "client_secret": "./data/client_secret.json", // google client secret
    "access_token": "./data/access_token.pickle", // google access token
    "encryption_key": "superSecureEncryptionKey" // encryption key to encrypt/decrypt email addresses
}
```

### Running

Once you setup your config file & have your Google client secret ready, start the program using: ``` python3 main.py 'path/to/config.json' ```
