from app import create_app

app = create_app()
app.secret_key = 'key@123'

if __name__ == '__main__':
    app.run(debug=False)
