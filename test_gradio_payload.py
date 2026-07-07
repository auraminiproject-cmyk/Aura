from gradio_client import Client

try:
    client = Client("yisol/IDM-VTON")
    # Just to inspect the endpoint format
    info = client.view_api()
    print("API OK")
except Exception as e:
    print(e)
