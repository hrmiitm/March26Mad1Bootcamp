from flask import Flask # Class

xyz = Flask(__name__) # Object

@xyz.route('/') # Registring the function with url
def home():
    x = 10
    return f"Hello From Home Function {x}"
    

xyz.run() # Object Method ---> whose object ---> of Flask Class
