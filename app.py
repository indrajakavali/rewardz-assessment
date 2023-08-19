from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
db = SQLAlchemy(app)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True)
    copies = db.Column(db.Integer)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    user_type = db.Column(db.String(20))


class Borrowing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    due_date = db.Column(db.DateTime)
    renewed = db.Column(db.Boolean)


@app.route('/check_book_availability/<title>', methods=['GET'])
def check_book_availability(title):
    book = Book.query.filter_by(title=title).first()
    if book:
        if book.copies > 0:
            return jsonify({"message": f"Book '{title}' is available for borrowing.", "copies_available": book.copies})
        else:
            # Query Borrowing table to find return date
            return jsonify({"message": f"Book '{title}' is not available. It will be returned on ..."})
    else:
        return jsonify({"message": f"Book '{title}' not found."})


@app.route('/get_borrowed_books/<user_id>', methods=['GET'])
def get_borrowed_books(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found."})

    borrowed_books = Borrowing.query.filter_by(user_id=user.id).all()
    books_info = []
    for borrowing in borrowed_books:
        book = Book.query.get(borrowing.book_id)
        books_info.append({
            "title": book.title,
            "due_date": borrowing.due_date.strftime('%Y-%m-%d'),
            "renewed": borrowing.renewed
        })

    return jsonify({"borrowed_books": books_info})


@app.route('/renew_book/<user_id>/<book_id>', methods=['POST'])
def renew_book(user_id, book_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found."})

    borrowing = Borrowing.query.filter_by(user_id=user.id, book_id=book_id).first()
    if not borrowing:
        return jsonify({"message": "This book is not borrowed by the user."})

    if borrowing:
        return jsonify({"message": "This book has already been renewed."})

    borrowing.renewed = True
    borrowing.due_date += timedelta(days=30)
    db.session.commit()

    return jsonify({"message": "Book renewed successfully."})


@app.route('/get_student_borrowing_history/<user_id>', methods=['GET'])
def get_student_borrowing_history(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found."})

    borrowings = Borrowing.query.filter_by(user_id=user.id).all()
    borrowing_history = []
    for borrowing in borrowings:
        book = Book.query.get(borrowing.book_id)
        borrowing_history.append({
            "title": book.title,
            "borrowed_date": borrowing.borrowed_date.strftime('%Y-%m-%d'),
            "due_date": borrowing.due_date.strftime('%Y-%m-%d'),
            "returned_date": borrowing.returned_date.strftime('%Y-%m-%d') if borrowing.returned_date else "Not returned"
        })

    return jsonify({"borrowing_history": borrowing_history})


@app.route('/mark_borrowed/<user_id>/<book_id>', methods=['POST'])
def mark_borrowed(user_id, book_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found."})

    book = Book.query.get(book_id)
    if not book:
        return jsonify({"message": "Book not found."})

    borrowing = Borrowing(user_id=user.id, book_id=book.id, due_date=datetime.now() + timedelta(days=30))
    db.session.add(borrowing)
    db.session.commit()

    return jsonify({"message": f"Book '{book.title}' marked as borrowed for user '{user.username}'."})


@app.route('/mark_returned/<user_id>/<book_id>', methods=['POST'])
def mark_returned(user_id, book_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found."})

    book = Book.query.get(book_id)
    if not book:
        return jsonify({"message": "Book not found."})

    borrowing = Borrowing.query.filter_by(user_id=user.id, book_id=book.id, returned_date=None).first()
    if not borrowing:
        return jsonify({"message": "This book is not currently borrowed by the user."})

    borrowing.returned_date = datetime.now()
    db.session.commit()

    return jsonify({"message": f"Book '{book.title}' marked as returned for user '{user.username}'."})


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)