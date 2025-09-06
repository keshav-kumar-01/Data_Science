from flask import Flask,render_template,request


'''
It creates an instance of Flask class , which will be your WSGI application.
'''
### WSGI application
app=Flask(__name__)

@app.route("/")
def Welcome():
    return "<html><H1>Hello World</H1></html>"

@app.route("/index",methods=['GET'])
def index():
    return render_template('index.html')
@app.route("/about")
def about():
    return render_template('about.html')

@app.route('/form',methods=['GET','POST'])
def form():
    if request.method=='POST':
        name=request.form['name']
        return f'Hello {name}!'
    return render_template('form.html')

if __name__ == "__main__":
    app.run(debug=True)