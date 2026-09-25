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
    """Динамически вычисляет размер шрифта, чтобы текст не превышал max_allowed_width"""
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

def show_preview(w_top, w_bot, height, text, font_name, max_allowed_width):
    plt.close('all')
    fig, ax = plt.subplots(figsize=(6, 2))
    
    pts = [(-w_top/2, height/2), (w_top/2, height/2), (w_bot/2, -height/2), (-w_bot/2, -height/2), (-w_top/2, height/2)]
    x, y = zip(*pts)
    ax.plot(x, y, color='#b0b0b0', linewidth=1.5, linestyle='--')
    
    if text:
        fp = get_google_font_prop(font_name)
        font_size = get_adaptive_font_size(text, height, font_name, max_allowed_width)
        tp = TextPath((0, 0), text, size=font_size, prop=fp)
        
        bbox = tp.get_extents()
        dx = -(bbox.x0 + bbox.x1) / 2
        dy = -(bbox.y0 + bbox.y1) / 2
        
        for path_data in tp.to_polygons():
            text_pts = [(p[0] + dx, p[1] + dy) for p in path_data]
            px, py = zip(*text_pts)
            ax.plot(px, py, color='#1f77b4', linewidth=1.0)
    
    ax.set_aspect('equal')
    ax.autoscale()
    ax.margins(0.1)
    ax.axis('off')
    st.pyplot(fig)

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

def get_base_dxf_bytes(w, y, include_name_plate, thickness, inp_w):
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
    
    if include_name_plate:
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

def get_cardboard_box_dxf_bytes(w, y, h, fold_gap=9.0):
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
    
    overlap = 7.0 
    
    cross_pts = [
        (-hw - overlap, hy),
        (-hw - overlap, hy + total_offset_y),
        (hw + overlap, hy + total_offset_y),
        (hw + overlap, hy),
        
        (hw, hy),
        (hw + total_offset_x, hy),
        (hw + total_offset_x, -hy),
        (hw, -hy),
        
        (hw + overlap, -hy),
        (hw + overlap, -hy - total_offset_y),
        (-hw - overlap, -hy - total_offset_y),
        (-hw - overlap, -hy),
        
        (-hw, -hy),
        (-hw - total_offset_x, -hy),
        (-hw - total_offset_x, hy),
        (-hw, hy)
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

def get_custom_cardboard_box_dxf_bytes(w, y, h, fold_gap=9.0):
    doc = ezdxf.new('R2010')
    doc.units = units.MM
    msp = doc.modelspace()
    
    dims = sorted([w, y, h], reverse=True)
    dim_x = dims[0]  # Самая длинная -> X
    dim_y = dims[1]  # Вторая -> Y
    wall_h = dims[2] # Третья -> высота стенок
    
    base_w = dim_x + 27.0
    base_y = dim_y + 27.0
    
    hw, hy = base_w / 2, base_y / 2
    half_gap = fold_gap / 2.0
    
    wall_h_y = wall_h + 4.0 
    wall_h_x = wall_h 
    
    extra_flap_x = 50.0 
    total_offset_x = fold_gap + wall_h_x + fold_gap + extra_flap_x
    
    extra_flap_y = base_y / 2.0 
    total_offset_y = fold_gap + wall_h_y + fold_gap + extra_flap_y
    
    overlap = 7.0 
    
    cross_pts = [
        (-hw - overlap, hy),
        (-hw - overlap, hy + total_offset_y),
        (hw + overlap, hy + total_offset_y),
        (hw + overlap, hy),
        
        (hw, hy),
        (hw + total_offset_x, hy),
        (hw + total_offset_x, -hy),
        (hw, -hy),
        
        (hw + overlap, -hy),
        (hw + overlap, -hy - total_offset_y),
        (-hw - overlap, -hy - total_offset_y),
        (-hw - overlap, -hy),
        
        (-hw, -hy),
        (-hw - total_offset_x, -hy),
        (-hw - total_offset_x, hy),
        (-hw, hy)
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
st.title("Acrylic Display Generator")
st.markdown("""
    <style>
    div.stDownloadButton > button {
        background-color: #FF4B4B !important;
        color: white !important;
        border: 1px solid #FF4B4B !important;
    }
    div.stDownloadButton > button:hover {
        background-color: #FF2B2B !important;
        color: white !important;
        border: 1px solid #FF2B2B !important;
    }
    </style>
""", unsafe_allow_html=True)

thickness = st.radio("Толщина материала", [3.0, 4.0], format_func=lambda x: f"{int(x)} мм", horizontal=True)

col1, col2 = st.columns([1, 1])
with col1:
    st.image("Picture.png", use_container_width=True)
with col2:
    inp_w = st.number_input("Внутренняя ширина (X)", 50, 800, 60)
    inp_y = st.number_input("Внутренняя глубина (Y)", 50, 800, 60)
    inp_z = st.number_input("Внутренняя высота (Z)", 50, 800, 80)

    width_x = inp_w + (2 * thickness)
    depth_y = inp_y + (2 * thickness)
    height_z = inp_z + thickness

    if st.button("Generate Main"):
        is_w_large = inp_w > 150
        is_y_large = inp_y > 150
        is_z_large = inp_z > 150
        
        st.session_state['dxf_data'] = get_dxf_bytes(width_x, depth_y, height_z, thickness, is_w_large, is_y_large, is_z_large)
        st.session_state['main_file_name'] = f"Main_{width_x:.1f}x{depth_y:.1f}x{height_z:.1f}.dxf"
    
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
        st.session_state['base_dxf'] = get_base_dxf_bytes(width_x, depth_y, include_plate, thickness, inp_w)
        st.session_state['base_file_name'] = f"Base_{width_x:.1f}x{depth_y:.1f}.dxf"
    
    if 'base_dxf' in st.session_state:
        st.download_button(
            label="Скачать Base DXF", 
            data=st.session_state['base_dxf'], 
            file_name=st.session_state.get('base_file_name', 'Base.dxf')
        )

if st.session_state.get('name_plate_val', False):
    st.subheader("Name Plate Settings")
    
    max_c = 11 if inp_w <= 99 else 20
    plate_text = st.text_input(f"Текст (max {max_c})", max_chars=max_c)
    plate_font = st.selectbox("Шрифт", ["Girassol", "Pirata One", "Bigshot One"])
    
    w_top_val = 51.0 if inp_w <= 99 else 91.0
    w_bot_val = 47.0 if inp_w <= 99 else 87.0
    
    max_text_width = 46.0 if inp_w <= 99 else 86.0
    
    if plate_text:
        show_preview(w_top_val, w_bot_val, 13, plate_text, plate_font, max_text_width)
        
    if st.button("Generate Name Plate File"):
        doc = ezdxf.new('R2010')
        doc.units = units.MM
        draw_trapezoid_plate(doc.modelspace(), 0, 0, w_top_val, w_bot_val, 13, 2, plate_text, plate_font, max_text_width)
        
        stream = io.StringIO()
        doc.write(stream)
        st.session_state['plate_dxf'] = io.BytesIO(stream.getvalue().encode('utf-8'))
        
        clean_text = "".join([c for c in plate_text if c.isalnum() or c in (' ', '_')]).strip()
        st.session_state['plate_file_name'] = f"Plate_{clean_text if clean_text else 'Custom'}.dxf"
        
    if 'plate_dxf' in st.session_state:
        st.download_button(
            label="Скачать Plate DXF", 
            data=st.session_state['plate_dxf'], 
            file_name=st.session_state.get('plate_file_name', 'Plate.dxf')
        )

st.divider()

# --- Раздел коробок в две колонки ---
box_col1, box_col2 = st.columns(2)

with box_col1:
    st.subheader("Cardboard Box")
    cardboard_thickness = st.radio("Толщина картона коробки", [7.0, 4.0], key="box_thick_main", format_func=lambda x: f"{int(x)} мм", horizontal=True)
    box_fold_gap = 9.0 if cardboard_thickness == 7.0 else 6.0
        
    if st.button("Generate Cardboard Box"):
        st.session_state['box_dxf'] = get_cardboard_box_dxf_bytes(width_x, depth_y, height_z, box_fold_gap)
        st.session_state['box_file_name'] = f"Box_{width_x:.1f}x{depth_y:.1f}x{height_z:.1f}_({int(cardboard_thickness)}mm).dxf"
        
    if 'box_dxf' in st.session_state:
        st.download_button(
            label="Скачать Box DXF", 
            data=st.session_state['box_dxf'], 
            file_name=st.session_state.get('box_file_name', 'Box.dxf')
        )

with box_col2:
    st.subheader("Custom Cardboard Box")
    custom_thick = st.radio("Толщина картона кастомной коробки", [7.0, 4.0], key="box_thick_custom", format_func=lambda x: f"{int(x)} мм", horizontal=True)
    custom_gap = 9.0 if custom_thick == 7.0 else 6.0
    
    c_w = st.number_input("Ширина", 50, 1500, 100)
    c_y = st.number_input("Глубина", 50, 1500, 100)
    c_h = st.number_input("Высота", 50, 1500, 100)
    
    if st.button("Generate Custom Cardboard Box"):
        st.session_state['custom_box_dxf'] = get_custom_cardboard_box_dxf_bytes(c_w, c_y, c_h, custom_gap)
        st.session_state['custom_box_file_name'] = f"CustomBox_{c_w:.1f}x{c_y:.1f}x{c_h:.1f}_({int(custom_thick)}mm).dxf"
        
    if 'custom_box_dxf' in st.session_state:
        st.download_button(
            label="Скачать Custom Box DXF", 
            data=st.session_state['custom_box_dxf'], 
            file_name=st.session_state.get('custom_box_file_name', 'CustomBox.dxf')
        )
