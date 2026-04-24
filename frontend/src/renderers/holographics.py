from src.styles.design_system import UI_CONFIG

def get_holo_box_svg(status="IDLE", team_color="#00ff88", connections=None, is_sealed=False, garment_color=None):
    """Genera un contenedor holográfico 3D avanzado basado en los sketches de diseño."""
    if connections is None: connections = {"top": False, "bottom": False, "left": False, "right": False}
    
    # ──────────────────────────────────────────────────────────
    # CONFIGURACIÓN VISUAL (Fácil de editar)
    # ──────────────────────────────────────────────────────────
    anim_class = "master-holo-box" if is_sealed else ""
    if garment_color is None: garment_color = team_color
    
    # Extraer valores desde la configuración unificada UI_CONFIG
    perim_opacity = UI_CONFIG["perim_opacity_sealed"] if is_sealed else UI_CONFIG["perim_opacity_open"]
    perim_stroke  = UI_CONFIG["perim_stroke"]
    
    floor_opacity = UI_CONFIG["floor_opacity_sealed"] if is_sealed else UI_CONFIG["floor_opacity_open"]
    floor_stroke  = UI_CONFIG["floor_stroke"]
    
    depth_opacity = UI_CONFIG["depth_opacity_sealed"] if is_sealed else UI_CONFIG["depth_opacity_open"]
    depth_stroke  = UI_CONFIG["depth_stroke"]
    
    div_opacity = UI_CONFIG["div_opacity"]
    div_stroke  = UI_CONFIG["div_stroke"]
    
    box_margin_x = UI_CONFIG["box_margin_x"]
    box_margin_y = UI_CONFIG["box_margin_y"]
    floor_inset_x = UI_CONFIG["floor_inset_x"]
    floor_inset_y = UI_CONFIG["floor_inset_y"]
    
    flap_height_y       = UI_CONFIG["flap_height_y"]
    flap_width_x        = UI_CONFIG["flap_width_x"]
    flap_angle_offset_x = UI_CONFIG["flap_angle_offset_x"]
    flap_angle_offset_y = UI_CONFIG["flap_angle_offset_y"]
    flap_stroke_op      = perim_opacity
    flap_fill_op        = UI_CONFIG["flap_fill_op"]
    flap_stroke_w       = UI_CONFIG["flap_stroke_w"]
    wall_fill_op        = UI_CONFIG["wall_fill_op"]
    # ──────────────────────────────────────────────────────────

    # 1. Definición de Coordenadas Maestras
    label_bg = "#ffffff"
    
    ix1, ix2 = (0 if connections["left"] else box_margin_x), (100 if connections["right"] else 100 - box_margin_x)
    iy1, iy2 = (0 if connections["top"] else box_margin_y), (100 if connections["bottom"] else 100 - box_margin_y)
    
    bx1, bx2 = (0 if connections["left"] else box_margin_x + floor_inset_x), (100 if connections["right"] else 100 - (box_margin_x + floor_inset_x))
    by1, by2 = (0 if connections["top"] else box_margin_y + floor_inset_y), (100 if connections["bottom"] else 100 - (box_margin_y + floor_inset_y))

    svg_elements = []

    # 2. RENDER: CAJA CERRADA / SELLADA
    if is_sealed:
        s_op = UI_CONFIG["sealed_base_opacity"]
        s_bw = UI_CONFIG["sealed_border_width"]
        t_w = UI_CONFIG["sealed_tape_width"]
        t_op = UI_CONFIG["sealed_tape_opacity"]
        
        p_path_sealed = ""
        if not connections["top"]:    p_path_sealed += f" M {ix1} {iy1} L {ix2} {iy1}" 
        if not connections["bottom"]: p_path_sealed += f" M {ix1} {iy2} L {ix2} {iy2}" 
        if not connections["left"]:   p_path_sealed += f" M {ix1} {iy1} L {ix1} {iy2}" 
        if not connections["right"]:  p_path_sealed += f" M {ix2} {iy1} L {ix2} {iy2}" 
        
        svg_elements.append(f'<path d="{p_path_sealed}" class="{anim_class}" fill="{team_color}" fill-opacity="{s_op}" stroke="{team_color}" stroke-width="{s_bw}"/>')
        
        # CINTA UNIFICADA (Con línea central y brillo neón)
        is_vertical_ship = connections["top"] or connections["bottom"]
        if is_vertical_ship:
            t_x = (ix1 + ix2) / 2
            t_y1 = 0 if connections["top"] else iy1
            t_y2 = 100 if connections["bottom"] else iy2
            # Línea Base (Brillante)
            svg_elements.append(f'<line x1="{t_x}" y1="{t_y1}" x2="{t_x}" y2="{t_y2}" class="{anim_class}" stroke="{team_color}" stroke-width="{t_w}" stroke-opacity="{t_op*1.5}"/>')
            # Línea Central de contraste
            svg_elements.append(f'<line x1="{t_x}" y1="{t_y1}" x2="{t_x}" y2="{t_y2}" stroke="#000" stroke-width="1.5" stroke-opacity="0.4"/>')
        else:
            t_y = (iy1 + iy2) / 2
            t_x1 = 0 if connections["left"] else ix1
            t_x2 = 100 if connections["right"] else ix2
            # Línea Base (Brillante)
            svg_elements.append(f'<line x1="{t_x1}" y1="{t_y}" x2="{t_x2}" y2="{t_y}" class="{anim_class}" stroke="{team_color}" stroke-width="{t_w}" stroke-opacity="{t_op*1.5}"/>')
            # Línea Central de contraste
            svg_elements.append(f'<line x1="{t_x1}" y1="{t_y}" x2="{t_x2}" y2="{t_y}" stroke="#000" stroke-width="1.5" stroke-opacity="0.4"/>')
            
        if not connections["right"] and not connections["bottom"]:
            lx, ly = (ix2-30, iy1+5) if not is_vertical_ship else (ix2-30, iy2-25)
            svg_elements.append(f'<g transform="translate({lx}, {ly}) rotate(12)">')
            svg_elements.append(f'  <rect width="26" height="18" fill="{label_bg}" rx="1" style="filter: drop-shadow(0 0 3px rgba(0,0,0,0.6));"/>')
            svg_elements.append(f'  <line x1="4" y1="6" x2="22" y2="6" stroke="#333" stroke-width="2" stroke-opacity="0.8"/>')
            svg_elements.append(f'  <line x1="4" y1="10" x2="16" y2="10" stroke="#333" stroke-width="1.5" stroke-opacity="0.5"/>')
            svg_elements.append(f'  <line x1="4" y1="13" x2="10" y2="13" stroke="#333" stroke-width="1" stroke-opacity="0.3"/>')
            svg_elements.append(f'</g>')
            
        return f'<svg viewBox="0 0 100 100" style="overflow:visible;">{"".join(svg_elements)}</svg>'

    # 3. RENDER: ESTRUCTURA 3D INTERNA (Caja Abierta)
    # Paredes Internas (Fills para dar volumen)
    if not is_sealed:
        # Pared Superior
        if not connections["top"]:
            p_top = f"M {ix1} {iy1} L {ix2} {iy1} L {bx2} {by1} L {bx1} {by1} Z"
            svg_elements.append(f'<path d="{p_top}" fill="{team_color}" fill-opacity="{wall_fill_op}" stroke="none"/>')
        # Pared Inferior
        if not connections["bottom"]:
            p_bot = f"M {ix1} {iy2} L {ix2} {iy2} L {bx2} {by2} L {bx1} {by2} Z"
            svg_elements.append(f'<path d="{p_bot}" fill="{team_color}" fill-opacity="{wall_fill_op}" stroke="none"/>')
        # Pared Izquierda
        if not connections["left"]:
            p_left = f"M {ix1} {iy1} L {ix1} {iy2} L {bx1} {by2} L {bx1} {by1} Z"
            svg_elements.append(f'<path d="{p_left}" fill="{team_color}" fill-opacity="{wall_fill_op}" stroke="none"/>')
        # Pared Derecha
        if not connections["right"]:
            p_right = f"M {ix2} {iy1} L {ix2} {iy2} L {bx2} {by2} L {bx2} {by1} Z"
            svg_elements.append(f'<path d="{p_right}" fill="{team_color}" fill-opacity="{wall_fill_op}" stroke="none"/>')

    # Fondo (Solo bordes exteriores no conectados)
    f_path_bx = ""
    if not connections["top"]:    f_path_bx += f" M {bx1} {by1} L {bx2} {by1}"
    if not connections["bottom"]: f_path_bx += f" M {bx1} {by2} L {bx2} {by2}"
    if not connections["left"]:   f_path_bx += f" M {bx1} {by1} L {bx1} {by2}"
    if not connections["right"]:  f_path_bx += f" M {bx2} {by1} L {bx2} {by2}"
    if f_path_bx:
        svg_elements.append(f'<path d="{f_path_bx}" fill="none" stroke="{team_color}" stroke-width="{floor_stroke}" stroke-opacity="{floor_opacity}"/>')

    # Perímetro Exterior (Solo bordes no conectados)
    p_path_ix = ""
    if not connections["top"]:    p_path_ix += f" M {ix1} {iy1} L {ix2} {iy1}" 
    if not connections["bottom"]: p_path_ix += f" M {ix1} {iy2} L {ix2} {iy2}" 
    if not connections["left"]:   p_path_ix += f" M {ix1} {iy1} L {ix1} {iy2}" 
    if not connections["right"]:  p_path_ix += f" M {ix2} {iy1} L {ix2} {iy2}" 
    if p_path_ix:
        svg_elements.append(f'<path d="{p_path_ix}" fill="none" stroke="{team_color}" stroke-width="{perim_stroke}" stroke-opacity="{perim_opacity}"/>')

    # Diagonales de Profundidad (Solo en esquinas exteriores reales)
    if not connections["left"] and not connections["top"]:    svg_elements.append(f'<line x1="{ix1}" y1="{iy1}" x2="{bx1}" y2="{by1}" stroke="{team_color}" stroke-width="{depth_stroke}" stroke-opacity="{depth_opacity}"/>')
    if not connections["right"] and not connections["top"]:   svg_elements.append(f'<line x1="{ix2}" y1="{iy1}" x2="{bx2}" y2="{by1}" stroke="{team_color}" stroke-width="{depth_stroke}" stroke-opacity="{depth_opacity}"/>')
    if not connections["left"] and not connections["bottom"]: svg_elements.append(f'<line x1="{ix1}" y1="{iy2}" x2="{bx1}" y2="{by2}" stroke="{team_color}" stroke-width="{depth_stroke}" stroke-opacity="{depth_opacity}"/>')
    if not connections["right"] and not connections["bottom"]:svg_elements.append(f'<line x1="{ix2}" y1="{iy2}" x2="{bx2}" y2="{by2}" stroke="{team_color}" stroke-width="{depth_stroke}" stroke-opacity="{depth_opacity}"/>')

    # Icono de Prenda (En el centro 50,50 con su propio glow)
    if status == "LOAD":
        l_sc = UI_CONFIG["load_icon_scale"]
        l_sw = UI_CONFIG["load_icon_stroke"]
        l_op = UI_CONFIG["load_icon_opacity"]
        icon_anim = "master-holo-box" if not is_sealed else "" 
        # Icono Detallado (Unificado) centrando el viewBox de ~20x22
        svg_elements.append(f'<g transform="translate(50,50) scale({l_sc * 0.8}) translate(-10,-11)">')
        svg_elements.append(f'  <path d="M20.38 3.46L16 2a4 4 0 01-8 0L3.62 3.46a2 2 0 00-1.34 2.23l.58 3.47a1 1 0 00.99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 002-2V10h2.15a1 1 0 00.99-.84l.58-3.47a2 2 0 00-1.34-2.23z" class="{icon_anim}" fill="none" stroke="{garment_color}" stroke-width="{l_sw}" stroke-opacity="{l_op}"/>')
        svg_elements.append(f'</g>')

    # 4. RENDER: SOLAPAS (FLAPS)
    # Flap Superior
    if not connections["top"]:
        f_x1 = ix1 + (0 if connections["left"] else flap_angle_offset_x)
        f_x2 = ix2 - (0 if connections["right"] else flap_angle_offset_x)
        path = f"M {ix1} {iy1} L {f_x1} {iy1-flap_height_y} L {f_x2} {iy1-flap_height_y} L {ix2} {iy1}"
        # Solo cerramos la base si no es una conexión vertical (para evitar ruido)
        path += f" L {ix1} {iy1}"
        svg_elements.append(f'<path d="{path}" fill="{team_color}" fill-opacity="{flap_fill_op}" stroke="{team_color}" stroke-opacity="{flap_stroke_op}" stroke-width="{flap_stroke_w}"/>')
    
    # Flap Inferior
    if not connections["bottom"]:
        f_x1 = ix1 + (0 if connections["left"] else flap_angle_offset_x)
        f_x2 = ix2 - (0 if connections["right"] else flap_angle_offset_x)
        path = f"M {ix1} {iy2} L {f_x1} {iy2+flap_height_y} L {f_x2} {iy2+flap_height_y} L {ix2} {iy2} L {ix1} {iy2}"
        svg_elements.append(f'<path d="{path}" fill="{team_color}" fill-opacity="{flap_fill_op}" stroke="{team_color}" stroke-opacity="{flap_stroke_op}" stroke-width="{flap_stroke_w}"/>')

    # Flap Izquierdo
    if not connections["left"]:
        f_y1 = iy1 + (0 if connections["top"] else flap_angle_offset_y)
        f_y2 = iy2 - (0 if connections["bottom"] else flap_angle_offset_y)
        path = f"M {ix1} {iy1} L {ix1-flap_width_x} {f_y1} L {ix1-flap_width_x} {f_y2} L {ix1} {iy2} L {ix1} {iy1}"
        svg_elements.append(f'<path d="{path}" fill="{team_color}" fill-opacity="{flap_fill_op}" stroke="{team_color}" stroke-opacity="{flap_stroke_op}" stroke-width="{flap_stroke_w}"/>')
        
    # Flap Derecho
    if not connections["right"]:
        f_y1 = iy1 + (0 if connections["top"] else flap_angle_offset_y)
        f_y2 = iy2 - (0 if connections["bottom"] else flap_angle_offset_y)
        path = f"M {ix2} {iy1} L {ix2+flap_width_x} {f_y1} L {ix2+flap_width_x} {f_y2} L {ix2} {iy2} L {ix2} {iy1}"
        svg_elements.append(f'<path d="{path}" fill="{team_color}" fill-opacity="{flap_fill_op}" stroke="{team_color}" stroke-opacity="{flap_stroke_op}" stroke-width="{flap_stroke_w}"/>')

    # 5. DIVISORES INTERNOS (ELIMINADOS PARA SEAMLESS BORDERS)
    pass

    # 🔷 RETORNO FINAL: SVG sin clase de animación global y sin opacidad base para evitar fugas de brillo 🔷
    return f'<svg viewBox="0 0 100 100" style="overflow:visible;">{"".join(svg_elements)}</svg>'


def get_holo_miss_svg():
    """Representación de prenda en el suelo (Fallo - Versión original ampliada)."""
    m_c_sc = UI_CONFIG["miss_container_scale"]
    m_i_sc = UI_CONFIG["miss_icon_scale"]
    m_sw = UI_CONFIG["miss_icon_stroke"]
    m_op = UI_CONFIG["miss_icon_opacity"]
    m_col = UI_CONFIG["miss_color"]
    # Usamos el mismo icono DETALLADO que en el Load
    path_camiseta = "M20.38 3.46L16 2a4 4 0 01-8 0L3.62 3.46a2 2 0 00-1.34 2.23l.58 3.47a1 1 0 00.99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 002-2V10h2.15a1 1 0 00.99-.84l.58-3.47a2 2 0 00-1.34-2.23z"
    return f'<svg viewBox="0 0 100 100" style="opacity:{m_op}; transform: rotate(45deg) scale({m_c_sc});"><path d="{path_camiseta}" fill="none" stroke="{m_col}" stroke-width="{m_sw}" transform="translate(35,35) scale({m_i_sc})"/></svg>'
