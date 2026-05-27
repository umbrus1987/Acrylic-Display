import streamlit as st
import ezdxf
import io
from ezdxf import units

# --- Вспомогательные функции ---
def add_holes(msp, start_x, start_y, width, height, is_wide, is_high, is_bottom_part):
    r = 1.25
    holes = [
        (start_x + 6, start_y + 6), (start_x + width - 6, start_y + 6), 
        (start_x + width - 6, start_y + height - 6), (start_x + 6, start_y + height - 6)
    ]
    for h in holes: msp.add_circle(h, radius=r)
    
    if is_wide:
        msp.add_circle((start_x + width/2, start_y + height - 6), radius=r)
        if is_bottom_part:
            msp.add_circle((start_x + width/2, start_y + 6), radius=r)
            
    if is_high:
        msp.add_circle((start_x + 6, start_y + height/2), radius=r)
        msp.add_circle((start_x + width - 6, start_y + height/2), radius=r)

# --- Функции отрисовки деталей ---
def draw_detail_1(msp, start_x, start_y, width, height, thickness):
    t = thickness
    w_base, h_base = width - 2*t, height - t
    w3, h3 = w_base / 3, h_base / 3
    sx, sy = start_x + t, start_y
    pts = [(sx, sy), (sx + w_base, sy), (sx + w_base, sy + h3), (sx + w_base + t, sy + h3), (sx + w_base + t, sy + 2*h3), (sx + w_base, sy + 2*h3), (sx + w_base, sy + h_base), (sx + 2*w3, sy + h_base), (sx + 2*w3, sy + h_base + t), (sx + w3, sy + h_base + t), (sx + w3, sy + h_base), (sx, sy + h_base), (sx, sy + 2*h3), (sx - t, sy + 2*h3), (sx - t, sy + h3), (sx, sy + h3), (sx, sy)]
    msp.add_lwpolyline(pts, close=True)
    add_holes(msp, start_x, start_y, width, height, width >= 150, height >= 150, False)

def draw_detail_2(msp, start_x, start_y, width, height, thickness):
    t = thickness
    h_base = height - t
    pts = [(start_x, start_y), (start_x + width, start_y), (start_x + width, start_y + height/3), (start_x + width - t, start_y + height/3), (start_x + width - t, start_y + 2*height/3), (start_x + width, start_y + 2*height/3), (start_x + width, start_y + h_base), (start_x + 2*width/3, start_y + h_base), (start_x + 2*width/3, start_y + h_base + t), (start_x + width/3, start_y + h_base + t), (start_x + width/3, start_y + h_base), (start_x, start_y + h_base), (start_x, start_y + 2*height/3), (start_x + t, start_y + 2*height/3), (start_x + t, start_y + height/3), (start_x, start_y + height/3), (start_x, start_y)]
    msp.add_lwpolyline(pts, close=True)
    add_holes(msp, start_x, start_y, width, height, width >= 150, height >= 150, False)

def draw_detail_3(msp, start_x, start_y, width, height, thickness):
    t = thickness
    w3, h3 = width / 3, height / 3
    pts = [(start_x + w3, start_y), (start_x + w3, start_y + t), (start_x + 2*w3, start_y + t), (start_x + 2*w3, start_y), (start_x + width, start_y), (start_x + width, start_y + h3), (start_x + width - t, start_y + h3), (start_x + width - t, start_y + 2*h3), (start_x + width, start_y + 2*h3), (start_x + width, start_y + height), (start_x + 2*w3, start_y + height), (start_x + 2*w3, start_y + height - t), (start_x + w3, start_y + height - t), (start_x + w3, start_y + height), (start_x, start_y + height), (start_x, start_y + 2*h3), (start_x + t, start_y + 2*h3), (start_x + t, start_y + h3), (start_x, start_y + h3), (start_x, start_y)]
    msp.add_lwpolyline(pts, close=True)
    add_holes(msp, start_x, start_y, width, height, width >= 150, height >= 150, True)

# --- Генерация ---
def get_dxf_bytes(w1, y2, z, thickness):
    doc = ezdxf.new('R2010')
    doc.units = units.MM
    msp = doc.modelspace()
    
    gap = 3 # Технологический зазор 3 мм
    
    # Расстановка деталей (2x Деталь 1, 2x Деталь 2, 1x Деталь 3)
    draw_detail_1(msp, 0, 0, w1, z, thickness)
    draw_detail_1(msp, w1 + gap, 0, w1, z, thickness)
    
    draw_detail_2(msp, 0, z + gap, y2, z, thickness)
    draw_detail_2(msp, y2 + gap, z + gap, y2, z, thickness)
    
    draw_detail_3(msp, 0, z + gap + z + gap, w1, y2, thickness)
    
    stream = io.StringIO()
    doc.write(stream)
    bytes_stream = io.BytesIO(stream.getvalue().encode('utf-8'))
    bytes_stream.seek(0)
    return bytes_stream

# --- Интерфейс ---
st.title("Acrylic Display generator")

# Стилизация кнопки (Красный цвет)
st.markdown("""
    <style>
    div.stDownloadButton > button:first-child {
        background-color: #FF4B4B;
        color: white;
        border: none;
        width: 100%;
    }
    div.stButton > button:first-child {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.image("Picture.png", use_container_width=True)

with col2:
    width_x = st.number_input("Ширина (X)", value=150.0)
    depth_y = st.number_input("Глубина (Y)", value=100.0)
    height_z = st.number_input("Высота (Z)", value=80.0)

    # Кнопка генерации
    if st.button("Generate"):
        st.session_state['dxf_data'] = get_dxf_bytes(width_x, depth_y, height_z, 3.0)
        st.session_state['file_name'] = f"{int(width_x)}x{int(depth_y)}x{int(height_z)}.dxf"

    # Кнопка скачивания появится СРАЗУ ПОД кнопкой Generate, если данные созданы
    if 'dxf_data' in st.session_state:
        st.download_button(
            label="Скачать DXF",
            data=st.session_state['dxf_data'],
            file_name=st.session_state['file_name'],
            mime="application/dxf"
        )