import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageDraw, ImageFont
import random
from fpdf import FPDF
import os
import time
import threading
from datetime import date, timedelta
import math

# ----------------------------------------------------------------------
# ---- Configurações do Bilhete e Layout (Folha A4 Completa) ----
# ----------------------------------------------------------------------

# NOTE: Certifique-se de que o arquivo '01.jpg' esteja no mesmo diretório
IMAGE_PATH = "01.jpg"

GRID_COLS = 4
GRID_ROWS = 5
CARTELAS_POR_PAGINA = GRID_COLS * GRID_ROWS # 20 bilhetes por página

# Dimensões do bilhete individual (usadas como base para PROPORÇÃO)
BILHETE_REF_LARGURA_PX = 1200
BILHETE_REF_ALTURA_PX = 700

# --------------------------------------------------------------------------------
# CORDENADAS E DIMENSÕES DE CADA CAMPO EM PIXELS (NO BILHETE DE REFERÊNCIA 1200x700)
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
# --------------------------------------------------------------------------------

# 1. AJUSTE PARA O NÚMERO DE BILHETE (Ex: 00001, 00002)
AJUSTE_NUM_BILHETE_INDIVIDUAL = {
    0: (175, 170), 1: (120, 170), 2: (70, 170), 3: (17, 170),      # Fileira 1
    4: (170, 130), 5: (120, 130), 6: (70, 130), 7: (17, 130),      # Fileira 2
    8: (175, 90), 9: (120, 90), 10: (70, 90), 11: (17, 90),      # Fileira 3
    12: (175, 45), 13: (120, 45), 14: (70, 45), 15: (17, 45), # Fileira 4
    16: (175, 10), 17: (120, 10), 18: (70, 10), 19: (17, 10)      # Fileira 5
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

FIELD_ADJUSTMENT_MAP = {
    'CAMPO_NUM_BILHETE': AJUSTE_NUM_BILHETE_INDIVIDUAL,
    'CAMPO_DATA_BILHETE': AJUSTE_DATA_BILHETE_INDIVIDUAL,
    'CAMPO_SEQ1': AJUSTE_SEQ1_INDIVIDUAL,
    'CAMPO_SEQ2': AJUSTE_SEQ2_INDIVIDUAL,
    'CAMPO_SEQ3': AJUSTE_SEQ3_INDIVIDUAL,
}

# Definições de Fonte
try:
    FONT_PATH = "C:\\Windows\\Fonts\\arialbd.ttf" # Fonte comum em Windows
    MAIN_FONT_REF = ImageFont.truetype(FONT_PATH, 55)
    SMALL_FONT_REF = ImageFont.truetype(FONT_PATH, 35)
except IOError:
    MAIN_FONT_REF = ImageFont.load_default()
    SMALL_FONT_REF = ImageFont.load_default()

# ----------------------------------------------------------------------
# ---- Classe Principal da Aplicação e Lógica de Geração ----
# ----------------------------------------------------------------------

class GeradorDeBilhetes:
    def __init__(self, master):
        self.app = master
        # Usado para garantir que as combinações de (seq1, seq2, seq3) sejam únicas em toda a geração
        self.sequencias_ja_usadas = set()
        self.original_image = self._load_image_template()
        self.generation_thread = None

        # Variáveis de Controle da Geração
        self.is_paused = False
        self.pause_lock = threading.Lock()
        self.is_generating = False
        self.start_time = 0
        self.current_task_index = 0
        self.total_tasks = 0

        self.setup_ui()

    def _load_image_template(self):
        try:
            return Image.open(IMAGE_PATH)
        except FileNotFoundError:
            messagebox.showerror("Erro de Carregamento", f"Arquivo de imagem base '{IMAGE_PATH}' não encontrado. Certifique-se de que está no mesmo diretório.")
            # Cria uma imagem de placeholder em caso de falha (para evitar crash)
            return Image.new('RGB', (1000, 707), color='red') # A4 em proporção 4:3 aprox.

    def gerar_sequencia_unica(self):
        """Gera uma sequência de 3x4 números única e não repetida para os 3 campos."""
        max_attempts = 1000
        attempts = 0
        while attempts < max_attempts:
            # Gera 3 sequências de 4 dígitos
            seq1 = f"{random.randint(0, 9999):04d}"
            seq2 = f"{random.randint(0, 9999):04d}"
            seq3 = f"{random.randint(0, 9999):04d}"
            combinacao = (seq1, seq2, seq3)

            if combinacao not in self.sequencias_ja_usadas:
                self.sequencias_ja_usadas.add(combinacao)
                return combinacao
            attempts += 1
        raise RecursionError("Combinações únicas esgotadas (após 1000 tentativas).")

    def draw_text_centered(self, draw_obj, text, font, fill_color, top_left_x, top_left_y, width, height):
        """Desenha o texto centralizado dentro de uma caixa."""
        try:
            text_bbox = draw_obj.textbbox((0, 0), text, font=font)
        except AttributeError:
            # Fallback para PIL mais antigas que não possuem textbbox
            text_width, text_height = draw_obj.textsize(text, font=font)
            text_bbox = (0, 0, text_width, text_height)

        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        center_x = top_left_x + (width / 2)
        center_y = top_left_y + (height / 2)

        text_x = center_x - (text_width / 2)
        text_y = center_y - (text_height / 2)

        # Ajuste vertical fino para compensar o 'baseline' da fonte
        text_y += (text_bbox[1] / 2)

        draw_obj.text((text_x, text_y), text, font=font, fill=fill_color)

    def get_scaled_field_dims(self, field_name, slot_index, slot_start_x, slot_start_y, ticket_properties):
        """Calcula as dimensões e posição do campo escaladas, aplicando o ajuste individual."""
        x_ref, y_ref, w_ref, h_ref = REF_CAMPO_DIMENSIONS_AND_POS[field_name]

        adjustment_map = FIELD_ADJUSTMENT_MAP.get(field_name, {})
        ajuste_x_ref, ajuste_y_ref = adjustment_map.get(slot_index, (0, 0))

        ajuste_x_pixels = ajuste_x_ref * ticket_properties['scale_factor_x']
        ajuste_y_pixels = ajuste_y_ref * ticket_properties['scale_factor_y']

        x_scaled = slot_start_x + (x_ref * ticket_properties['scale_factor_x']) + ajuste_x_pixels
        y_scaled = slot_start_y + (y_ref * ticket_properties['scale_factor_y']) + ajuste_y_pixels

        w_scaled = w_ref * ticket_properties['scale_factor_x']
        h_scaled = h_ref * ticket_properties['scale_factor_y']

        return x_scaled, y_scaled, w_scaled, h_scaled

    def _draw_ticket_on_a4_slot(self, draw, slot_index, bilhete_contador, date_str, ticket_properties, seq1, seq2, seq3):
        """Desenha os números de um bilhete em um slot específico da imagem A4, usando sequências fornecidas."""
        black = (0, 0, 0)
        col = slot_index % GRID_COLS
        row = slot_index // GRID_COLS

        slot_start_x = col * ticket_properties['slot_width']
        slot_start_y = row * ticket_properties['slot_height']

        # SEQ1
        x, y, w, h = self.get_scaled_field_dims('CAMPO_SEQ1', slot_index, slot_start_x, slot_start_y, ticket_properties)
        self.draw_text_centered(draw, seq1, ticket_properties['main_font'], black, x, y, w, h)

        # SEQ2
        x, y, w, h = self.get_scaled_field_dims('CAMPO_SEQ2', slot_index, slot_start_x, slot_start_y, ticket_properties)
        self.draw_text_centered(draw, seq2, ticket_properties['main_font'], black, x, y, w, h)

        # SEQ3
        x, y, w, h = self.get_scaled_field_dims('CAMPO_SEQ3', slot_index, slot_start_x, slot_start_y, ticket_properties)
        self.draw_text_centered(draw, seq3, ticket_properties['main_font'], black, x, y, w, h)

        # Número do Bilhete
        ticket_number_str = f"{bilhete_contador:05d}"
        x, y, w, h = self.get_scaled_field_dims('CAMPO_NUM_BILHETE', slot_index, slot_start_x, slot_start_y, ticket_properties)
        self.draw_text_centered(draw, ticket_number_str, ticket_properties['small_font'], black, x, y, w, h)

        # Data do Bilhete
        x, y, w, h = self.get_scaled_field_dims('CAMPO_DATA_BILHETE', slot_index, slot_start_x, slot_start_y, ticket_properties)
        self.draw_text_centered(draw, date_str, ticket_properties['small_font'], black, x, y, w, h)


    def _generate_pdf_page(self, num_pages, date_str, start_number, file_path, ticket_properties, sequences_for_current_file):
        """Gera um único PDF com os bilhetes e coleta as sequências geradas."""
        pdf = FPDF(unit="pt", format="A4", orientation='L')
        pdf.set_auto_page_break(False)

        bilhete_contador = start_number

        for page_num in range(num_pages):
            # --- Controle de Pausa ---
            with self.pause_lock:
                while self.is_paused:
                    self.update_status(f"⏸️ Pausado. Bilhete: {bilhete_contador - 1} de {self.total_tasks * CARTELAS_POR_PAGINA}")
                    time.sleep(0.5)

            if self.original_image.mode != 'RGB':
                page_image = self.original_image.copy().convert("RGB")
            else:
                page_image = self.original_image.copy()

            draw = ImageDraw.Draw(page_image)

            pdf.add_page()

            for i in range(CARTELAS_POR_PAGINA):
                # 1. Gera a sequência única
                seq1, seq2, seq3 = self.gerar_sequencia_unica()

                # 2. Coleta a sequência
                sequences_for_current_file.append((seq1, seq2, seq3))

                # 3. Desenha no bilhete
                self._draw_ticket_on_a4_slot(draw, i, bilhete_contador, date_str, ticket_properties, seq1, seq2, seq3)
                bilhete_contador += 1

            self.current_task_index += 1
            self.update_progress_and_time()

            temp_img_path = f"temp_page_{os.getpid()}_{page_num}.png" # Usa PID para evitar conflito
            page_image.save(temp_img_path, quality=90)

            PAPER_WIDTH_PT = 841.89
            PAPER_HEIGHT_PT = 595.28
            pdf.image(temp_img_path, x=0, y=0, w=PAPER_WIDTH_PT, h=PAPER_HEIGHT_PT)

            os.remove(temp_img_path)

        # Salva o PDF
        pdf.output(file_path)

    def _save_sequences_to_txt(self, file_path, sequences_list):
        """Salva a lista de sequências geradas em um arquivo .txt."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("Relatório de Sequências Geradas\n")
                f.write("---------------------------------------\n")
                f.write("Seq. 1 | Seq. 2 | Seq. 3\n")
                f.write("---------------------------------------\n")
                for seq1, seq2, seq3 in sequences_list:
                    f.write(f"{seq1}     | {seq2}     | {seq3}\n")
        except Exception as e:
            print(f"Erro ao salvar arquivo TXT: {e}")
            # Não é um erro crítico, apenas loga no console.

    def update_progress_and_time(self):
        """Atualiza a barra de progresso e o tempo restante na thread principal."""
        if self.total_tasks > 0:
            progress = self.current_task_index / self.total_tasks
            self.app.after(10, lambda p=progress: self.progress_bar.set(p))

        if self.current_task_index > 0:
            elapsed = time.time() - self.start_time
            time_per_task = elapsed / self.current_task_index
            remaining_tasks = self.total_tasks - self.current_task_index
            etr_seconds = remaining_tasks * time_per_task
            
            etr_delta = timedelta(seconds=math.ceil(etr_seconds))
            etr_str = str(etr_delta)
            
            if ':' in etr_str: # Formata HH:MM:SS
                etr_display = etr_str.split('.')[0]
            else: # Trata casos de dias/horas (simplificado)
                etr_display = f"{int(etr_seconds)}s"
            
            status = f"Geração em Andamento | Tempo Estimado: {etr_display}"
        else:
            status = "Preparando Geração..."

        self.update_status(status)


    def update_status(self, status_text):
        """Atualiza o texto de status na thread principal."""
        self.app.after(10, lambda: self.status_label.configure(text=status_text))

    def start_multi_file_generation(self):
        """Valida entradas e inicia a geração multi-arquivo em uma thread."""
        if self.is_generating:
            messagebox.showinfo("Aviso", "A geração já está em andamento.")
            return

        try:
            num_files = int(self.entry_num_files.get())
            num_pages = int(self.entry_pages_per_file.get())

            if num_files <= 0 or num_pages <= 0:
                messagebox.showerror("Erro de Entrada", "Quantidade de arquivos e páginas deve ser maior que zero.")
                return
        except ValueError:
            messagebox.showerror("Erro de Entrada", "Quantidade de arquivos/páginas inválida. Insira números inteiros.")
            return

        # 1. Define a data
        date_option = self.var_data.get()
        if date_option == 'current':
            date_str = date.today().strftime('%d/%m/%y')
        else:
            date_str = self.entry_data_manual.get()
            if not (len(date_str) == 8 and date_str[2] == '/' and date_str[5] == '/'):
                messagebox.showerror("Erro de Entrada", "Formato de data inválido. Use DD/MM/AA (Ex: 15/08/25).")
                return

        # 2. Define o número inicial
        try:
            start_number_str = self.entry_start_number.get()
            start_number = int(start_number_str) if start_number_str else 1
            if start_number < 1:
                messagebox.showerror("Erro de Entrada", "O número inicial deve ser 1 ou maior.")
                return
        except ValueError:
            messagebox.showerror("Erro de Entrada", "Número inicial inválido. Insira um número inteiro positivo.")
            return

        # 3. Pergunta a pasta de destino
        save_dir = filedialog.askdirectory(title="Selecione a Pasta para Salvar os PDFs e TXTs")
        if not save_dir:
            return

        # 4. Inicia o Worker
        self.is_generating = True
        self.is_paused = False
        self.btn_gerar.configure(state="disabled")
        self.btn_pause.configure(state="normal")
        self.btn_continue.configure(state="disabled")

        self.sequencias_ja_usadas.clear() # Limpa o cache de sequências para uma nova geração

        args = (num_files, num_pages, date_str, start_number, save_dir)
        self.generation_thread = threading.Thread(target=self.generation_worker, args=args)
        self.generation_thread.start()


    def generation_worker(self, num_files, num_pages, date_str, start_number, save_dir):
        """Lógica que roda em uma thread separada para gerar os arquivos (PDF e TXT)."""

        # 1. Configurações e Cálculos de Escala (Realizado apenas uma vez)
        if not self.original_image:
            self.finalize_generation(False, "Erro: Imagem base não carregada.")
            return

        A4_LARGURA = self.original_image.width
        A4_ALTURA = self.original_image.height

        SLOT_WIDTH = A4_LARGURA / GRID_COLS
        SLOT_HEIGHT = A4_ALTURA / GRID_ROWS

        scale_factor_x = SLOT_WIDTH / BILHETE_REF_LARGURA_PX
        scale_factor_y = SLOT_HEIGHT / BILHETE_REF_ALTURA_PX

        new_main_font_size = int(MAIN_FONT_REF.size * scale_factor_y)
        new_small_font_size = int(SMALL_FONT_REF.size * scale_factor_y)

        try:
            main_font_scaled = ImageFont.truetype(FONT_PATH, new_main_font_size)
            small_font_scaled = ImageFont.truetype(FONT_PATH, new_small_font_size)
        except Exception:
            main_font_scaled = ImageFont.load_default()
            small_font_scaled = ImageFont.load_default()

        ticket_properties = {
            'slot_width': SLOT_WIDTH, 'slot_height': SLOT_HEIGHT,
            'scale_factor_x': scale_factor_x, 'scale_factor_y': scale_factor_y,
            'main_font': main_font_scaled, 'small_font': small_font_scaled
        }

        # 2. Execução da Geração Multi-Arquivo
        self.current_task_index = 0
        self.total_tasks = num_files * num_pages # Total de páginas a gerar
        self.start_time = time.time()
        current_ticket_number = start_number

        try:
            for file_num in range(1, num_files + 1):
                file_name = f"Bilhetes_Grupo_da_Sorte_Parte_{file_num:02d}.pdf"
                file_path = os.path.join(save_dir, file_name)
                txt_file_path = file_path.replace('.pdf', '_Sequencias.txt')

                file_start_number = current_ticket_number

                # Lista para coletar as sequências deste arquivo PDF específico
                sequences_for_current_file = []

                self.update_status(f"Iniciando PDF {file_num}/{num_files}...")

                # 1. Gera o PDF e coleta as sequências
                self._generate_pdf_page(num_pages, date_str, file_start_number, file_path, ticket_properties, sequences_for_current_file)

                # 2. Salva as sequências no arquivo TXT
                self._save_sequences_to_txt(txt_file_path, sequences_for_current_file)

                # 3. Atualiza o número inicial para o próximo arquivo
                current_ticket_number = file_start_number + (num_pages * CARTELAS_POR_PAGINA)

            self.finalize_generation(True, f"✅ Sucesso! {num_files} PDFs e {num_files} TXTs gerados na pasta:\n{save_dir}")

        except RecursionError:
            self.finalize_generation(False, "Erro de Geração: Combinações únicas esgotadas (3x4 dígitos). Tente um número menor de bilhetes.")
        except Exception as e:
            self.finalize_generation(False, f"Erro inesperado durante a geração: {e}")


    def finalize_generation(self, success, message):
        """Função para redefinir o estado da GUI após a geração (chamada na thread principal)."""
        self.is_generating = False
        self.is_paused = False

        self.app.after(10, lambda: self.btn_gerar.configure(state="normal"))
        self.app.after(10, lambda: self.btn_pause.configure(state="disabled"))
        self.app.after(10, lambda: self.btn_continue.configure(state="disabled"))
        self.app.after(10, lambda: self.progress_bar.set(0))
        self.app.after(10, lambda: self.update_status("Pronto para gerar!"))

        if success:
            self.app.after(10, lambda: messagebox.showinfo("Geração Concluída", message))
        else:
            self.app.after(10, lambda: messagebox.showerror("Geração Falhou", message))

    # ----------------------------------------------------------------------
    # ---- Funções de Controle (Pause/Continue) ----
    # ----------------------------------------------------------------------

    def toggle_pause(self):
        if self.is_generating:
            with self.pause_lock:
                self.is_paused = True
            self.btn_pause.configure(state="disabled")
            self.btn_continue.configure(state="normal")
            self.update_status("⏸️ Pausado")

    def toggle_continue(self):
        with self.pause_lock:
            self.is_paused = False
        self.btn_pause.configure(state="normal")
        self.btn_continue.configure(state="disabled")
        self.update_status("▶️ Retomando Geração...")


    # ----------------------------------------------------------------------
    # ---- Configuração da Interface Gráfica ----
    # ----------------------------------------------------------------------

    def toggle_manual_date_entry(self):
        if self.var_data.get() == 'manual':
            self.entry_data_manual.configure(state='normal')
        else:
            self.entry_data_manual.configure(state='disabled')

    def setup_ui(self):
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.app.title("Gerador de Bilhetes Pix Premiado (Upgrade)")
        self.app.geometry("550x700")
        self.app.resizable(False, False)

        # Título
        title_label = ctk.CTkLabel(self.app, text="🚀 Gerador de Bilhetes Multi-PDF (Arte A4 Base)",
                                     font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(20, 10))

        # Frame de Entrada
        input_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        input_frame.pack(padx=25, pady=10, fill="x", expand=False)

        # Configuração da Grade para Inputs (2 colunas)
        input_frame.columnconfigure(0, weight=1)
        input_frame.columnconfigure(1, weight=1)

        # --- Seção 1: Quantidades ---

        # Quantidade de Arquivos (Novo)
        ctk.CTkLabel(input_frame, text="📁 Quantidade de Arquivos PDF:").grid(row=0, column=0, sticky='w', padx=10, pady=(10, 0))
        self.entry_num_files = ctk.CTkEntry(input_frame, placeholder_text="Ex: 3 Arquivos", width=200)
        self.entry_num_files.insert(0, "1") # Valor padrão
        self.entry_num_files.grid(row=1, column=0, sticky='ew', padx=10, pady=(5, 10))

        # Páginas por Arquivo (Atualizado)
        ctk.CTkLabel(input_frame, text="📄 Páginas por Arquivo (20 bilhetes/página):").grid(row=0, column=1, sticky='w', padx=10, pady=(10, 0))
        self.entry_pages_per_file = ctk.CTkEntry(input_frame, placeholder_text="Ex: 50 Páginas", width=200)
        self.entry_pages_per_file.insert(0, "5") # Valor padrão
        self.entry_pages_per_file.grid(row=1, column=1, sticky='ew', padx=10, pady=(5, 10))

        # --- Seção 2: Numeração Inicial ---

        ctk.CTkLabel(input_frame, text="🔢 Iniciar Bilhetes a partir de:").grid(row=2, column=0, sticky='w', padx=10, pady=(10, 0), columnspan=2)
        self.entry_start_number = ctk.CTkEntry(input_frame, placeholder_text="Deixe em branco para começar em 1", width=420)
        self.entry_start_number.grid(row=3, column=0, sticky='ew', padx=10, pady=(5, 10), columnspan=2)

        # --- Seção 3: Data ---
        date_frame = ctk.CTkFrame(input_frame)
        date_frame.grid(row=4, column=0, sticky='ew', padx=10, pady=(10, 10), columnspan=2)

        ctk.CTkLabel(date_frame, text="📅 Opção de Data do Sorteio:").pack(anchor='w', padx=15, pady=(10, 0))
        self.var_data = ctk.StringVar(value='current')

        radio_current = ctk.CTkRadioButton(date_frame, text="Data Atual", variable=self.var_data, value='current', command=self.toggle_manual_date_entry)
        radio_current.pack(anchor='w', padx=15)

        radio_manual = ctk.CTkRadioButton(date_frame, text="Inserir Data Manual (DD/MM/AA)", variable=self.var_data, value='manual', command=self.toggle_manual_date_entry)
        radio_manual.pack(anchor='w', padx=15)

        self.entry_data_manual = ctk.CTkEntry(date_frame, placeholder_text="Ex: 15/08/25", width=380, state='disabled')
        self.entry_data_manual.pack(anchor='w', padx=15, pady=10)

        # --- Seção 4: Botão Gerar Principal ---
        self.btn_gerar = ctk.CTkButton(self.app, text="🚀 INICIAR GERAÇÃO E SALVAR", command=self.start_multi_file_generation,
                                         font=ctk.CTkFont(size=18, weight="bold"), height=50, fg_color="#006400", hover_color="#008000")
        self.btn_gerar.pack(pady=(20, 10), padx=25, fill="x")

        # --- Seção 5: Progresso e Controle ---
        progress_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        progress_frame.pack(padx=25, pady=(10, 20), fill="x")

        self.status_label = ctk.CTkLabel(progress_frame, text="Pronto para gerar!", font=ctk.CTkFont(size=14))
        self.status_label.pack(anchor='w', pady=(5, 5))

        self.progress_bar = ctk.CTkProgressBar(progress_frame, orientation="horizontal", height=20)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 15))

        # Botões de Controle (Pause/Continue)
        control_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        control_frame.pack(padx=25, pady=(0, 20), fill="x")
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)

        self.btn_pause = ctk.CTkButton(control_frame, text="⏸️ Pausar", command=self.toggle_pause,
                                             fg_color="orange", hover_color="darkorange", state="disabled")
        self.btn_pause.grid(row=0, column=0, sticky='ew', padx=(0, 10))

        self.btn_continue = ctk.CTkButton(control_frame, text="▶️ Continuar", command=self.toggle_continue,
                                             fg_color="green", hover_color="darkgreen", state="disabled")
        self.btn_continue.grid(row=0, column=1, sticky='ew', padx=(10, 0))


if __name__ == "__main__":
    app = ctk.CTk()
    GeradorDeBilhetes(app)
    app.mainloop()
