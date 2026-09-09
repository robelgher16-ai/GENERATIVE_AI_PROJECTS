from app_local import Movie


def test_movie_model():

    movie = Movie(
        title="Inception",
        release_year=2010,
        genre=[
            "Science Fiction",
            "Action"
        ],
        director="Christopher Nolan",
        cast=[
            "Leonardo DiCaprio",
            "Tom Hardy"
        ],
        rating=8.8,
        summery="A thief enters people's dreams."
    )

    assert movie.title == "Inception"

    assert movie.release_year == 2010

    assert movie.director == "Christopher Nolan"

    assert movie.rating == 8.8

    assert len(movie.cast) == 2

    assert len(movie.genre) == 2