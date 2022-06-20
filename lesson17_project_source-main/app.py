from flask import Flask, request, jsonify
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RESTX_JSON'] = {'ensure_ascii': False, 'indent': 3}
db = SQLAlchemy(app)


class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")


class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class MovieSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    year = fields.Int()
    rating = fields.Float()
    genre_id = fields.Int()
    director_id = fields.Int()


class DirectorSchema(Schema):
    id = fields.Int()
    name = fields.Str()


class GenreSchema(Schema):
    id = fields.Int()
    name = fields.Str()


movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)

director_schema = DirectorSchema()
directors_schema = DirectorSchema(many=True)

genre_schema = GenreSchema()
genres_schema = GenreSchema(many=True)

api = Api(app)
movie_ns = api.namespace('movies')
director_ns = api.namespace('directors')
genre_ns = api.namespace('genres')


@movie_ns.route('/')
class MovieView(Resource):
    def get(self):
        get_movies = db.session.query(Movie.id, Movie.title, Movie.description, Movie.rating, Movie.trailer,
                                      Genre.name.label('genre'),
                                      Director.name.label('director')).join(Genre).join(Director)
        d_id = request.args.get('director_id')
        g_id = request.args.get('genre_id')
        if d_id:
            get_movies = get_movies.filter(Movie.director_id == d_id)
        if g_id:
            get_movies = get_movies.filter(Movie.genre_id == g_id)

        all_movies = get_movies.all()
        return movies_schema.dumps(all_movies), 200

    def post(self):
        req_json = request.json
        new_movie = Movie(**req_json)
        with db.session.begin():
            db.session.add(new_movie)
        return "Новый объект создан", 201


@movie_ns.route('/<int:pk>')
class MovieView(Resource):
    def get(self, pk: int):
        movie_pk = db.session.query(Movie.id, Movie.title, Movie.description, Movie.rating,
                                    Movie.trailer,
                                    Genre.name.label('genre'),
                                    Director.name.label('director')).join(Genre).join(Director).filter(
            Movie.id == pk).first()
        if movie_pk:
            return movie_schema.dump(movie_pk), 200
        return "Запрос не найден", 404

    def put(self, pk: int):
        movie = db.session.query(Movie).get(pk)
        if not movie:
            return "Запрос не найден", 404
        req_json = request.json

        movie.title = req_json["title"],
        movie.description = req_json["description"],
        movie.trailer = req_json["trailer"],
        movie.year = req_json["year"],
        movie.rating = req_json["rating"],
        movie.genre_id = req_json["genre_id"],
        movie.director_id = req_json["director_id"]
        db.session.add(movie)
        db.session.commit()
        return "", 204

    def delete(self, pk: int):
        movie = db.session.query(Movie).get(pk)
        if not movie:
            return "Запрос не найден", 404
        db.session.delete(movie)
        db.session.commit()
        return "", 204


@director_ns.route('/')
class DirectorView(Resource):
    def get(self):
        all_directors = Director.query.all()
        return directors_schema.dump(all_directors) , 200

    def post(self):
        req_json = request.json
        new_director = Director(**req_json)
        with db.session.begin():
            db.session.add(new_director)
        return "Новый объект создан", 201


@director_ns.route('/<int:director_id>')
class DirectorView(Resource):
    def get(self, director_id: int):
        director = Director.query.get(director_id)
        if director_id:
            return director_schema.dump(director), 200
        return "Запрос не найден", 404

    def delete(self, director_id: int):
        director = db.session.query(Director).get(director_id)
        if not director:
            return "Запрос не найден", 404
        db.session.delete(director)
        db.session.commit()
        return "", 204


@genre_ns.route('/')
class GenreView(Resource):
    def get(self):
        all_genres = Genre.query.all()
        return genres_schema.dump(all_genres) , 200

    def post(self):
        req_json = request.json
        new_genres = Genre(**req_json)
        with db.session.begin():
            db.session.add(new_genres)
        return "Новый объект создан", 201


@genre_ns.route('/<int:genre_id>')
class GenreView(Resource):
    def get(self, genre_id: int):
        genre = Genre.query.get(genre_id)
        if genre_id:
            return genres_schema.dump(genre), 200
        return "Запрос не найден", 404

    def delete(self, genre_id: int):
        genre = db.session.query(Genre).get(genre_id)
        if not genre:
            return "Запрос не найден", 404
        db.session.delete(genre)
        db.session.commit()
        return "", 204

if __name__ == '__main__':
    app.run(debug=True)
