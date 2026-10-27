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
