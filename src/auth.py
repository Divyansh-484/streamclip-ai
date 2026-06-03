import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID     = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

def get_access_token():
    """
    Gets an App Access Token from Twitch using Client Credentials flow.
    This token authenticates API requests (not user-specific).
    """
    url  = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type":    "client_credentials"
    }

    response = requests.post(url, params=params)

    if response.status_code == 200:
        token_data = response.json()
        print(f"✓ Access token obtained")
        print(f"  Token type:  {token_data['token_type']}")
        print(f"  Expires in:  {token_data['expires_in']} seconds "
              f"({token_data['expires_in']//3600} hours)")
        return token_data["access_token"]
    else:
        print(f"✗ Failed to get token: {response.status_code}")
        print(f"  Error: {response.json()}")
        return None


def get_headers(token):
    """
    Returns headers needed for every Twitch API request.
    """
    return {
        "Authorization": f"Bearer {token}",
        "Client-Id":     CLIENT_ID
    }


def get_stream_info(token, channel_name):
    """
    Gets live stream info for a channel.
    Returns None if channel is offline.
    """
    headers = get_headers(token)
    url     = "https://api.twitch.tv/helix/streams"
    params  = {"user_login": channel_name}

    response = requests.get(url, headers=headers, params=params)
    data     = response.json().get("data", [])

    if data:
        stream = data[0]
        print(f"\n✓ Stream found: {channel_name}")
        print(f"  Title:    {stream['title']}")
        print(f"  Game:     {stream['game_name']}")
        print(f"  Viewers:  {stream['viewer_count']:,}")
        return stream
    else:
        print(f"\n✗ {channel_name} is offline or doesn't exist")
        return None


if __name__ == "__main__":
    token = get_access_token()
    if token:
        # Test with a popular channel that's usually live
        get_stream_info(token, "xqc")
        