import hashlib
pswd = input(">>> ")
pswd = bytes(pswd, 'utf-8')
encryptedPWD = hashlib.sha3_256(pswd).hexdigest()
print(encryptedPWD)
