from gradio_client import Client
try:
    client = Client("yisol/IDM-VTON")
    print(client.view_api())
except Exception as e:
    print(e)
