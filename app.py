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
def add_holes(msp, start_x, start_y, width, height, is_wide, is_high, is_bottom_part, thickness=3.0):
    r = 1.25
    # Угловой отступ: 6.0 для 3мм, 7.0 для 4мм
    corner_offset = 6.0 if thickness == 3.0 else 7.0
    
    # Нижний отступ одинаковый для 3мм и 4мм
    bottom_offset = 6.0 if is_bottom_part else 8.0

    # Основные 4 угла
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

def draw_trapezoid_plate(msp, center_x, center_y, w_top, w_bot, height, radius, text, font):
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
        font_map = {"STANDARD": "sans-serif", "TXT": "monospace", "ROMANS": "serif", "ITALIC": "serif"}
        family = font_map.get(font, "sans-serif")
        
        fp = FontProperties(family=family, weight='bold')
        tp = TextPath((0, 0), text, size=height*0.4, prop=fp)
        
        bbox = tp.get_extents()
        dx = -(bbox.x0 + bbox.x1) / 2 + center_x
        dy = -(bbox.y0 + bbox.y1) / 2 + center_y
        
        for path_data in tp.to_polygons():
            text_pts = [(p[0] + dx, p[1] + dy) for p in path_data]
            msp.add_lwpolyline(text_pts, close=True, dxfattribs={'color': 92})

def show_preview(w_top, w_bot, height, text, font_name):
    plt.close('all')
    fig, ax = plt.subplots(figsize=(5, 1.5))
    pts = [(-w_top/2, height/2), (w_top/2, height/2), (w_bot/2, -height/2), (-w_bot/2, -height/2), (-w_top/2, height/2)]
    x, y = zip(*pts)
    ax.plot(x, y, 'g-')
    
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

def get_base_dxf_bytes(w, y, include_name_plate, thickness):
    doc = ezdxf.new('R2010')
    doc.units = units.MM
    msp = doc.modelspace()
    
    extra_blue = 2.0
    extra_red = 20.0
    
    # 1. Синий контур (Color 5)
    w1, h1 = w + extra_blue, y + extra_blue
    hw1, hh1 = w1 / 2, h1 / 2
    msp.add_lwpolyline([(-hw1, -hh1), (hw1, -hh1), (hw1, hh1), (-hw1, hh1)], close=True, dxfattribs={'color': 5})
    
    # 2. Красный контур (Color 1)
    w2, h2 = w1 + extra_red, h1 + extra_red
    hw2, hh2 = w2 / 2, h2 / 2
    red_bottom_y = -hh2 
    msp.add_lwpolyline([(-hw2, -hh2), (hw2, -hh2), (hw2, hh2), (-hw2, hh2)], close=True, dxfattribs={'color': 1})
    
    # 3. Зеленая линия
    if include_name_plate:
        fixed_link_scale = thickness / 3.0
        fixed_line_w = 90.0 * fixed_link_scale
        half_line_w = fixed_line_w / 2
        bevel = int(7 * fixed_link_scale)
        
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

def get_cardboard_box_dxf_bytes(w, y, h):
    doc = ezdxf.new('R2010')
    doc.units = units.MM
    msp = doc.modelspace()
    
    dimensions = sorted([w, y, h])
    dim1, dim2 = dimensions[1], dimensions[2]
    
    # Большая из двух сторон всегда по X, меньшая по Y
    dim_x = max(dim1, dim2)
    dim_y = min(dim1, dim2)
    
    base_w = dim_x + 27.0
    base_y = dim_y + 27.0
    
    hw, hy = base_w / 2, base_y / 2
    fold_gap = 9.0
    
    wall_height_y = 45.0 + 4.0 
    wall_total_offset_y = wall_height_y + fold_gap 
    extra_flap_y = dim_x / 2.0 
    total_offset_y = wall_total_offset_y + fold_gap + extra_flap_y
    
    wall_height_x = 45.0 
    wall_total_offset_x = wall_height_x + fold_gap 
    extra_flap_x = dim_y / 2.0 
    total_offset_x = wall_total_offset_x + fold_gap + extra_flap_x
    
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
    
    folds = [
        [(-hw - overlap, hy), (hw + overlap, hy)],
        [(-hw - overlap, hy + fold_gap), (hw + overlap, hy + fold_gap)],
        [(-hw - overlap, hy + wall_total_offset_y), (hw + overlap, hy + wall_total_offset_y)],
        [(-hw - overlap, hy + wall_total_offset_y + fold_gap), (hw + overlap, hy + wall_total_offset_y + fold_gap)],
        
        [(-hw - overlap, -hy), (hw + overlap, -hy)],
        [(-hw - overlap, -hy - fold_gap), (hw + overlap, -hy - fold_gap)],
        [(-hw - overlap, -hy - wall_total_offset_y), (hw + overlap, -hy - wall_total_offset_y)],
        [(-hw - overlap, -hy - wall_total_offset_y - fold_gap), (hw + overlap, -hy - wall_total_offset_y - fold_gap)],
        
        [(hw, -hy), (hw, hy)],
        [(hw + fold_gap, -hy), (hw + fold_gap, hy)],
        [(hw + wall_total_offset_x, -hy), (hw + wall_total_offset_x, hy)],
        [(hw + wall_total_offset_x + fold_gap, -hy), (hw + wall_total_offset_x + fold_gap, hy)],
        
        [(-hw, -hy), (-hw, hy)],
        [(-hw - fold_gap, -hy), (-hw - fold_gap, hy)],
        [(-hw - wall_total_offset_x, -hy), (-hw - wall_total_offset_x, hy)],
        [(-hw - wall_total_offset_x + fold_gap, -hy), (-hw - wall_total_offset_x + fold_gap, hy)]
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
        st.session_state['base_dxf'] = get_base_dxf_bytes(width_x, depth_y, include_plate, thickness)
        st.session_state['base_file_name'] = f"Base_{width_x:.1f}x{depth_y:.1f}.dxf"
    
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
        show_preview(91, 87, 13, plate_text, plate_font)
    if st.button("Generate Name Plate File"):
        doc = ezdxf.new('R2010')
        doc.units = units.MM
        draw_trapezoid_plate(doc.modelspace(), 0, 0, 91, 87, 13, 2, plate_text, plate_font)
        
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
st.subheader("Cardboard Box (Cross Net)")
    
if st.button("Generate Cardboard Box"):
        st.session_state['box_dxf'] = get_cardboard_box_dxf_bytes(width_x, depth_y, height_z)
        st.session_state['box_file_name'] = f"Box_Cross_{width_x:.1f}x{depth_y:.1f}x{height_z:.1f}.dxf"
    
if 'box_dxf' in st.session_state:
        st.download_button(
            label="Скачать Box DXF", 
            data=st.session_state['box_dxf'], 
            file_name=st.session_state.get('box_file_name', 'Box.dxf')
        )
