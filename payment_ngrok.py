from pyngrok import ngrok
import os


port = 8000


public_url = ngrok.connect(str(port))
print(f"Ngrok tunnel URL: {public_url}")


os.system(f"python manage.py runserver {port}")