import requests
import time
# import sys

GRANT_TYPE = "client_credentials"
authUrl = "https://id.twitch.tv/oauth2/token"
testUrl = "https://api.igdb.com/v4/games"

def get_bearer_token(client_id: str, client_secret: str):
    params = {'client_id': client_id, 'client_secret': client_secret, 'grant_type': GRANT_TYPE}
    
    obj = requests.post(authUrl, data=params)
    expiration_date = time.time() + obj.json()["expires_in"]
    return obj.json()["access_token"], expiration_date


def verify_bearer_token(client_id: str, token: str):
    headers = {'Client-ID': client_id, 'Authorization': f"Bearer {token}"}
    obj = requests.post(testUrl, headers=headers)
    match obj.status_code:
        case 200:
            print ("worked")
        case 401:
            print ("Unauthorized")
        case 408:
            print ("Timeout")
        case _:
            print ("idk you figure it out")

    


