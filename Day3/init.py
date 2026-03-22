





from app import app, db
from models import User

# Create 1 Admin
admin = User(username='admin', email='admin@admin.com', password='a', isAdmin=True)
db.session.add(admin)
db.session.commit()

print('1 Admin Created')

users = [
    ('user1', 'user1@email.com', 'u1'),
    ('user2', 'user2@email.com', 'u2'),
    ('user3', 'user3@email.com', 'u3'),
]

creators = [
    ('creator1', 'creator1@email.com', 'c1'),
    ('creator2', 'creator2@email.com', 'c2'),
    ('creator3', 'creator3@email.com', 'c3'),
]

for (n, e, p) in users:
    user = User(username=n, email=e, password=p)
    db.session.add(user)
    db.session.commit()

print('3 Users Created')

for (n, e, p) in creators:
    user = User(username=n, email=e, password=p, isCreator=True)
    db.session.add(user)
    db.session.commit()


print('3 Creators Created')