### JINJA 2 template engine
'''
{{ }} expressions to print output in html
{%...%} conditions, for loops
{#...#} this for comments

'''


from flask import Flask,render_template,request,redirect,url_for


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


### Variable rule
@app.route('/success/<int:score>')
def success(score):
    res=""
    if score>=50:
        res="PASSED"
    else:
        res="FAILED"
    
    return render_template('result.html',results=res)

@app.route('/successres/<int:score>')
def successres(score):
    res=""
    if score>=50:
        res="PASSED"
    else:
        res="FAILED"
    
    exp={'score':score,"res":res}
    return render_template('result1.html',results=exp)

## if conditions
@app.route('/successif/<int:score>')
def successif(score):
    return render_template('result.html',results=score)


@app.route('/fail/<int:score>')
def fail(score):    
    return render_template('result.html',results=score)

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        Science = float(request.form['Science'])
        Maths = float(request.form['Maths'])
        C = float(request.form['C'])
        DataScience = float(request.form['DataScience'])

        total_score = round((Science + Maths + C + DataScience) / 4)
        return redirect(url_for('successres', score=total_score))

    # for GET, show the form
    return render_template('getresult.html')



if __name__ == "__main__":
    app.run(debug=True)