from flask import Flask, render_template

app = Flask(__name__)

books = [
    {
        "title": "1984",
        "author": "George Orwell"
    },
    {
        "title": "Ulysses",
        "author": "James Joyce"
    },
    {
        "title": "Pride and Prejudice",
        "author": "Jane Austen"
    }
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/books")
def show_books():
    return render_template("books.html", books=books)

@app.route("/about")
def about():
    return render_template("about.html")

app.run(debug=True)