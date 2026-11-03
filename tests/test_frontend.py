from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_demo_and_method_render():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "frontend/app.py"))
    app.run(timeout=30)
    assert not app.exception
    app.toggle[0].set_value(True).run()
    assert "Python" in app.text_area[0].value
    assert not app.exception
    app.sidebar.radio[0].set_value("Comprendre la méthode").run()
    assert not app.exception
    assert "Un score" in app.title[0].value

