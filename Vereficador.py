import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import re
from collections import Counter
import os # Importado para manipulação de caminhos (path)

# --- 1. Função de Análise de Sequências ---
def analisar_sequencias(conteudo_arquivo: str) -> dict:
    """
    Extrai todas as sequências de 4 dígitos do texto e encontra as repetições.
    """
    if not conteudo_arquivo:
        return {}
        
    todas_as_sequencias = re.findall(r'\b\d{4}\b', conteudo_arquivo)
    contagem_sequencias = Counter(todas_as_sequencias)

    sequencias_repetidas = {
        seq: count 
        for seq, count in contagem_sequencias.items() 
        if count > 1
    }

    # Retorna o resultado ordenado por contagem (do mais repetido para o menos)
    return dict(sorted(sequencias_repetidas.items(), key=lambda item: item[1], reverse=True))


# --- 2. Classe para Construir a Janela (O "Painel") ---
class AnalisadorApp:
    def __init__(self, master):
        self.master = master
        master.title("Painel de Verificação de Sequências (4 Dígitos)")
        master.geometry("500x600")
        master.resizable(False, False)

        self.caminho_arquivo = None
        self.resultados_repetidos = None
        
        # Define o caminho da Área de Trabalho
        self.caminho_desktop = os.path.expanduser('~/Desktop') 

        # Título
        self.label_titulo = tk.Label(master, text="Verificador de Sequências Repetidas", font=("Helvetica", 14, "bold"))
        self.label_titulo.pack(pady=10)

        # Rótulo de status do arquivo
        self.label_status = tk.Label(master, text="Nenhum arquivo TXT carregado.", fg="red", font=("Helvetica", 10))
        self.label_status.pack(pady=5)

        # Botão para Enviar (Mandar) o Arquivo
        self.btn_carregar = tk.Button(master, text="1. Mandar Arquivo TXT", command=self.carregar_arquivo, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))
        self.btn_carregar.pack(pady=5)

        # Botão para Verificar
        self.btn_verificar = tk.Button(master, text="2. VERIFICAR", command=self.executar_verificacao, bg="#2196F3", fg="white", font=("Helvetica", 12, "bold"), state=tk.DISABLED)
        self.btn_verificar.pack(pady=10)
        
        # Botão para Salvar Resultados
        self.btn_salvar = tk.Button(master, text="3. BAIXAR/Salvar Repetições", command=self.salvar_resultados, bg="#FF9800", fg="white", font=("Helvetica", 10, "bold"), state=tk.DISABLED)
        self.btn_salvar.pack(pady=5)
        
        # Separador
        tk.Frame(master, height=2, bd=1, relief=tk.SUNKEN).pack(fill="x", padx=20, pady=5)
        
        # Área de Resultados
        self.label_resultado = tk.Label(master, text="RESULTADO DA ANÁLISE:", font=("Helvetica", 10, "bold"))
        self.label_resultado.pack(pady=5)
        
        # Área de texto com barra de rolagem
        self.area_resultado = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=50, height=15, font=("Courier", 10))
        self.area_resultado.pack(padx=20, pady=10)

    # --- Métodos de Controle ---
    def carregar_arquivo(self):
        self.caminho_arquivo = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")],
            title="Selecione o arquivo TXT"
        )
        
        if self.caminho_arquivo:
            nome_curto = os.path.basename(self.caminho_arquivo)
            self.label_status.config(text=f"Arquivo carregado: {nome_curto}", fg="darkgreen")
            self.btn_verificar.config(state=tk.NORMAL)
            self.btn_salvar.config(state=tk.DISABLED)
            self.area_resultado.delete('1.0', tk.END)
            self.area_resultado.insert(tk.END, f"Arquivo '{nome_curto}' pronto para verificação. Clique em VERIFICAR.")
            self.resultados_repetidos = None
        else:
            self.label_status.config(text="Nenhum arquivo TXT carregado.", fg="red")
            self.btn_verificar.config(state=tk.DISABLED)
            self.btn_salvar.config(state=tk.DISABLED)

    def executar_verificacao(self):
        if not self.caminho_arquivo:
            messagebox.showerror("Erro", "Por favor, carregue um arquivo TXT primeiro.")
            return

        try:
            with open(self.caminho_arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()

            self.resultados_repetidos = analisar_sequencias(conteudo)
            
            self.area_resultado.delete('1.0', tk.END)
            
            if self.resultados_repetidos:
                self.area_resultado.insert(tk.END, "🎉 SEQUÊNCIAS REPETIDAS ENCONTRADAS:\n\n")
                
                for seq, contagem in self.resultados_repetidos.items():
                    self.area_resultado.insert(tk.END, f"  Sequência: {seq} | Repetições: {contagem} vezes\n")
                    
                self.area_resultado.insert(tk.END, "\n--- ANÁLISE CONCLUÍDA. O botão 'BAIXAR' está ativo. ---")
                self.btn_salvar.config(state=tk.NORMAL)
            else:
                self.area_resultado.insert(tk.END, "🎉 Nenhuma sequência de 4 números se repetiu no arquivo fornecido.")
                self.btn_salvar.config(state=tk.DISABLED)

        except Exception as e:
            self.area_resultado.delete('1.0', tk.END)
            self.area_resultado.insert(tk.END, f"❌ ERRO AO PROCESSAR:\n{e}")
            messagebox.showerror("Erro de Processamento", f"Ocorreu um erro ao ler ou analisar o arquivo:\n{e}")
            self.btn_salvar.config(state=tk.DISABLED)
            self.resultados_repetidos = None
            
    # Método para o botão "BAIXAR/Salvar Repetições" (Alterado para salvar em TXT)
    def salvar_resultados(self):
        if not self.resultados_repetidos:
            messagebox.showwarning("Atenção", "Nenhum resultado para salvar. Por favor, execute a VERIFICAÇÃO primeiro.")
            return

        # Abre a janela para o usuário escolher o local e nome do arquivo
        caminho_salvar = filedialog.asksaveasfilename(
            # Define TXT como padrão e coloca TXT no Filetypes
            defaultextension=".txt", 
            filetypes=[("Arquivo de Texto", "*.txt"), ("Arquivo CSV", "*.csv")],
            title="Salvar Arquivo de Repetições",
            initialdir=self.caminho_desktop
        )

        if caminho_salvar:
            try:
                # ----------------------------------------------------
                # MUDANÇA APLICADA: Monta o conteúdo formatado como texto
                # ----------------------------------------------------
                conteudo_txt = "Relatório de Sequências Repetidas\n"
                conteudo_txt += "===================================\n"
                conteudo_txt += "Sequência | Repetições\n"
                conteudo_txt += "===================================\n"
                
                for seq, count in self.resultados_repetidos.items():
                    # Formata cada linha para alinhar (usando f-strings)
                    conteudo_txt += f"{seq:9} | {count}\n" 
                
                conteudo_txt += "===================================\n"
                conteudo_txt += f"Total de sequências repetidas: {len(self.resultados_repetidos)}\n"


                # Salva o conteúdo formatado no arquivo escolhido
                with open(caminho_salvar, 'w', encoding='utf-8') as f:
                    f.write(conteudo_txt)
                
                messagebox.showinfo("Sucesso", f"Resultados salvos com sucesso na Área de Trabalho (ou local escolhido) como:\n{os.path.basename(caminho_salvar)}")
                
            except Exception as e:
                messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo:\n{e}")


# --- 3. Execução Principal ---
if __name__ == "__main__":
    root = tk.Tk()
    app = AnalisadorApp(root)
    root.mainloop()