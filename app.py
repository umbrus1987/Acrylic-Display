import matplotlib
matplotlib.use('Agg') # Исправление для отображения картинок
import streamlit as st
import ezdxf
import io
import math
import matplotlib.pyplot as plt
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
import matplotlib.path as mpath
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

# --- Вспомогательные функции ---
def add_holes(msp, start_x, start_y, width, height, is_wide, is_high, is_bottom_part, bottom_offset=8.0):
    r = 1.25
    # Основные 4 угла
    holes = [
        (start_x + 6, start_y + bottom_offset), 
        (start_x + width - 6, start_y + bottom_offset), 
        (start_x + width - 6, start_y + height - 6), 
        (start_x + 6, start_y + height - 6)
    ]
    for h in holes: 
        msp.add_circle(h, radius=r)
        
    if is_wide:
        # Оставляем ТОЛЬКО верхнее центральное отверстие для широких деталей
        msp.add_circle((start_x + width/2, start_y + height - 6), radius=r)
        
        # Убираем нижнее центральное отверстие, если вы его там не хотите
        # Если оно нужно ТОЛЬКО на основании (Base/Detail 3), оставьте проверку:
        if is_bottom_part: 
            msp.add_circle((start_x + width/2, start_y + bottom_offset), radius=r)
            
    if is_high:
        msp.add_circle((start_x + 6, start_y + height/2), radius=r)
        msp.add_circle((start_x + width - 6, start_y + height/2), radius=r)

def draw_detail_1(msp, start_x, start_y, width, height, thickness):
    t = thickness
    w_base, h_base = width - 2*t, height - t
    w3, h3 = w_base / 3, h_base / 3
    sx, sy = start_x + t, start_y
    
    # Сдвиг низа паза на +1 мм, а верха на +2 мм (удлинение паза на 1 мм)
    shift_bottom = 1.0
    shift_top = 2.0
    ext = 1.0 
    
    pts = [
        (sx, sy), 
        (sx + w_base, sy), 
        
        # Правый вертикальный паз:
        (sx + w_base, sy + h3 + shift_bottom),
        (sx + w_base + t, sy + h3 + shift_bottom),
        (sx + w_base + t, sy + 2*h3 + shift_top),
        (sx + w_base, sy + 2*h3 + shift_top),
        
        (sx + w_base, sy + h_base), 
        
        # Верхний горизонтальный шип (сохранен с ext=1.0):
        (sx + 2*w3 + ext, sy + h_base),      
        (sx + 2*w3 + ext, sy + h_base + t),  
        (sx + w3 - ext, sy + h_base + t),    
        (sx + w3 - ext, sy + h_base),        
        
        (sx, sy + h_base), 
        
        # Левый вертикальный паз:
        (sx, sy + 2*h3 + shift_top),
        (sx - t, sy + 2*h3 + shift_top),
        (sx - t, sy + h3 + shift_bottom),
        (sx, sy + h3 + shift_bottom), 
        
        (sx, sy)
    ]
    msp.add_lwpolyline(pts, close=True)
    add_holes(msp, start_x, start_y, width, height, width >= 150, height >= 150, False, bottom_offset=8.0)

def draw_detail_2(msp, start_x, start_y, width, height, thickness):
    t = thickness
    h_base = height - t
    pts = [(start_x, start_y), (start_x + width, start_y), (start_x + width, start_y + height/3), (start_x + width - t, start_y + height/3), (start_x + width - t, start_y + 2*height/3), (start_x + width, start_y + 2*height/3), (start_x + width, start_y + h_base), (start_x + 2*width/3, start_y + h_base), (start_x + 2*width/3, start_y + h_base + t), (start_x + width/3, start_y + h_base + t), (start_x + width/3, start_y + h_base), (start_x, start_y + h_base), (start_x, start_y + 2*height/3), (start_x + t, start_y + 2*height/3), (start_x + t, start_y + height/3), (start_x, start_y + height/3), (start_x, start_y)]
    msp.add_lwpolyline(pts, close=True)
    add_holes(msp, start_x, start_y, width, height, width >= 150, height >= 150, False, bottom_offset=8.0)

def draw_detail_3(msp, start_x, start_y, width, height, thickness):
    t = thickness
    w3, h3 = width / 3, height / 3
    pts = [(start_x + w3, start_y), (start_x + w3, start_y + t), (start_x + 2*w3, start_y + t), (start_x + 2*w3, start_y), (start_x + width, start_y), (start_x + width, start_y + h3), (start_x + width - t, start_y + h3), (start_x + width - t, start_y + 2*h3), (start_x + width, start_y + 2*h3), (start_x + width, start_y + height), (start_x + 2*w3, start_y + height), (start_x + 2*w3, start_y + height - t), (start_x + w3, start_y + height - t), (start_x + w3, start_y + height), (start_x, start_y + height), (start_x, start_y + 2*h3), (start_x + t, start_y + 2*h3), (start_x + t, start_y + h3), (start_x, start_y + h3), (start_x, start_y)]
    msp.add_lwpolyline(pts, close=True)
    add_holes(msp, start_x, start_y, width, height, width >= 150, height >= 150, True)

def draw_trapezoid_plate(msp, center_x, center_y, w_top, w_bot, height, radius, text, font):
    # Инициализируем pts в самом начале, чтобы избежать UnboundLocalError
    pts = []
    
    r, h = radius, height
    hw_t, hw_b = w_top / 2, w_bot / 2
    
    def get_arc_points(cx, cy, start_angle, end_angle, radius, steps=8):
        arc_pts = []
        for i in range(steps + 1):
            angle = math.radians(start_angle + (end_angle - start_angle) * i / steps)
            arc_pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        return arc_pts
    
    # Добавляем дуги по углам в список pts
    pts.extend(get_arc_points(center_x + hw_t - r, center_y + h/2 - r, 0, 90, r))
    pts.extend(get_arc_points(center_x - hw_t + r, center_y + h/2 - r, 90, 180, r))
    pts.extend(get_arc_points(center_x - hw_b + r, center_y - h/2 + r, 180, 270, r))
    pts.extend(get_arc_points(center_x + hw_b - r, center_y - h/2 + r, 270, 360, r))
    
    # Рисуем контур трапеции (цвет 7 - черный)
    msp.add_lwpolyline(pts, close=True, dxfattribs={'color': 7})
    
    # ВЕКТОРИЗАЦИЯ ТЕКСТА
    if text:
        font_map = {"STANDARD": "sans-serif", "TXT": "monospace", "ROMANS": "serif", "ITALIC": "serif"}
        family = font_map.get(font, "sans-serif")
        
        fp = FontProperties(family=family, weight='bold')
        tp = TextPath((0, 0), text, size=height*0.4, prop=fp)
        
        bbox = tp.get_extents()
        dx = -(bbox.x0 + bbox.x1) / 2 + center_x
        dy = -(bbox.y0 + bbox.y1) / 2 + center_y
        
        # Рисуем буквы (цвет 92 - зеленый для LightBurn C04)
        for path_data in tp.to_polygons():
            text_pts = [(p[0] + dx, p[1] + dy) for p in path_data]
            msp.add_lwpolyline(text_pts, close=True, dxfattribs={'color': 92})

def show_preview(w_top, w_bot, height, text, font_name):
    plt.close('all') # Очистка перед отрисовкой
    fig, ax = plt.subplots(figsize=(5, 1.5))
    pts = [(-w_top/2, height/2), (w_top/2, height/2), (w_bot/2, -height/2), (-w_bot/2, -height/2), (-w_top/2, height/2)]
    x, y = zip(*pts)
    ax.plot(x, y, 'g-')
    
    # Сопоставляем имена шрифтов AutoCAD с системными шрифтами
    font_map = {
        "STANDARD": "sans-serif",
        "TXT": "monospace",
        "ROMANS": "serif",
        "ITALIC": "serif"
    }
    family = font_map.get(font_name, "sans-serif")
    style = "italic" if font_name == "ITALIC" else "normal"
    
    ax.text(0, 0, text, ha='center', va='center', fontsize=14, 
            fontweight='bold', fontfamily=family, fontstyle=style)
    
    ax.set_aspect('equal')
    ax.axis('off')
    st.pyplot(fig)

def get_dxf_bytes(w1, y2, z, thickness):
    doc = ezdxf.new('R2010')
    doc.units = units.MM
    msp = doc.modelspace()
    gap = 3
    draw_detail_1(msp, 0, 0, w1, z, thickness)
    draw_detail_1(msp, w1 + gap, 0, w1, z, thickness)
    draw_detail_2(msp, 0, z + gap, y2, z, thickness)
    draw_detail_2(msp, y2 + gap, z + gap, y2, z, thickness)
    draw_detail_3(msp, 0, z + gap + z + gap, w1, y2, thickness)
    stream = io.StringIO()
    doc.write(stream)
    return io.BytesIO(stream.getvalue().encode('utf-8'))

def get_base_dxf_bytes(w, y, include_name_plate):
    doc = ezdxf.new('R2010')
    doc.units = units.MM
    msp = doc.modelspace()
    
    # 1. Синий контур: (w+1) x (y+1)
    w1, h1 = w + 1, y + 1
    hw1, hh1 = w1 / 2, h1 / 2
    msp.add_lwpolyline([(-hw1, -hh1), (hw1, -hh1), (hw1, hh1), (-hw1, hh1)], close=True, dxfattribs={'color': 5})
    
    # 2. Красный контур: +20 мм к синему
    w2, h2 = w1 + 20, h1 + 20
    hw2, hh2 = w2 / 2, h2 / 2
    # Нижняя линия красного прямоугольника находится на уровне Y = -hh2
    red_bottom_y = -hh2 
    msp.add_lwpolyline([(-hw2, -hh2), (hw2, -hh2), (hw2, hh2), (-hw2, hh2)], close=True, dxfattribs={'color': 1})
    
    # 3. Зеленая линия со скошенными краями (ушки направлены вниз)
    # Горизонтальный отрезок на уровне red_bottom_y, ушки уходят вниз
    line_w = w 
    half_line_w = line_w / 2
    bevel = 7 # Длина скоса
    
    pts_green = [
        (-half_line_w - bevel, red_bottom_y - bevel), # Левый конец скоса (вниз)
        (-half_line_w, red_bottom_y),                # Левая точка горизонтали
        (half_line_w, red_bottom_y),                 # Правая точка горизонтали
        (half_line_w + bevel, red_bottom_y - bevel)  # Правый конец скоса (вниз)
    ]
    msp.add_lwpolyline(pts_green, close=False, dxfattribs={'color': 3})
    
    # ... (далее ваш код для Name Plate)
    
    if include_name_plate:
        y_pos = -(y + 20) / 2
        msp.add_lwpolyline([(-45-7, y_pos-7), (-45, y_pos), (45, y_pos), (45+7, y_pos-7)], close=False, dxfattribs={'color': 3})
    
    stream = io.StringIO()
    doc.write(stream)
    return io.BytesIO(stream.getvalue().encode('utf-8'))

# --- UI ---
st.title("Acrylic Display Generator")
st.markdown("""
    <style>
    /* Оставляем обычные кнопки (Generate) в покое */
    /* div.stButton > button не трогаем */
    
    /* Стили только для кнопок скачивания (Download) */
    div.stDownloadButton > button {
        background-color: #FF4B4B !important;
        color: white !important;
        border: 1px solid #FF4B4B !important;
    }
    
    /* Эффект при наведении на кнопку скачивания */
    div.stDownloadButton > button:hover {
        background-color: #FF2B2B !important;
        color: white !important;
        border: 1px solid #FF2B2B !important;
    }
    </style>
""", unsafe_allow_html=True)
col1, col2 = st.columns([1, 1])
with col1:
    st.image("Picture.png", use_container_width=True)
with col2:
    width_x = st.number_input("Ширина (X)", 50, 800
, 150)
    depth_y = st.number_input("Глубина (Y)", 50, 800, 100)
    height_z = st.number_input("Высота (Z)", 50, 800, 100)
    if st.button("Generate Main"):
        st.session_state['dxf_data'] = get_dxf_bytes(width_x, depth_y, height_z, 3.0)
        # Имя файла: Main_X x Y x Z
        st.session_state['main_file_name'] = f"Main_{width_x}x{depth_y}x{height_z}.dxf"
    
    if 'dxf_data' in st.session_state:
        st.download_button(
            label="Скачать Main DXF", 
            data=st.session_state['dxf_data'], 
            file_name=st.session_state.get('main_file_name', 'Main.dxf')
        )
    st.divider()
    st.checkbox("Name Plate", key='name_plate_val')
    if st.button("Generate Base"):
        include_plate = st.session_state.get('name_plate_val', False)
        st.session_state['base_dxf'] = get_base_dxf_bytes(width_x, depth_y, include_plate)
        # Имя файла: Base_X x Y
        st.session_state['base_file_name'] = f"Base_{width_x}x{depth_y}.dxf"
    
    if 'base_dxf' in st.session_state:
        st.download_button(
            label="Скачать Base DXF", 
            data=st.session_state['base_dxf'], 
            file_name=st.session_state.get('base_file_name', 'Base.dxf')
        )

if st.session_state.get('name_plate_val', False):
    st.subheader("Name Plate Settings")
    plate_text = st.text_input("Текст (max 16)", max_chars=16)
    plate_font = st.selectbox("Шрифт", ["STANDARD", "ROMANS", "ITALIC"])
    if plate_text:
        # Передаем font_name в функцию
        show_preview(91, 87, 13, plate_text, plate_font)
    if st.button("Generate Name Plate File"):
        doc = ezdxf.new('R2010')
        doc.units = units.MM
        draw_trapezoid_plate(doc.modelspace(), 0, 0, 91, 87, 13, 2, plate_text, plate_font)
        
        stream = io.StringIO()
        doc.write(stream)
        st.session_state['plate_dxf'] = io.BytesIO(stream.getvalue().encode('utf-8'))
        
        # Имя файла: Plate_Текст
        clean_text = "".join([c for c in plate_text if c.isalnum() or c in (' ', '_')]).strip()
        st.session_state['plate_file_name'] = f"Plate_{clean_text if clean_text else 'Custom'}.dxf"
        
    if 'plate_dxf' in st.session_state:
        st.download_button(
            label="Скачать Plate DXF", 
            data=st.session_state['plate_dxf'], 
            file_name=st.session_state.get('plate_file_name', 'Plate.dxf')
        )
