import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageDraw, ImageFont
import random
from fpdf import FPDF
import os
from datetime import date
import threading

# ---- Configurações do Bilhete e Layout ----
# Caminho da imagem do bilhete base
IMAGE_PATH = "BILHETE_RECENTE.jpg" 

# Posições dos campos de texto (x, y) - Canto superior esquerdo da caixa branca.
CAMPO_COORDENADAS = {
    'campo1': (530, 358),  # Leve ajuste para baixo no campo 1
    'campo2': (530, 428),  # Leve ajuste para baixo no campo 2
    'campo3': (530, 494),  # Leve ajuste para baixo no campo 3
    'numero_bilhete': (23, 490), # Leve ajuste para baixo no número
    'data_bilhete': (253, 490)
}

# Dimensões aproximadas dos campos brancos para centralização do texto (em pixels da imagem original)
CAMPO_LARGURA = 200
CAMPO_ALTURA = 65

# Configurações da Fonte
try:
    FONT_PATH = "C:\\Windows\\Fonts\\arialbd.ttf"  
    MAIN_FONT = ImageFont.truetype(FONT_PATH, 55)
    SMALL_FONT = ImageFont.truetype(FONT_PATH, 35)
except IOError:
    try:
        FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" 
        MAIN_FONT = ImageFont.truetype(FONT_PATH, 55)
        SMALL_FONT = ImageFont.truetype(FONT_PATH, 35)
    except IOError:
        MAIN_FONT = ImageFont.load_default() 
        SMALL_FONT = ImageFont.load_default()

# Configurações de layout no PDF (A4 em pontos)
BILHETE_ORIGINAL_LARGURA_PX = 886
BILHETE_ORIGINAL_ALTURA_PX = 600

# Dimensões da página A4 em pontos (Paisagem: Largura x Altura)
PAPER_WIDTH_PT = 841.89
PAPER_HEIGHT_PT = 595.28

# Define a grade para 4x4 para 16 bilhetes por página
GRID_COLS = 4  
GRID_ROWS = 4
CARTELAS_POR_PAGINA = GRID_COLS * GRID_ROWS

# Define uma margem de segurança fixa em pontos (Aproximadamente 7mm)
SAFE_MARGIN_PT = 20

# Define o espaçamento entre bilhetes como 0
SPACING_X = 0
SPACING_Y = 0

# MUDANÇA: Otimiza o tamanho dos bilhetes com base na largura do espaço útil
PROPORTION_BILHETE = BILHETE_ORIGINAL_LARGURA_PX / BILHETE_ORIGINAL_ALTURA_PX

# Calcula a largura do bilhete com base na largura útil da página
USABLE_WIDTH_PT = PAPER_WIDTH_PT - (2 * SAFE_MARGIN_PT)
BILHETE_RENDER_LARGURA = USABLE_WIDTH_PT / GRID_COLS

# Recalcula a altura do bilhete para manter a proporção
BILHETE_RENDER_ALTURA = BILHETE_RENDER_LARGURA / PROPORTION_BILHETE

# Calcula as margens para centralizar a grade inteira na página
TOTAL_RENDER_WIDTH = BILHETE_RENDER_LARGURA * GRID_COLS
TOTAL_RENDER_HEIGHT = BILHETE_RENDER_ALTURA * GRID_ROWS

MARGIN_X = SAFE_MARGIN_PT
MARGIN_Y = (PAPER_HEIGHT_PT - TOTAL_RENDER_HEIGHT) / 2

SEQUENCIAS_JA_USADAS = set()
PDF_FILENAME = "Grupo da Sorte.pdf"

# ---- Funções de Geração ----

def gerar_sequencia_unica():
    """Gera uma sequência de 3x4 números única e não repetida para os 3 campos."""
    while True:
        seq1 = f"{random.randint(0, 9999):04d}"
        seq2 = f"{random.randint(0, 9999):04d}"
        seq3 = f"{random.randint(0, 9999):04d}"
        combinacao = (seq1, seq2, seq3)
        if combinacao not in SEQUENCIAS_JA_USADAS:
            SEQUENCIAS_JA_USADAS.add(combinacao)
            return combinacao

def create_single_ticket_image(original_img_obj, ticket_number_str, ticket_date_str):
    """Gera uma única imagem de bilhete com todos os números e data preenchidos."""
    img = original_img_obj.copy()
    draw = ImageDraw.Draw(img)
    black = (0, 0, 0)
    seq1, seq2, seq3 = gerar_sequencia_unica()
    numeric_sequences = [seq1, seq2, seq3]

    pos_num_bilhete = CAMPO_COORDENADAS['numero_bilhete']
    bbox_num_bilhete = draw.textbbox((0, 0), ticket_number_str, font=SMALL_FONT)
    text_width_num_bilhete = bbox_num_bilhete[2] - bbox_num_bilhete[0]
    text_height_num_bilhete = bbox_num_bilhete[3] - bbox_num_bilhete[1]
    x_num_bilhete = pos_num_bilhete[0] + (CAMPO_LARGURA - text_width_num_bilhete) / 2
    y_num_bilhete = pos_num_bilhete[1] + (CAMPO_ALTURA - text_height_num_bilhete) / 2
    draw.text((x_num_bilhete, y_num_bilhete), ticket_number_str, font=SMALL_FONT, fill=black)

    pos_data_bilhete = CAMPO_COORDENADAS['data_bilhete']
    bbox_data_bilhete = draw.textbbox((0, 0), ticket_date_str, font=SMALL_FONT)
    text_width_data_bilhete = bbox_data_bilhete[2] - bbox_data_bilhete[0]
    text_height_data_bilhete = bbox_data_bilhete[3] - bbox_data_bilhete[1]
    x_data_bilhete = pos_data_bilhete[0] + (CAMPO_LARGURA - text_width_data_bilhete) / 2
    y_data_bilhete = pos_data_bilhete[1] + (CAMPO_ALTURA - text_height_data_bilhete) / 2
    draw.text((x_data_bilhete, y_data_bilhete), ticket_date_str, font=SMALL_FONT, fill=black)

    for i, seq in enumerate(numeric_sequences):
        pos_campo = CAMPO_COORDENADAS[f'campo{i+1}']
        bbox_campo = draw.textbbox((0, 0), seq, font=MAIN_FONT)
        text_width_campo = bbox_campo[2] - bbox_campo[0]
        text_height_campo = bbox_campo[3] - bbox_campo[1]
        x_campo = pos_campo[0] + (CAMPO_LARGURA - text_width_campo) / 2
        y_campo = pos_campo[1] + (CAMPO_ALTURA - text_height_campo) / 2
        draw.text((x_campo, y_campo), seq, font=MAIN_FONT, fill=black)
        
    return img

def generate_and_save_pdf_threaded(num_pages, date_str, start_number, app_instance, progress_bar, btn_gerar):
    """Função para gerar o PDF em uma thread separada."""
    try:
        original_image = Image.open(IMAGE_PATH)
    except FileNotFoundError:
        messagebox.showerror("Erro", f"Arquivo de imagem base '{IMAGE_PATH}' não encontrado. Por favor, verifique o nome e o caminho.")
        btn_gerar.configure(state="normal")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("Arquivos PDF", "*.pdf")],
        initialfile=PDF_FILENAME,
        title="Salvar PDF de Bilhetes Premiados"
    )

    if not file_path:
        messagebox.showinfo("Cancelado", "Geração de PDF cancelada pelo usuário.")
        btn_gerar.configure(state="normal")
        return

    pdf = FPDF(unit="pt", format="A4", orientation='L')
    pdf.set_auto_page_break(False)

    total_bilhetes = num_pages * CARTELAS_POR_PAGINA
    
    # MODIFICAÇÃO: Inicia a contagem com o número inicial fornecido
    bilhete_contador = start_number

    for page_num in range(num_pages):
        pdf.add_page()
        for i in range(CARTELAS_POR_PAGINA):
            ticket_number_str = f"{bilhete_contador:05d}"
            
            ticket_image = create_single_ticket_image(original_image, ticket_number_str, date_str)
            
            if ticket_image is None:
                messagebox.showerror("Erro", "Falha ao criar a imagem do bilhete. Verifique as coordenadas dos campos.")
                btn_gerar.configure(state="normal")
                return

            temp_img_path = f"temp_ticket_{bilhete_contador}.png"
            try:
                ticket_image.save(temp_img_path)
            except Exception as e:
                messagebox.showerror("Erro ao Salvar Imagem Temporária", f"Não foi possível salvar imagem temporária: {e}")
                btn_gerar.configure(state="normal")
                return

            col = i % GRID_COLS
            row = i // GRID_COLS
            
            # Posição calculada
            x_pos = MARGIN_X + col * (BILHETE_RENDER_LARGURA + SPACING_X)
            y_pos = MARGIN_Y + row * (BILHETE_RENDER_ALTURA + SPACING_Y)

            pdf.image(temp_img_path, x=x_pos, y=y_pos, w=BILHETE_RENDER_LARGURA, h=BILHETE_RENDER_ALTURA)
            os.remove(temp_img_path)
            
            # ATUALIZA O CONTADOR APÓS A CRIAÇÃO DO BILHETE
            bilhete_contador += 1
            
            app_instance.after(10, lambda: progress_bar.set((bilhete_contador - start_number) / total_bilhetes))

    try:
        pdf.output(file_path)
        messagebox.showinfo("Sucesso", f"O PDF foi gerado e salvo em:\n{file_path}")
    except Exception as e:
        messagebox.showerror("Erro ao Salvar PDF", f"Não foi possível salvar o PDF: {e}\nVerifique as permissões da pasta.")
    finally:
        app_instance.after(10, lambda: progress_bar.set(0))
        app_instance.after(10, lambda: btn_gerar.configure(state="normal"))

# ---- Interface Gráfica com CustomTkinter ----

def start_generation_in_thread():
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
            
    # NOVA LÓGICA: Obtém o número inicial do bilhete
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
app.title("Gerador de Bilhetes Pix Premiado")
app.geometry("500x520") # AUMENTADO O TAMANHO DA JANELA
app.resizable(False, False)

title_label = ctk.CTkLabel(app, text="✨ Gerador de Bilhetes Pix Premiado ✨", font=ctk.CTkFont(size=20, weight="bold"))
title_label.pack(pady=20)

input_frame = ctk.CTkFrame(app)
input_frame.pack(padx=20, pady=10, fill="x", expand=False)

ctk.CTkLabel(input_frame, text="🔢 Quantidade de Páginas:").pack(anchor='w', padx=15, pady=(10, 0))
entry_paginas = ctk.CTkEntry(input_frame, placeholder_text="Ex: 5", width=300)
entry_paginas.pack(anchor='w', padx=15, pady=5)

# NOVO CAMPO: Iniciar a contagem do bilhete
ctk.CTkLabel(input_frame, text="🔢 Iniciar Bilhetes a partir de:").pack(anchor='w', padx=15, pady=(10, 0))
entry_start_number = ctk.CTkEntry(input_frame, placeholder_text="Deixe em branco para começar em 1", width=300)
entry_start_number.pack(anchor='w', padx=15, pady=5)


ctk.CTkLabel(input_frame, text="📅 Opção de Data:").pack(anchor='w', padx=15, pady=(10, 0))
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




class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Cronograma de Estudos – Comissária de Voo (Nível Iniciante)", ln=True, align="C")
        self.ln(5)

    def chapter_title(self, title):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, ln=True)
        self.ln(2)

    def chapter_body(self, body):
        self.set_font("Arial", "", 11)
        self.multi_cell(0, 8, body)
        self.ln()
