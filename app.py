"""Entry point aplikasi Streamlit Smart Parking.

Jalankan dengan: uv run streamlit run app.py

Harus berada di root project: `streamlit run` menaruh direktori skrip di
sys.path, jadi skrip yang ditaruh langsung di views/ tidak bisa mengimpor core.
"""

from views.parking_ui import main

main()
