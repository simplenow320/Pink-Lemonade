from app import create_app
def test_brand_tokens_present():
    app = create_app()
    client = app.test_client()
    res = client.get('/static/css/brand.css')
    css = res.get_data(as_text=True)
    assert "#F8D7DA" in css and "--radius" in css

def test_nav_renders():
    app = create_app()
    client = app.test_client()
    res = client.get('/')
    html = res.get_data(as_text=True)
    assert 'role="navigation"' in html and 'Find funding now' in html