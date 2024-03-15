import pandas as pd
from flask import Flask, render_template, request, jsonify

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///searches.db'

db = SQLAlchemy(app)

# Parameters and file names
DATA_FILE = "xlsx/CarsData.xlsx"
TEMPLATE_FOLDER = "templates"

# Loading the Excel data
df = pd.read_excel(DATA_FILE)


# Modèle de données pour stocker les recherches des utilisateurs
class Search(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(100), nullable=False)
    car_type = db.Column(db.String(50))


def get_initial_recommendations(car_type=None):
    """Generates a diversified set of car recommendations from different types."""
    recommended_cars = []
    if car_type:
        # Filter cars by the specified type
        filtered_cars = df[df['Type'] == car_type]
        if not filtered_cars.empty:
            recommended_car = filtered_cars.sample(1)
            recommended_cars.append(recommended_car.to_dict('records')[0])
    else:
        # If no type is specified, generate recommendations from different types
        for car_type in df['Type'].unique():
            filtered_cars = df[df['Type'] == car_type]
            if not filtered_cars.empty:
                recommended_car = filtered_cars.sample(1)
                recommended_cars.append(recommended_car.to_dict('records')[0])
    return recommended_cars


@app.route("/home")
@app.route("/")
def home():
    recommended_cars = get_initial_recommendations()
    # Checking for the existence of recommendations before passing to the template:
    if not recommended_cars:
        message = "No car data available for recommendations."
    else:
        message = ""  # Clearing the previous search message for the homepage
    return render_template("index.html", recommended_cars=recommended_cars, message=message)


@app.route("/search/")
def search():
    query = request.args.get('q', '')
    car_type = query.split()[-1] if query.split()[-1] in df['Type'].unique() else None

    # Filtrer les voitures dans la base de données
    filtered_df = df[df['Make'].str.contains(query, case=False, na=False) |
                     df['Model'].str.contains(query, case=False, na=False) |
                     df['Type'].str.contains(query, case=False, na=False)]

    # Enregistrer la recherche dans la base de données
    new_search = Search(query=query, car_type=car_type)
    db.session.add(new_search)
    db.session.commit()

    # Obtenir les recommandations basées sur le type de voiture recherché
    recommended_cars = get_initial_recommendations(car_type)

    # Filtrer les recommandations pour correspondre au type de voiture recherché
    if car_type:
        recommended_cars = [car for car in recommended_cars if car['Type'] == car_type]

    # Requête pour obtenir les types de voiture basés sur les recherches précédentes
    previous_searches = db.session.query(Search.car_type).distinct().all()

    return render_template("index.html", cars=filtered_df.to_dict('records'), query=query,
                           recommended_cars=recommended_cars, previous_searches=previous_searches)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Créer la structure de la base de données si elle n'existe pas
    app.run(debug=True)
