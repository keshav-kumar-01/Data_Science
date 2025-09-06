from flask import Flask


'''
It creates an instance of Flask class , which will be your WSGI application.
'''
### WSGI application
app=Flask(__name__)

@app.route("/")
def Welcome():
    return "Welcome to best home page.this is amazing"

@app.route("/index")
def index():
    return "Welcome to best index page.this is amazing"

if __name__ == "__main__":
    app.run(debug=True)