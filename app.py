import matplotlib
matplotlib.use('Agg') # Исправление для отображения картинок
import streamlit as st
import ezdxf
import io
import math
import os
import urllib.request
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from ezdxf import units
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

# --- Настройка Google Fonts ---
GOOGLE_FONTS = {
    "Girassol": "https://github.com/google/fonts/raw/main/ofl/girassol/Girassol-Regular.ttf",
    "Pirata One": "https://github.com/google/fonts/raw/main/ofl/pirataone/PirataOne-Regular.ttf",
    "Bigshot One": "https://github.com/google/fonts/raw/main/ofl/bigshotone/BigshotOne-Regular.ttf"
}

def get_google_font_prop(font_name):
    filename = f"{font_name.replace(' ', '')}-Regular.ttf"
    if not os.path.exists(filename):
        try:
            url = GOOGLE_FONTS.get(font_name)
            if url:
                urllib.request.urlretrieve(url, filename)
        except Exception:
            pass
            
    if os.path.exists(filename):
        fm.fontManager.addfont(filename)
        return fm.FontProperties(fname=filename)
    
    return fm.FontProperties(weight='bold')

def get_adaptive_font_size(text, base_height, font_name, max_allowed_width=46.0):
    if not text:
        return base_height * 0.7
    
    font_size = base_height * 0.7
    
    try:
        fp = get_google_font_prop(font_name)
        tp = TextPath((0, 0), text, size=font_size, prop=fp)
        bbox = tp.get_extents()
        current_width = bbox.x1 - bbox.x0
        
        if current_width > max_allowed_width:
            scale = max_allowed_width / current_width
            font_size *= scale
            
            min_limit = base_height * 0.3
            if font_size < min_limit:
                font_size = min_limit
    except Exception:
        pass
        
    return font_size

# --- Вспомогательные функции ---
def add_holes(msp, start_x, start_y, width, height, is_wide, is_high, is_bottom_part, thickness=3.0):
    r = 1.25
    corner_offset = 6.0 if thickness == 3.0 else 7.0
    bottom_offset = 6.0 if is_bottom_part else 8.0

    holes = [
        (start_x + corner_offset, start_y + bottom_offset), 
        (start_x + width - corner_offset, start_y + bottom_offset), 
        (start_x + width - corner_offset, start_y + height - corner_offset), 
        (start_x + corner_offset, start_y + height - corner_offset)
    ]
    for h in holes: 
        msp.add_circle(h, radius=r)
        
    if is_wide:
        msp.add_circle((start_x + width/2, start_y + height - corner_offset), radius=r)
        if is_bottom_part: 
            msp.add_circle((start_x + width/2, start_y + bottom_offset), radius=r)
            
    if is_high:
        msp.add_circle((start_x + corner_offset, start_y + height/2), radius=r)
        msp.add_circle((start_x + width - corner_offset, start_y + height/2), radius=r)

def draw_detail_1(msp, start_x, start_y, width, height, thickness, is_wide, is_high):
    t = thickness
    w_base, h_base = width - 2*t, height - t
    w3, h3 = w_base / 3, h_base / 3
    sx, sy = start_x + t, start_y
    
    shift_bottom = 1.0
    shift_top = 2.0
    ext = 1.0 
    
    pts = [
        (sx, sy), 
        (sx + w_base, sy), 
        (sx + w_base, sy + h3 + shift_bottom),
        (sx + w_base + t, sy + h3 + shift_bottom),
        (sx + w_base + t, sy + 2*h3 + shift_top),
        (sx + w_base, sy + 2*h3 + shift_top),
        (sx + w_base, sy + h_base), 
        (sx + 2*w3 + ext, sy + h_base),      
        (sx + 2*w3 + ext, sy + h_base + t),  
        (sx + w3 - ext, sy + h_base + t),    
        (sx + w3 - ext, sy + h_base),        
        (sx, sy + h_base), 
        (sx, sy + 2*h3 + shift_top),
        (sx - t, sy + 2*h3 + shift_top),
        (sx - t, sy + h3 + shift_bottom),
        (sx, sy + h3 + shift_bottom), 
        (sx, sy)
    ]
    msp.add_lwpolyline(pts, close=True)
    add_holes(msp, start_x, start_y, width, height, is_wide, is_high, False, thickness=thickness)

def draw_detail_2(msp, start_x, start_y, width, height, thickness, is_wide, is_high):
    t = thickness
    h_base = height - t
    pts = [
        (start_x, start_y), (start_x + width, start_y), 
        (start_x + width, start_y + height/3), (start_x + width - t, start_y + height/3), 
        (start_x + width - t, start_y + 2*height/3), (start_x + width, start_y + 2*height/3), 
        (start_x + width, start_y + h_base), (start_x + 2*width/3, start_y + h_base), 
        (start_x + 2*width/3, start_y + h_base + t), (start_x + width/3, start_y + h_base + t), 
        (start_x + width/3, start_y + h_base), (start_x, start_y + h_base), 
        (start_x, start_y + 2*height/3), (start_x + t, start_y + 2*height/3), 
        (start_x + t, start_y + height/3), (start_x, start_y + height/3), (start_x, start_y)
    ]
    msp.add_lwpolyline(pts, close=True)
    add_holes(msp, start_x, start_y, width, height, is_wide, is_high, False, thickness=thickness)

def draw_detail_3(msp, start_x, start_y, width, height, thickness, is_wide, is_high):
    t = thickness
    w3, h3 = width / 3, height / 3
    pts = [
        (start_x + w3, start_y), (start_x + w3, start_y + t), 
        (start_x + 2*w3, start_y + t), (start_x + 2*w3, start_y), 
        (start_x + width, start_y), (start_x + width, start_y + h3), 
        (start_x + width - t, start_y + h3), (start_x + width - t, start_y + 2*h3), 
        (start_x + width, start_y + 2*h3), (start_x + width, start_y + height), 
        (start_x + 2*w3, start_y + height), (start_x + 2*w3, start_y + height - t), 
        (start_x + w3, start_y + height - t), (start_x + w3, start_y + height), 
        (start_x, start_y + height), (start_x, start_y + 2*h3), 
        (start_x + t, start_y + 2*h3), (start_x + t, start_y + h3), 
        (start_x, start_y + h3), (start_x, start_y)
    ]
    msp.add_lwpolyline(pts, close=True)
    add_holes(msp, start_x, start_y, width, height, is_wide, is_high, True, thickness=thickness)

def draw_trapezoid_plate(msp, center_x, center_y, w_top, w_bot, height, radius, text, font_name, max_allowed_width):
    pts = []
    r, h = radius, height
    hw_t, hw_b = w_top / 2, w_bot / 2
    
    def get_arc_points(cx, cy, start_angle, end_angle, radius, steps=8):
        arc_pts = []
        for i in range(steps + 1):
            angle = math.radians(start_angle + (end_angle - start_angle) * i / steps)
            arc_pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        return arc_pts
    
    pts.extend(get_arc_points(center_x + hw_t - r, center_y + h/2 - r, 0, 90, r))
    pts.extend(get_arc_points(center_x - hw_t + r, center_y + h/2 - r, 90, 180, r))
    pts.extend(get_arc_points(center_x - hw_b + r, center_y - h/2 + r, 180, 270, r))
    pts.extend(get_arc_points(center_x + hw_b - r, center_y - h/2 + r, 270, 360, r))
    
    msp.add_lwpolyline(pts, close=True, dxfattribs={'color': 7})
    
    if text:
        fp = get_google_font_prop(font_name)
        font_size = get_adaptive_font_size(text, height, font_name, max_allowed_width)
        tp = TextPath((0, 0), text, size=font_size, prop=fp)
        
        bbox = tp.get_extents()
        dx = -(bbox.x0 + bbox.x1) / 2 + center_x
        dy = -(bbox.y0 + bbox.y1) / 2 + center_y
        
        for path_data in tp.to_polygons():
            text_pts = [(p[0] + dx, p[1] + dy) for p in path_data]
            msp.add_lwpolyline(text_pts, close=True, dxfattribs={'color': 92})

def get_dxf_bytes(w1, y2, z, thickness, is_w_large, is_y_large, is_z_large):
    doc = ezdxf.new('R2010')
    doc.units = units.MM
    msp = doc.modelspace()
    gap = 3
    draw_detail_1(msp, 0, 0, w1, z, thickness, is_w_large, is_z_large)
    draw_detail_1(msp, w1 + gap, 0, w1, z, thickness, is_w_large, is_z_large)
    draw_detail_2(msp, 0, z + gap, y2, z, thickness, is_y_large, is_z_large)
    draw_detail_2(msp, y2 + gap, z + gap, y2, z, thickness, is_y_large, is_z_large)
    draw_detail_3(msp, 0, z + gap + z + gap, w1, y2, thickness, is_w_large, is_y_large)
    stream = io.StringIO()
    doc.write(stream)
    return io.BytesIO(stream.getvalue().encode('utf-8'))

def get_base_dxf_bytes(w, y, thickness, inp_w):
    doc = ezdxf.new('R2010')
    doc.units = units.MM
    msp = doc.modelspace()
    
    extra_blue = 2.0
    extra_red = 20.0
    
    w1, h1 = w + extra_blue, y + extra_blue
    hw1, hh1 = w1 / 2, h1 / 2
    msp.add_lwpolyline([(-hw1, -hh1), (hw1, -hh1), (hw1, hh1), (-hw1, hh1)], close=True, dxfattribs={'color': 5})
    
    w2, h2 = w1 + extra_red, h1 + extra_red
    hw2, hh2 = w2 / 2, h2 / 2
    red_bottom_y = -hh2 
    msp.add_lwpolyline([(-hw2, -hh2), (hw2, -hh2), (hw2, hh2), (-hw2, hh2)], close=True, dxfattribs={'color': 1})
    
    fixed_line_w = 50.0 if inp_w <= 99 else 90.0
    half_line_w = fixed_line_w / 2
    bevel = 7
    
    pts_green = [
        (-half_line_w - bevel, red_bottom_y - bevel), 
        (-half_line_w, red_bottom_y),                
        (half_line_w, red_bottom_y),                 
        (half_line_w + bevel, red_bottom_y - bevel)  
    ]
    msp.add_lwpolyline(pts_green, close=False, dxfattribs={'color': 3})

    stream = io.StringIO()
    doc.write(stream)
    return io.BytesIO(stream.getvalue().encode('utf-8'))

def get_leather_dxf_bytes(w, y):
    doc = ezdxf.new('R2010')
    doc.units = units.MM
    msp = doc.modelspace()
    
    leather_w = w + 8.18
    leather_h = y + 8.18
    radius = 2.0
    hw, hh = leather_w / 2, leather_h / 2
    r = radius
    pts = []
    
    def get_arc_points(cx, cy, start_angle, end_angle, radius, steps=8):
        arc_pts = []
        for i in range(steps + 1):
            angle = math.radians(start_angle + (end_angle - start_angle) * i / steps)
            arc_pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        return arc_pts
        
    pts.extend(get_arc_points(hw - r, hh - r, 0, 90, r))
    pts.extend(get_arc_points(-hw + r, hh - r, 90, 180, r))
    pts.extend(get_arc_points(-hw + r, -hh + r, 180, 270, r))
    pts.extend(get_arc_points(hw - r, -hh + r, 270, 360, r))
    
    msp.add_lwpolyline(pts, close=True, dxfattribs={'color': 7})
    
    stream = io.StringIO()
    doc.write(stream)
    return io.BytesIO(stream.getvalue().encode('utf-8'))

def get_cardboard_box_dxf_bytes(w, y, h, cardboard_thick, fold_gap=9.0):
    doc = ezdxf.new('R2010')
    doc.units = units.MM
    msp = doc.modelspace()
    
    dimensions = sorted([w, y, h])
    dim1, dim2 = dimensions[1], dimensions[2]
    
    dim_x = max(dim1, dim2)
    dim_y = min(dim1, dim2)
    
    base_w = dim_x + 27.0
    base_y = dim_y + 27.0
    
    hw, hy = base_w / 2, base_y / 2
    half_gap = fold_gap / 2.0
    
    wall_h_y = 45.0 + 4.0 
    wall_h_x = 45.0 
    
    extra_flap_x = 50.0 
    total_offset_x = fold_gap + wall_h_x + fold_gap + extra_flap_x
    
    extra_flap_y = base_y / 2.0 
    total_offset_y = fold_gap + wall_h_y + fold_gap + extra_flap_y
    
    overlap = cardboard_thick 
    
    cross_pts = [
        (-hw - overlap, hy), (-hw - overlap, hy + total_offset_y),
        (hw + overlap, hy + total_offset_y), (hw + overlap, hy),
        (hw, hy), (hw + total_offset_x, hy), (hw + total_offset_x, -hy), (hw, -hy),
        (hw + overlap, -hy), (hw + overlap, -hy - total_offset_y),
        (-hw - overlap, -hy - total_offset_y), (-hw - overlap, -hy),
        (-hw, -hy), (-hw - total_offset_x, -hy), (-hw - total_offset_x, hy), (-hw, hy)
    ]
    msp.add_lwpolyline(cross_pts, close=True, dxfattribs={'color': 1})
    
    fold_y_1 = hy + half_gap
    fold_y_2 = hy + fold_gap + wall_h_y + half_gap
    fold_x_1 = hw + half_gap
    fold_x_2 = hw + fold_gap + wall_h_x + half_gap

    folds = [
        [(-hw - overlap, fold_y_1), (hw + overlap, fold_y_1)],
        [(-hw - overlap, fold_y_2), (hw + overlap, fold_y_2)],
        [(-hw - overlap, -fold_y_1), (hw + overlap, -fold_y_1)],
        [(-hw - overlap, -fold_y_2), (hw + overlap, -fold_y_2)],
        [(fold_x_1, -hy), (fold_x_1, hy)],
        [(fold_x_2, -hy), (fold_x_2, hy)],
        [(-fold_x_1, -hy), (-fold_x_1, hy)],
        [(-fold_x_2, -hy), (-fold_x_2, hy)]
    ]
    for fold in folds:
        msp.add_lwpolyline(fold, close=False, dxfattribs={'color': 2})
        
    stream = io.StringIO()
    doc.write(stream)
    return io.BytesIO(stream.getvalue().encode('utf-8'))

def get_custom_cardboard_box_dxf_bytes(w, y, h, custom_thick, fold_gap=9.0):
    doc = ezdxf.new('R2010')
    doc.units = units.MM
    msp = doc.modelspace()
    
    dims = sorted([w, y, h], reverse=True)
    dim_x = dims[0]
    dim_y = dims[1]
    wall_h = dims[2]
    
    base_w = dim_x
    base_y = dim_y
    
    hw, hy = base_w / 2, base_y / 2
    half_gap = fold_gap / 2.0
    
    wall_h_y = wall_h + 4.0 
    wall_h_x = wall_h 
    
    extra_flap_x = 50.0 
    total_offset_x = fold_gap + wall_h_x + fold_gap + extra_flap_x
    
    extra_flap_y = base_y / 2.0 
    total_offset_y = fold_gap + wall_h_y + fold_gap + extra_flap_y
    
    overlap = custom_thick 
    
    cross_pts = [
        (-hw - overlap, hy), (-hw - overlap, hy + total_offset_y),
        (hw + overlap, hy + total_offset_y), (hw + overlap, hy),
        (hw, hy), (hw + total_offset_x, hy), (hw + total_offset_x, -hy), (hw, -hy),
        (hw + overlap, -hy), (hw + overlap, -hy - total_offset_y),
        (-hw - overlap, -hy - total_offset_y), (-hw - overlap, -hy),
        (-hw, -hy), (-hw - total_offset_x, -hy), (-hw - total_offset_x, hy), (-hw, hy)
    ]
    msp.add_lwpolyline(cross_pts, close=True, dxfattribs={'color': 1})
    
    fold_y_1 = hy + half_gap
    fold_y_2 = hy + fold_gap + wall_h_y + half_gap
    fold_x_1 = hw + half_gap
    fold_x_2 = hw + fold_gap + wall_h_x + half_gap

    folds = [
        [(-hw - overlap, fold_y_1), (hw + overlap, fold_y_1)],
        [(-hw - overlap, fold_y_2), (hw + overlap, fold_y_2)],
        [(-hw - overlap, -fold_y_1), (hw + overlap, -fold_y_1)],
        [(-hw - overlap, -fold_y_2), (hw + overlap, -fold_y_2)],
        [(fold_x_1, -hy), (fold_x_1, hy)],
        [(fold_x_2, -hy), (fold_x_2, hy)],
        [(-fold_x_1, -hy), (-fold_x_1, hy)],
        [(-fold_x_2, -hy), (-fold_x_2, hy)]
    ]
    for fold in folds:
        msp.add_lwpolyline(fold, close=False, dxfattribs={'color': 2})
        
    stream = io.StringIO()
    doc.write(stream)
    return io.BytesIO(stream.getvalue().encode('utf-8'))

# --- UI ---
st.title("Acrylic Display & Box Generator")
st.markdown("""
    <style>
    div.stDownloadButton > button {
        background-color: #FF4B4B !important;
        color: white !important;
        border: 1px solid #FF4B4B !important;
        white-space: normal !important;
        word-break: break-word !important;
        text-align: center !important;
        padding: 0.5rem 1rem !important;
        height: auto !important;
        min-height: 42px !important;
    }
    div.stDownloadButton > button:hover {
        background-color: #FF2B2B !important;
        color: white !important;
        border: 1px solid #FF2B2B !important;
    }
    </style>
""", unsafe_allow_html=True)

thickness = st.radio("Толщина материала (акрил)", [3.0, 4.0], format_func=lambda x: f"{int(x)} мм", horizontal=True)

col1, col2 = st.columns([1, 1])
with col1:
    st.image("Picture.png", use_container_width=True)
with col2:
    inp_w = st.number_input("WIDTH - Внутренняя ширина", 50, 800, 60)
    inp_y = st.number_input("DEPTH - Внутренняя глубина", 50, 800, 60)
    inp_z = st.number_input("HEIGHTВнутренняя высота", 50, 800, 80)

    width_x = inp_w + (2 * thickness)
    depth_y = inp_y + (2 * thickness)
    height_z = inp_z + thickness

    # Изменен порядок на [4.0, 7.0], по умолчанию 4 мм
    cardboard_thickness = st.radio("Толщина картона коробки", [4.0, 7.0], key="box_thick_main", format_func=lambda x: f"{int(x)} мм", horizontal=True)
    box_fold_gap = 6.0 if cardboard_thickness == 4.0 else 9.0

    if st.button("Сгенерировать комплект (Acryl, Base, Leather, Box)"):
        is_w_large = inp_w > 150
        is_y_large = inp_y > 150
        is_z_large = inp_z > 150
        
        st.session_state['acryl_dxf'] = get_dxf_bytes(width_x, depth_y, height_z, thickness, is_w_large, is_y_large, is_z_large)
        st.session_state['acryl_file_name'] = f"Acryl_{inp_w}x{inp_y}x{inp_z}_({int(thickness)}mm).dxf"
        
        st.session_state['base_dxf'] = get_base_dxf_bytes(width_x, depth_y, thickness, inp_w)
        st.session_state['base_file_name'] = f"Base_{inp_w}x{inp_y}_({int(thickness)}mm).dxf"
        
        st.session_state['leather_dxf'] = get_leather_dxf_bytes(inp_w, inp_y)
        st.session_state['leather_file_name'] = f"Leather_{inp_w}x{inp_y}_({int(thickness)}mm).dxf"
        
        st.session_state['box_dxf'] = get_cardboard_box_dxf_bytes(width_x, depth_y, height_z, cardboard_thickness, box_fold_gap)
        st.session_state['box_file_name'] = f"Box_{inp_w}x{inp_y}x{inp_z}_({int(cardboard_thickness)}mm).dxf"
        
        st.success("Комплект успешно сгенерирован!")

    if all(k in st.session_state for k in ['acryl_dxf', 'base_dxf', 'leather_dxf', 'box_dxf']):
        st.markdown("### Скачать файлы комплекта:")
        dl_c1, dl_c2, dl_c3, dl_c4 = st.columns(4)
        with dl_c1:
            st.download_button("Acryl", data=st.session_state['acryl_dxf'], file_name=st.session_state.get('acryl_file_name', 'Acryl.dxf'))
        with dl_c2:
            st.download_button("Base", data=st.session_state['base_dxf'], file_name=st.session_state.get('base_file_name', 'Base.dxf'))
        with dl_c3:
            st.download_button("Leather", data=st.session_state['leather_dxf'], file_name=st.session_state.get('leather_file_name', 'Leather.dxf'))
        with dl_c4:
            st.download_button("Box", data=st.session_state['box_dxf'], file_name=st.session_state.get('box_file_name', 'Box.dxf'))

st.divider()

# --- Раздел пакетной генерации табличек (Name Plates) ---
st.subheader("Пакетная генерация табличек")
np_size_type = st.radio("Размер таблички", ["Маленькая (max 11 символов, ширина до 99)", "Большая (max 20 символов)"], horizontal=True)
is_small_plate = "Маленькая" in np_size_type

max_c = 11 if is_small_plate else 20
w_top_val = 51.0 if is_small_plate else 91.0
w_bot_val = 47.0 if is_small_plate else 87.0
max_text_width = 46.0 if is_small_plate else 86.0

np_font = st.selectbox("Шрифт табличек", ["Girassol", "Pirata One", "Bigshot One"], key="batch_font")
plate_lines_raw = st.text_area(f"Тексты табличек (каждая строка — новая табличка, макс. {max_c} символов на строку)")

if st.button("Сгенерировать файл с табличками"):
    lines = [line.strip() for line in plate_lines_raw.split("\n") if line.strip()]
    if not lines:
        st.warning("Введите хотя бы одну строчку текста!")
    else:
        doc = ezdxf.new('R2010')
        doc.units = units.MM
        msp = doc.modelspace()
        
        plate_w = w_top_val
        plate_h = 13.0
        spacing = 2.0
        
        for idx, text_line in enumerate(lines):
            if len(text_line) > max_c:
                text_line = text_line[:max_c]
                
            col_idx = idx // 6
            row_idx = idx % 6
            
            center_x = col_idx * (plate_w + spacing) + plate_w / 2
            center_y = -row_idx * (plate_h + spacing) - plate_h / 2
            
            draw_trapezoid_plate(msp, center_x, center_y, w_top_val, w_bot_val, plate_h, 2, text_line, np_font, max_text_width)
            
        stream = io.StringIO()
        doc.write(stream)
        st.session_state['plates_dxf'] = io.BytesIO(stream.getvalue().encode('utf-8'))
        st.session_state['plates_file_name'] = f"NamePlates_{len(lines)}pcs.dxf"
        st.success(f"Успешно сгенерировано табличек: {len(lines)}")

if 'plates_dxf' in st.session_state:
    st.download_button(
        label="Скачать файл с табличками", 
        data=st.session_state['plates_dxf'], 
        file_name=st.session_state.get('plates_file_name', 'NamePlates.dxf')
    )

st.divider()

# --- Раздел кастомной коробки ---
st.subheader("Custom Cardboard Box")
custom_thick = st.radio("Толщина картона кастомной коробки", [4.0, 7.0], key="box_thick_custom", format_func=lambda x: f"{int(x)} мм", horizontal=True)
custom_gap = 6.0 if custom_thick == 4.0 else 9.0

cc1, cc2, cc3 = st.columns(3)
with cc1:
    c_w = st.number_input("Ширина", 50, 1500, 100)
with cc2:
    c_y = st.number_input("Глубина", 50, 1500, 100)
with cc3:
    c_h = st.number_input("Высота", 50, 1500, 100)

if st.button("Generate Custom Cardboard Box"):
    st.session_state['custom_box_dxf'] = get_custom_cardboard_box_dxf_bytes(c_w, c_y, c_h, custom_thick, custom_gap)
    st.session_state['custom_box_file_name'] = f"CustomBox_{c_w}x{c_y}x{c_h}_({int(custom_thick)}mm).dxf"
    
if 'custom_box_dxf' in st.session_state:
    st.download_button(
        label="Скачать Custom Box DXF", 
        data=st.session_state['custom_box_dxf'], 
        file_name=st.session_state.get('custom_box_file_name', 'CustomBox.dxf')
    )
