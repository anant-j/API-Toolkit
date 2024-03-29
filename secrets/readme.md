### The following secret keys go in this folder.

> 1.  firebase_keys.json
>     Obtain from Google Firebase Console

```
{
    "type": "",
    "project_id": "",
    "private_key_id": "",
    "private_key": "",
    "client_email": "",
    "client_id": "",
    "auth_uri": "",
    "token_uri": "",
    "auth_provider_x509_cert_url": "",
    "client_x509_cert_url": ""
}

```

<hr/>

> 2.  keys.json

```
{
    "Google_Distance_Matrix": "FROM GOOGLE CLOUD CONSOLE",
    "Github_Webhook": "FROM GITHUB API TOKENS",
    "Telegram": {
        "Key": "FROM Telegram",
        "DeviceID": "Chat_Id from Telegram",
    },
    "Twilio": {
        "MY_ACCOUNT_SID": "FROM TWILIO CONSOLE",
        "MY_AUTH_TOKEN": "FROM TWILIO CONSOLE",
        "MY_TWILIO_NUMBER": "FROM TWILIO CONSOLE"
    },
    "IpInfo": "FROM IPINFO",
    "Hosts": {
        "Redirect_address": "YOUR WEBSITE'S ADDRESS",
        "Origin": "YOUR WEBSITE'S ORIGIN ADDRESS",
        "Home_Location" : "HOME ADDRESS"
    }
}
```

> 3.  config.json

```
{
    "Rate_Limit": {
        "Seconds": 30,
        "Maximum_requests_allowed": 5
    },
    "Performance": {
        "Allowed": 2.0
    }
}
```

<hr/>
