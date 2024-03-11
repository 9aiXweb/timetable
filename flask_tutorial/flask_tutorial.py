from flask import Flask, redirect, url_for, render_template
app = Flask(__name__)

@app.route('/')
def index():
   return render_template('hello.html')

@app.route('/hello/<user>')
def hello_name(user):
   return render_template('hello.html', name=user)

@app.route('/url')
def url():
   print(url_for('index'))
   print("hello")
   return redirect(url_for('index'))

if __name__ == '__main__':
   app.run(debug = True)