import datetime
import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import base64

# Directorio para guardar las llaves temporales
KEYS_DIR = "temp_keys"
if not os.path.exists(KEYS_DIR):
    os.makedirs(KEYS_DIR)

class RSAManager:
    _current_keys = {} # { "YYYY-MM-DD": (private_key, public_key_pem) }

    @classmethod
    def _get_today_str(cls):
        return datetime.date.today().isoformat()

    @classmethod
    def get_keys(cls):
        today = cls._get_today_str()
        
        # Si ya existen en memoria, las devolvemos
        if today in cls._current_keys:
            return cls._current_keys[today]

        # Intentar cargar desde archivo para persistencia tras reinicio
        priv_path = os.path.join(KEYS_DIR, f"private_{today}.pem")
        pub_path = os.path.join(KEYS_DIR, f"public_{today}.pem")

        if os.path.exists(priv_path) and os.path.exists(pub_path):
            with open(priv_path, "rb") as f:
                private_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
            with open(pub_path, "rb") as f:
                public_key_pem = f.read().decode()
            
            cls._current_keys[today] = (private_key, public_key_pem)
            return private_key, public_key_pem

        # Si no existen, generamos nuevas
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        # Guardar en archivos
        with open(priv_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open(pub_path, "wb") as f:
            f.write(public_key_pem.encode())

        # Limpiar llaves antiguas (opcional, para no llenar el disco)
        cls._cleanup_old_keys()

        cls._current_keys[today] = (private_key, public_key_pem)
        return private_key, public_key_pem

    @classmethod
    def _cleanup_old_keys(cls):
        today = cls._get_today_str()
        for filename in os.listdir(KEYS_DIR):
            if today not in filename:
                try:
                    os.remove(os.path.join(KEYS_DIR, filename))
                except:
                    pass
        # Limpiar memoria
        cls._current_keys = {k: v for k, v in cls._current_keys.items() if k == today}

    @classmethod
    def decrypt_password(cls, encrypted_password_b64: str) -> str:
        try:
            private_key, _ = cls.get_keys()
            encrypted_data = base64.b64decode(encrypted_password_b64)
            decrypted = private_key.decrypt(
                encrypted_data,
                padding.PKCS1v15()
            )
            return decrypted.decode()
        except Exception as e:
            # En caso de error (llave expirada o formato invalido)
            raise ValueError(f"No se pudo descifrar la contraseña. Es posible que la llave haya expirado. {str(e)}")
