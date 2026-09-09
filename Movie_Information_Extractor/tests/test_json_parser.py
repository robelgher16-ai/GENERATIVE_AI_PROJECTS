from app_local import extract_json_object


def test_valid_json():

    response = """
    {
        "title": "Inception",
        "release_year": 2010,
        "genre": ["Science Fiction", "Action"],
        "director": "Christopher Nolan",
        "cast": ["Leonardo DiCaprio"],
        "rating": 8.8,
        "summery": "A thief enters dreams."
    }
    """

    result = extract_json_object(response)

    assert result is not None

    assert result["title"] == "Inception"

    assert result["release_year"] == 2010


def test_json_with_markdown():

    response = """
    ```json
    {
        "title": "Inception",
        "release_year": 2010
    }
    ```
    """

    result = extract_json_object(response)

    assert result is not None

    assert result["title"] == "Inception"


def test_invalid_response():

    response = """
    This is not JSON.
    """

    result = extract_json_object(response)

    assert result is None