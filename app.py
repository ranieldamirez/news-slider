# app.py

from flask import Flask, request, jsonify, render_template
from models import db, NewsSource, Headline

def create_app():
    """
    A factory function that creates our Flask app, configures the DB, and defines our endpoints (routes).
    """
    app = Flask(__name__)

    # 1) Tell Flask-SQLAlchemy which database to use.
    # Here, we use a SQLite file called 'news.db'.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 2) Initialize SQLAlchemy with the Flask app's settings
    db.init_app(app)

    # 3) Create all database tables if they don't already exist
    with app.app_context():
        db.create_all()
    
    # 4) Define routes

    @app.route('/')
    def home():
        return render_template('index.html')
    
    @app.route('/about')
    def about():
        return render_template('about.html')
    
    @app.route('/add_source', methods=['POST'])
    def add_source():
        """
        Add a new news source.
        Expects JSON: {"name": "CNN", "bias_score": -5}
        """

        data = request.get_json()
        name = data.get('name')
        bias = data.get('bias_score')

        # Make a new NewsSource object
        source = NewsSource(name=name, bias_score=bias)

        db.session.add(source) # Stage it for insertion
        db.session.commit() # Actually write to DB

        return jsonify({"message": "Source added!", "id": source.id}), 201
    
    @app.route('/add_headline', methods=['POST'])
    def add_headline():
        """
        Add a new headline.
        Expects JSON: {"source_id": 1, "title": "Some headline", "url": "https://..."}
        """
        data = request.get_json()
        s_id = data.get('source_id')
        title = data.get('title')
        url = data.get('url')

        headline = Headline(source_id=s_id, title=title, url=url)
        db.session.add(headline)
        db.session.commit()

        return jsonify({"message": "Headline added!", "id": headline.id}), 201


    @app.route('/headlines', methods=['GET'])
    def get_headlines():
        """
        Returns a list of headlines (optionally filtered by a bias range).
        Example query params:
        /headlines?min_bias=5&max_bias=5
        """

        # If no values provided, default to -10 / +10
        min_bias = int(request.args.get('min_bias', -10))
        max_bias = int(request.args.get('max_bias', 10))

        # Query all headlines joined with their news source
        # then filter by the source's bias_score
        query = db.session.query(Headline, NewsSource).join(NewsSource).filter(
            NewsSource.bias_score >= min_bias,
            NewsSource.bias_score <= max_bias
        )

        results = []

        for headline, source in query.all():
            results.append({
                "id":  headline.id,
                "title": headline.title,
                "url": headline.url,
                "source_name": source.name,
                "bias_score": source.bias_score
            })

        return jsonify(results)
    return app

app = create_app() # Expose app at Module level for Render/Gunicorn

# This runs the Flask app if we do "python app.py"
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port) # for Render deployment



    