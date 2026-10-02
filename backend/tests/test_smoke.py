def test_app_metadata():
    from main import app

    assert app.title == "Indian Stock Market Finance API"
    assert app.version == "1.0.0"
