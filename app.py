def get_cardboard_box_dxf_bytes(w, y, h):
    doc = ezdxf.new('R2010')
    doc.units = units.MM
    msp = doc.modelspace()
    
    dimensions = sorted([w, y, h])
    dim1, dim2 = dimensions[1], dimensions[2]
    
    # Большая из двух сторон всегда по X, меньшая по Y
    dim_x = max(dim1, dim2)
    dim_y = min(dim1, dim2)
    
    # Размеры дна коробки
    base_w = dim_x + 27.0
    base_y = dim_y + 27.0
    
    hw, hy = base_w / 2, base_y / 2
    fold_gap = 9.0
    
    wall_height_y = 45.0 + 4.0 
    wall_total_offset_y = wall_height_y + fold_gap 
    
    # Клапаны зависят от размеров дна
    extra_flap_y = base_w / 2.0 
    total_offset_y = wall_total_offset_y + fold_gap + extra_flap_y
    
    wall_height_x = 45.0 
    wall_total_offset_x = wall_height_x + fold_gap 
    
    extra_flap_x = base_y / 2.0 
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
    
    # Ровно по 2 линии сгиба на каждый луч (одна у основания стенки, вторая у края клапана)
    folds = [
        # Верхний луч
        [(-hw - overlap, hy), (hw + overlap, hy)],
        [(-hw - overlap, hy + wall_height_y), (hw + overlap, hy + wall_height_y)],
        [(-hw - overlap, hy + wall_total_offset_y), (hw + overlap, hy + wall_total_offset_y)],
        
        # Нижний луч
        [(-hw - overlap, -hy), (hw + overlap, -hy)],
        [(-hw - overlap, -hy - wall_height_y), (hw + overlap, -hy - wall_height_y)],
        [(-hw - overlap, -hy - wall_total_offset_y), (hw + overlap, -hy - wall_total_offset_y)],
        
        # Правый луч
        [(hw, -hy), (hw, hy)],
        [(hw + wall_height_x, -hy), (hw + wall_height_x, hy)],
        [(hw + wall_total_offset_x, -hy), (hw + wall_total_offset_x, hy)],
        
        # Левый луч
        [(-hw, -hy), (-hw, hy)],
        [(-hw - wall_height_x, -hy), (-hw - wall_height_x, hy)],
        [(-hw - wall_total_offset_x, -hy), (-hw - wall_total_offset_x, hy)]
    ]
    
    for fold in folds:
        msp.add_lwpolyline(fold, close=False, dxfattribs={'color': 2})
        
    stream = io.StringIO()
    doc.write(stream)
    return io.BytesIO(stream.getvalue().encode('utf-8'))
