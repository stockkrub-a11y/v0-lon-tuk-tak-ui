import requests
from dotenv import load_dotenv
import os

load_dotenv()

def test_https():
    url = 'https://julumxzweprvvcnealal.supabase.co/rest/v1/'
    key = os.getenv('SUPABASE_KEY')
    
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f'HTTPS Connection: OK (status={response.status_code})')
        return True
    except Exception as e:
        print(f'HTTPS Connection Failed: {str(e)}')
        return False

if __name__ == '__main__':
    print('Testing HTTPS connection to Supabase...')
    test_https()