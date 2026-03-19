from flask import Flask # Class

app = Flask(__name__) # Object

@app.route('/') # Registring the function with url
def home():
    x = 10
    return f"Hello From Home Function {x}"
    

app.run() # Object Method ---> whose object ---> of Flask Class
