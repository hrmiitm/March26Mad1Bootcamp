from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph

password= "123"

hash_password = gph(password)

print(hash_password)

user_entered_password = "234"
print(cph(hash_password, user_entered_password))