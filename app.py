# app.py

from flask import Flask, jsonify, request
from models import db, NewsSource, Headline

def create_app():
    # Create a Flask instance
    app = Flask(__name__)

    # Configure the database URI:
    # For quick demos, use an SQLite file called "news.db" in this folder.
    # You can switch to PostgreSQL/MySQL by changing this line.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'

    # Disable event system overhead
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize SQLAlchemy with our app configuration
    db.init_app(app)

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    @app.route('/add_source', methods=['POST'])
    def add_source():
        """
        Add a new news source with a given bias score.
        Expects a JSON payload, e.g.:
        {
            "name": "CNN",
            "bias_score": -5
        }
        """
        data = request.get_json()       # Parse JSON request body
        name = data.get('name')        # Extract "name" field from JSON
        bias_score = data.get('bias_score')  # Extract "bias_score" field

        # Create a new NewsSource object
        new_source = NewsSource(name=name, bias_score=bias_score)
        # Add it to the database session
        db.session.add(new_source)
        # Commit changes (inserts the row into the "news_sources" table)
        db.session.commit()

        # Return a message including the ID of the newly inserted source
        return jsonify({"message": f"Source '{name}' added.", "id": new_source.id}), 201

    @app.route('/add_headline', methods=['POST'])
    def add_headline():
        """
        Add a new headline. Expects JSON:
        {
            "source_id": 1,
            "title": "Breaking News",
            "url": "https://cnn.com/breaking"
        }
        """
        data = request.get_json()
        source_id = data.get('source_id')
        title = data.get('title')
        url = data.get('url')

        # Create a new Headline object
        new_headline = Headline(source_id=source_id, title=title, url=url)
        db.session.add(new_headline)
        db.session.commit()

        return jsonify({"message": "Headline added.", "id": new_headline.id}), 201

    @app.route('/headlines', methods=['GET'])
    def get_headlines():
        """
        Returns all headlines, or can filter by bias range if provided via query params, e.g.:
        /headlines?min_bias=-5&max_bias=5
        """
        # Use the provided query params or default to -10 / +10
        min_bias = request.args.get('min_bias', -10, type=int)
        max_bias = request.args.get('max_bias', 10, type=int)

        # Query the Headline table, joined with the NewsSource table
        # to filter by the source's bias score
        query = db.session.query(Headline, NewsSource).join(NewsSource).filter(
            NewsSource.bias_score >= min_bias,
            NewsSource.bias_score <= max_bias
        )

        # Collect the results into a list of dictionaries
        results = []
        for headline, source in query.all():
            results.append({
                "id": headline.id,
                "title": headline.title,
                "url": headline.url,
                "source": source.name,         # The name of the news source
                "bias_score": source.bias_score
            })

        # Return the list as JSON
        return jsonify(results)

    return app

# Only run the Flask server if this file is executed directly (e.g. "python app.py")
if __name__ == "__main__":
    # Call create_app(), then run the app in debug mode on localhost:5000
    app = create_app()
    app.run(debug=True)
