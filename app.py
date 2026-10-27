"""Entry point aplikasi Streamlit Smart Parking.

Jalankan dengan salah satu cara:

    python app.py                  # tanpa uv, cukup `pip install -r requirements.txt`
    streamlit run app.py
    uv run streamlit run app.py

Harus berada di root project: `streamlit run` menaruh direktori skrip di
sys.path, jadi skrip yang ditaruh langsung di views/ tidak bisa mengimpor core.
"""

import sys
from pathlib import Path

from streamlit.runtime.scriptrunner import get_script_run_ctx


def _jalankan_lewat_streamlit() -> int:
    """Luncurkan ulang file ini di bawah `streamlit run`.

    Dipakai saat file dijalankan sebagai `python app.py`. Tanpa ini Streamlit
    tidak punya ScriptRunContext, jadi tidak ada server yang jalan dan setiap
    pemanggilan st.* hanya memunculkan peringatan "missing ScriptRunContext".
    """
    from streamlit.web import cli as streamlit_cli

    sys.argv = ["streamlit", "run", str(Path(__file__).resolve()), *sys.argv[1:]]
    return streamlit_cli.main()


# suppress_warning=True: di jalur `python app.py` ctx memang belum ada, dan
# peringatannya cuma membingungkan karena detik berikutnya kita relaunch.
if get_script_run_ctx(suppress_warning=True) is None:
    sys.exit(_jalankan_lewat_streamlit())

from views.parking_ui import main  # noqa: E402  (impor setelah guard relaunch)

main()
