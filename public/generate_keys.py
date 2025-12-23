from py_vapid import Vapid
import os

# Generar claves VAPID
vapid = Vapid()
vapid.generate_keys()
vapid_private_key = vapid.private_pem().decode('utf-8')
vapid_public_key = vapid.public_pem().decode('utf-8')

# Generar SECRET_KEY
secret_key = os.urandom(32).hex()

# Guardar en archivo .env
env_content = f"""VAPID_PRIVATE_KEY={vapid_private_key}
VAPID_PUBLIC_KEY={vapid_public_key}
SECRET_KEY={secret_key}
"""

with open('.env', 'w') as f:
    f.write(env_content)

print("Claves generadas y guardadas en .env:")
print(f"VAPID_PRIVATE_KEY: {vapid_private_key}")
print(f"VAPID_PUBLIC_KEY: {vapid_public_key}")
print(f"SECRET_KEY: {secret_key}")
print("Copia VAPID_PUBLIC_KEY en index.html (línea ~380).")
print("Agrega VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY y SECRET_KEY como variables de entorno en Render.")
print("No subas .env a GitHub (está en .gitignore).")
