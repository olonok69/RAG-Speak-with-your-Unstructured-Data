import streamlit_authenticator as stauth
import yaml
from streamlit_authenticator import Authenticate
from yaml.loader import SafeLoader
from IPython import embed

with open("ex.yaml") as file:
    auth = yaml.load(file, Loader=SafeLoader)

hashed_passwords = stauth.Hasher.hash_passwords(credentials=auth["credentials"])

print(hashed_passwords)
