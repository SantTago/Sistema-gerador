import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageDraw, ImageFont
import random
from fpdf import FPDF
import os
from datetime import date
import threading

# ----------------------------------------------------------------------
# ---- Configurações do Bilhete e Layout (Folha A4 Completa) ----
# ----------------------------------------------------------------------

IMAGE_PATH = "01.jpg" 

GRID_COLS = 4 
GRID_ROWS = 5
CARTELAS_POR_PAGINA = GRID_COLS * GRID_ROWS # 20 bilhetes por página

# Dimensões do bilhete individual (usadas como base para PROPORÇÃO)
BILHETE_REF_LARGURA_PX = 1200
BILHETE_REF_ALTURA_PX = 700

# --------------------------------------------------------------------------------
# CORDENADAS E DIMENSÕES DE CADA CAMPO EM PIXELS (NO BILHETE DE REFERÊNCIA 1200x700)
#
# Esta seção define a posição DOS NÚMEROS DENTRO DE CADA BILHETE (SEM AJUSTE).
# Formato: 'CAMPO_NOME': (X_TopLeft, Y_TopLeft, Largura_do_Campo, Altura_do_Campo)
# --------------------------------------------------------------------------------
REF_CAMPO_DIMENSIONS_AND_POS = {
    # Sequências (Números principais, 4 dígitos)
    'CAMPO_SEQ1': (410, 318, 200, 50), 
    'CAMPO_SEQ2': (410, 375, 200, 50), 
    'CAMPO_SEQ3': (410, 432, 200, 50), 
    
    # Infos Inferiores (Número do Bilhete e Data)
    'CAMPO_NUM_BILHETE': (20, 480, 160, 40),
    'CAMPO_DATA_BILHETE': (240, 480, 160, 40),
}

# --------------------------------------------------------------------------------
# --- AJUSTES INDIVIDUAIS POR CAMPO E POR BILHETE (0 a 19) ---
# 
# Você deve editar os valores (Ajuste_X, Ajuste_Y) em um dos 5 dicionários abaixo:
# X: Positivo move para a DIREITA. Negativo move para a ESQUERDA.
# Y: Positivo move para BAIXO. Negativo move para CIMA.
# --------------------------------------------------------------------------------

# Mapeamento do Índice (Slot 0 é o primeiro bilhete, Slot 19 é o último)
# Fileira 1: 0, 1, 2, 3
# Fileira 2: 4, 5, 6, 7
# Fileira 3: 8, 9, 10, 11
# Fileira 4: 12, 13, 14, 15
# Fileira 5: 16, 17, 18, 19

# 1. AJUSTE PARA O NÚMERO DE BILHETE (Ex: 00001, 00002)
AJUSTE_NUM_BILHETE_INDIVIDUAL = {
    0: (175, 170), 1: (120, 170), 2: (70, 170), 3: (17, 170),     # Fileira 1
    4: (170, 130), 5: (120, 130), 6: (70, 130), 7: (17, 130),     # Fileira 2
    8: (175, 90), 9: (120, 90), 10: (70, 90), 11: (17, 90),   # Fileira 3
    12: (175, 45), 13: (120, 45), 14: (70, 45), 15: (17, 45), # Fileira 4
    16: (175, 10), 17: (120, 10), 18: (70, 10), 19: (17, 10)  # Fileira 5
}

# 2. AJUSTE PARA A DATA DO SORTEIO (Ex: 15/08/25)
AJUSTE_DATA_BILHETE_INDIVIDUAL = {
    0: (255, 170), 1: (207, 170), 2: (160, 170), 3: (105, 170),     
    4: (255, 130), 5: (207, 130), 6: (160, 130), 7: (105, 130),     
    8: (255, 90), 9: (207, 90), 10: (160, 90), 11: (105, 90),   
    12: (255, 45), 13: (207, 45), 14: (160, 45), 15: (105, 45), 
    16: (255, 10), 17: (207, 10), 18: (160, 10), 19: (105, 10)  
}

# 3. AJUSTE PARA A PRIMEIRA SEQUÊNCIA (CAMPO_SEQ1)
AJUSTE_SEQ1_INDIVIDUAL = {
    0: (450, 180), 1: (400, 180), 2: (350, 180), 3: (300, 180),     
    4: (450, 140), 5: (400, 140), 6: (350, 140), 7: (300, 140),  
    8: (450, 100), 9: (400, 100), 10: (350, 100), 11: (300, 100),   
    12: (450, 60), 13: (400, 60), 14: (350, 60), 15: (300, 60), 
    16: (450, 20), 17: (400, 20), 18: (350, 20), 19: (300, 20)  
}

# 4. AJUSTE PARA A SEGUNDA SEQUÊNCIA (CAMPO_SEQ2)
AJUSTE_SEQ2_INDIVIDUAL = {
    0: (450, 200), 1: (400, 200), 2: (350, 200), 3: (300, 200),     
    4: (450, 160), 5: (400, 160), 6: (350, 160), 7: (300, 160),     
    8: (450, 200), 9: (400, 120), 10: (350, 120), 11: (300, 120),   
    12: (450, 155), 13: (400, 80), 14: (350, 80), 15: (300, 80), 
    16: (450, 120), 17: (400, 40), 18: (350, 40), 19: (300, 40)  
}

# 5. AJUSTE PARA A TERCEIRA SEQUÊNCIA (CAMPO_SEQ3)
AJUSTE_SEQ3_INDIVIDUAL = {
    0: (450, 220), 1: (400, 220), 2: (350, 220), 3: (300, 220),     
    4: (450, 180), 5: (400, 180), 6: (350, 180), 7: (300, 180),     
    8: (450, 60), 9: (400, 140), 10: (350, 140), 11: (300, 140),   
    12: (450, 20), 13: (400, 100), 14: (350, 100), 15: (300, 100), 
    16: (450, -20), 17: (400, 60), 18: (350, 60), 19: (300, 60)  
}
# --------------------------------------------------------------------------------

# Mapa interno para referenciar os dicionários de ajuste dinamicamente
FIELD_ADJUSTMENT_MAP = {
    'CAMPO_NUM_BILHETE': AJUSTE_NUM_BILHETE_INDIVIDUAL,
    'CAMPO_DATA_BILHETE': AJUSTE_DATA_BILHETE_INDIVIDUAL,
    'CAMPO_SEQ1': AJUSTE_SEQ1_INDIVIDUAL,
    'CAMPO_SEQ2': AJUSTE_SEQ2_INDIVIDUAL,
    'CAMPO_SEQ3': AJUSTE_SEQ3_INDIVIDUAL,
}

# Definições de Fonte
try:
    # Tenta usar uma fonte comum em sistemas Windows (Arial Bold)
    FONT_PATH = "C:\\Windows\\Fonts\\arialbd.ttf" 
    MAIN_FONT_REF = ImageFont.truetype(FONT_PATH, 55) # Tamanho base para as 3 sequências
    SMALL_FONT_REF = ImageFont.truetype(FONT_PATH, 35) # Tamanho base para o número e data
except IOError:
    # Se a fonte não for encontrada, usa a padrão (que pode não ter o mesmo alinhamento)
    MAIN_FONT_REF = ImageFont.load_default() 
    SMALL_FONT_REF = ImageFont.load_default()

SEQUENCIAS_JA_USADAS = set()
PDF_FILENAME = "Grupo da Sorte - Bilhetes.pdf"


# ----------------------------------------------------------------------
# ---- Funções de Geração e Lógica ----
# ----------------------------------------------------------------------

def gerar_sequencia_unica():
    """Gera uma sequência de 3x4 números única e não repetida para os 3 campos."""
    global SEQUENCIAS_JA_USADAS
    while True:
        seq1 = f"{random.randint(0, 9999):04d}"
        seq2 = f"{random.randint(0, 9999):04d}"
        seq3 = f"{random.randint(0, 9999):04d}"
        combinacao = (seq1, seq2, seq3)
        if combinacao not in SEQUENCIAS_JA_USADAS:
            SEQUENCIAS_JA_USADAS.add(combinacao)
            return combinacao

def draw_text_centered(draw_obj, text, font, fill_color, top_left_x, top_left_y, width, height):
    """
    Desenha o texto centralizado dentro de uma caixa (campo branco) definida.
    """
    text_bbox = draw_obj.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Calcula a posição central dentro da caixa
    center_x = top_left_x + (width / 2)
    center_y = top_left_y + (height / 2)

    # Ajusta o ponto de desenho para que o texto fique centralizado
    text_x = center_x - (text_width / 2)
    text_y = center_y - (text_height / 2)
    
    # Ajuste vertical fino para compensar o 'baseline' da fonte
    text_y += (text_bbox[1] / 2) 
    
    draw_obj.text((text_x, text_y), text, font=font, fill=fill_color)

def get_scaled_field_dims(field_name, slot_index, slot_start_x, slot_start_y, ticket_properties):
    """
    Calcula as dimensões e posição do campo escaladas, aplicando o ajuste 
    individual específico para o campo e o slot atuais.
    """
    x_ref, y_ref, w_ref, h_ref = REF_CAMPO_DIMENSIONS_AND_POS[field_name]
    
    # Busca o dicionário de ajustes específico para este campo
    adjustment_map = FIELD_ADJUSTMENT_MAP.get(field_name, {})
    
    # Busca o ajuste (X, Y) para o slot atual (default é (0, 0))
    ajuste_x_ref, ajuste_y_ref = adjustment_map.get(slot_index, (0, 0))
    
    # Converte o ajuste de referência para pixels reais na imagem A4
    ajuste_x_pixels = ajuste_x_ref * ticket_properties['scale_factor_x']
    ajuste_y_pixels = ajuste_y_ref * ticket_properties['scale_factor_y']
    
    # 1. Posição Top-Left do Campo (Base do Slot + Ref do Campo + Ajuste Individual)
    x_scaled = slot_start_x + (x_ref * ticket_properties['scale_factor_x']) + ajuste_x_pixels
    y_scaled = slot_start_y + (y_ref * ticket_properties['scale_factor_y']) + ajuste_y_pixels
    
    # 2. Dimensões do Campo (apenas escalonadas)
    w_scaled = w_ref * ticket_properties['scale_factor_x']
    h_scaled = h_ref * ticket_properties['scale_factor_y']
    
    return x_scaled, y_scaled, w_scaled, h_scaled

def draw_ticket_on_a4_slot(draw, slot_index, bilhete_contador, date_str, ticket_properties):
    """
    Desenha os números de um bilhete em um slot específico da imagem A4,
    aplicando o ajuste de coordenadas individual por campo.
    """
    black = (0, 0, 0)
    
    col = slot_index % GRID_COLS
    row = slot_index // GRID_COLS # Índice da fileira (0, 1, 2, 3, 4)
    
    # Coordenada de início do slot na imagem A4 (BASE - SEM AJUSTE DE SLOT AQUI)
    slot_start_x = col * ticket_properties['slot_width']
    slot_start_y = row * ticket_properties['slot_height']

    # 2. Gerar as 3 sequências numéricas (4 dígitos)
    try:
        seq1, seq2, seq3 = gerar_sequencia_unica()
    except RecursionError:
        raise RecursionError("Combinações únicas esgotadas.")
        
    # --- Desenho das Sequências ---
    
    # SEQ1
    x, y, w, h = get_scaled_field_dims('CAMPO_SEQ1', slot_index, slot_start_x, slot_start_y, ticket_properties)
    draw_text_centered(draw, seq1, ticket_properties['main_font'], black, x, y, w, h)

    # SEQ2
    x, y, w, h = get_scaled_field_dims('CAMPO_SEQ2', slot_index, slot_start_x, slot_start_y, ticket_properties)
    draw_text_centered(draw, seq2, ticket_properties['main_font'], black, x, y, w, h)

    # SEQ3
    x, y, w, h = get_scaled_field_dims('CAMPO_SEQ3', slot_index, slot_start_x, slot_start_y, ticket_properties)
    draw_text_centered(draw, seq3, ticket_properties['main_font'], black, x, y, w, h)

    # --- Desenho do Número do Bilhete ---
    ticket_number_str = f"{bilhete_contador:05d}"
    x, y, w, h = get_scaled_field_dims('CAMPO_NUM_BILHETE', slot_index, slot_start_x, slot_start_y, ticket_properties)
    draw_text_centered(draw, ticket_number_str, ticket_properties['small_font'], black, x, y, w, h)

    # --- Desenho da Data do Bilhete ---
    x, y, w, h = get_scaled_field_dims('CAMPO_DATA_BILHETE', slot_index, slot_start_x, slot_start_y, ticket_properties)
    draw_text_centered(draw, date_str, ticket_properties['small_font'], black, x, y, w, h)


def generate_and_save_pdf_threaded(num_pages, date_str, start_number, app_instance, progress_bar, btn_gerar):
    """Gera o PDF preenchendo 20 bilhetes na imagem A4 base por página."""
    global SEQUENCIAS_JA_USADAS
    
    SEQUENCIAS_JA_USADAS.clear()

    try:
        original_image = Image.open(IMAGE_PATH)
    except FileNotFoundError:
        messagebox.showerror("Erro", f"Arquivo de imagem base '{IMAGE_PATH}' não encontrado. Certifique-se de que está no mesmo diretório.")
        btn_gerar.configure(state="normal")
        return

    # 1. CÁLCULO DE ESCALA
    A4_LARGURA = original_image.width
    A4_ALTURA = original_image.height
    
    SLOT_WIDTH = A4_LARGURA / GRID_COLS
    SLOT_HEIGHT = A4_ALTURA / GRID_ROWS
    
    # Fator de escala em relação ao bilhete de referência (1200x700)
    scale_factor_x = SLOT_WIDTH / BILHETE_REF_LARGURA_PX
    scale_factor_y = SLOT_HEIGHT / BILHETE_REF_ALTURA_PX
    
    # Recalcula tamanhos de fonte
    new_main_font_size = int(MAIN_FONT_REF.size * scale_factor_y)
    new_small_font_size = int(SMALL_FONT_REF.size * scale_factor_y)
    
    try:
        main_font_scaled = ImageFont.truetype(FONT_PATH, new_main_font_size)
        small_font_scaled = ImageFont.truetype(FONT_PATH, new_small_font_size)
    except Exception:
        main_font_scaled = ImageFont.load_default()
        small_font_scaled = ImageFont.load_default()

    # Propriedades finais para a função de desenho
    ticket_properties = {
        'slot_width': SLOT_WIDTH,
        'slot_height': SLOT_HEIGHT,
        'scale_factor_x': scale_factor_x, 
        'scale_factor_y': scale_factor_y,
        'main_font': main_font_scaled,
        'small_font': small_font_scaled
    }
    
    # 2. Configuração do PDF
    file_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("Arquivos PDF", "*.pdf")],
        initialfile=PDF_FILENAME,
        title="Salvar PDF de Bilhetes Premiados"
    )

    if not file_path:
        btn_gerar.configure(state="normal")
        return

    # PDF em A4 Paisagem (tamanho padrão em pontos)
    pdf = FPDF(unit="pt", format="A4", orientation='L')
    pdf.set_auto_page_break(False)

    total_bilhetes = num_pages * CARTELAS_POR_PAGINA
    bilhete_contador = start_number

    # 3. Geração das Páginas
    for page_num in range(num_pages):
        page_image = original_image.copy().convert("RGB")
        draw = ImageDraw.Draw(page_image)
        
        pdf.add_page()
        
        try:
            for i in range(CARTELAS_POR_PAGINA):
                draw_ticket_on_a4_slot(draw, i, bilhete_contador, date_str, ticket_properties)
                
                bilhete_contador += 1
                
                progress = (bilhete_contador - start_number) / total_bilhetes
                app_instance.after(10, lambda p=progress: progress_bar.set(p))
            
            temp_img_path = f"temp_page_{page_num}.png"
            page_image.save(temp_img_path, quality=90)
            
            PAPER_WIDTH_PT = 841.89
            PAPER_HEIGHT_PT = 595.28
            pdf.image(temp_img_path, x=0, y=0, w=PAPER_WIDTH_PT, h=PAPER_HEIGHT_PT)
            
            os.remove(temp_img_path)
            
        except RecursionError:
            messagebox.showerror("Erro de Geração", "Combinações únicas esgotadas. Tente um número menor de bilhetes.")
            btn_gerar.configure(state="normal")
            return
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro durante o desenho: {e}")
            btn_gerar.configure(state="normal")
            return


    try:
        pdf.output(file_path)
        messagebox.showinfo("Sucesso", f"O PDF com {total_bilhetes} bilhetes (20 por página, arte A4) foi gerado e salvo em:\n{file_path}")
    except Exception as e:
        messagebox.showerror("Erro ao Salvar PDF", f"Não foi possível salvar o PDF: {e}\nVerifique as permissões da pasta.")
    finally:
        app_instance.after(10, lambda: progress_bar.set(0))
        app_instance.after(10, lambda: btn_gerar.configure(state="normal"))


# ----------------------------------------------------------------------
# ---- Interface Gráfica (CustomTkinter) ----
# ----------------------------------------------------------------------

def start_generation_in_thread():
    """Valida as entradas e inicia a geração do PDF em uma thread separada."""
    btn_gerar.configure(state="disabled")

    try:
        num_pages = int(entry_paginas.get())
        if num_pages <= 0:
            messagebox.showerror("Erro de Entrada", "Por favor, insira um número positivo de páginas.")
            btn_gerar.configure(state="normal")
            return
    except ValueError:
        messagebox.showerror("Erro de Entrada", "Quantidade de páginas inválida. Insira um número inteiro.")
        btn_gerar.configure(state="normal")
        return

    date_option = var_data.get()
    if date_option == 'current':
        date_str = date.today().strftime('%d/%m/%y')
    else:
        date_str = entry_data_manual.get()
        if not (len(date_str) == 8 and date_str[2] == '/' and date_str[5] == '/'):
            messagebox.showerror("Erro de Entrada", "Formato de data inválido. Use DD/MM/AA (Ex: 15/08/25).")
            btn_gerar.configure(state="normal")
            return
            
    try:
        start_number_str = entry_start_number.get()
        if start_number_str == "":
            start_number = 1
        else:
            start_number = int(start_number_str)
            if start_number < 1:
                messagebox.showerror("Erro de Entrada", "O número inicial deve ser 1 ou maior.")
                btn_gerar.configure(state="normal")
                return
    except ValueError:
        messagebox.showerror("Erro de Entrada", "Número inicial inválido. Insira um número inteiro positivo.")
        btn_gerar.configure(state="normal")
        return
        
    thread = threading.Thread(target=generate_and_save_pdf_threaded, 
                              args=(num_pages, date_str, start_number, app, progress_bar, btn_gerar))
    thread.start()

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Gerador de Bilhetes Pix Premiado (Arte A4)")
app.geometry("500x550") 
app.resizable(False, False)

title_label = ctk.CTkLabel(app, text="✨ Gerador de Bilhetes Pix Premiado (Arte A4 Base) ✨", font=ctk.CTkFont(size=18, weight="bold"))
title_label.pack(pady=20)

input_frame = ctk.CTkFrame(app)
input_frame.pack(padx=20, pady=10, fill="x", expand=False)

ctk.CTkLabel(input_frame, text="📄 Quantidade de Páginas (20 bilhetes/página):").pack(anchor='w', padx=15, pady=(10, 0))
entry_paginas = ctk.CTkEntry(input_frame, placeholder_text="Ex: 5 (Total de 100 Bilhetes)", width=300)
entry_paginas.pack(anchor='w', padx=15, pady=5)

ctk.CTkLabel(input_frame, text="🔢 Iniciar Bilhetes a partir de:").pack(anchor='w', padx=15, pady=(10, 0))
entry_start_number = ctk.CTkEntry(input_frame, placeholder_text="Deixe em branco para começar em 1", width=300)
entry_start_number.pack(anchor='w', padx=15, pady=5)

ctk.CTkLabel(input_frame, text="📅 Opção de Data do Sorteio:").pack(anchor='w', padx=15, pady=(10, 0))
var_data = ctk.StringVar(value='current')

def toggle_manual_date_entry():
    if var_data.get() == 'manual':
        entry_data_manual.configure(state='normal')
    else:
        entry_data_manual.configure(state='disabled')

radio_current = ctk.CTkRadioButton(input_frame, text="Data Atual", variable=var_data, value='current', command=toggle_manual_date_entry)
radio_current.pack(anchor='w', padx=15)

radio_manual = ctk.CTkRadioButton(input_frame, text="Inserir Data Manual (DD/MM/AA)", variable=var_data, value='manual', command=toggle_manual_date_entry)
radio_manual.pack(anchor='w', padx=15)

entry_data_manual = ctk.CTkEntry(input_frame, placeholder_text="Ex: 15/08/25", width=300, state='disabled')
entry_data_manual.pack(anchor='w', padx=15, pady=5)

btn_gerar = ctk.CTkButton(app, text="📥 Gerar e Salvar PDF", command=start_generation_in_thread, 
                          font=ctk.CTkFont(size=16, weight="bold"), height=40)
btn_gerar.pack(pady=20)

progress_bar = ctk.CTkProgressBar(app, orientation="horizontal", width=400)
progress_bar.set(0)
progress_bar.pack(pady=10)

app.mainloop()
