import requests
from PIL import Image
from io import  BytesIO
import imagehash

def calculate_image_hash_from_url(image_url):
    response = requests.get(image_url)
    image_data = response.content
    image = Image.open(BytesIO(image_data))
    hash_value = imagehash.average_hash(image)
    hash_string = str(hash_value)  # Convierte el hash en una cadena
    hash_integer = int(hash_string, 16)  # Convierte la cadena en un entero
    return hash_integer