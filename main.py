import threading
import time
import random
import tkinter as tk
from tkinter import ttk, messagebox
import math


class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Jantar dos Filósofos")
        self.root.geometry("650x700")

        self.create_main_menu()

    def create_main_menu(self):
        """Cria o menu principal com as opções de algoritmo"""
        self.clear_window()

        lbl_title = ttk.Label(self.root, text="Jantar dos Filósofos", font=("Arial", 16, "bold"))
        lbl_title.pack(pady=20)

        lbl_subtitle = ttk.Label(self.root, text="Escolha o algoritmo para resolver o problema:")
        lbl_subtitle.pack(pady=10)

        btn_ingenua = ttk.Button(self.root, text="Solução Ingênua (Pode Deadlock)",
                                 command=lambda: self.start_simulation("ingenua"))
        btn_ingenua.pack(pady=5, fill=tk.X, padx=50)

        btn_timeout = ttk.Button(self.root, text="Solução com Timeout (Possível Starvation)",
                                 command=lambda: self.start_simulation("timeout"))
        btn_timeout.pack(pady=5, fill=tk.X, padx=50)

        btn_semaforo = ttk.Button(self.root, text="Solução com Semáforo (Ótima)",
                                  command=lambda: self.start_simulation("semaforo"))
        btn_semaforo.pack(pady=5, fill=tk.X, padx=50)

        btn_sair = ttk.Button(self.root, text="Sair", command=self.root.quit)
        btn_sair.pack(pady=20, fill=tk.X, padx=50)

    def clear_window(self):
        """Remove todos os widgets da janela principal"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def start_simulation(self, algorithm_type):
        """Inicia a simulação com o algoritmo selecionado"""
        self.clear_window()

        btn_voltar = ttk.Button(self.root, text="Voltar ao Menu", command=self.create_main_menu)
        btn_voltar.pack(pady=5, anchor=tk.NW)

        if algorithm_type == "ingenua":
            app = AppIngenua(self.root)
        elif algorithm_type == "timeout":
            app = AppTimeout(self.root)
        elif algorithm_type == "semaforo":
            app = AppSemaforo(self.root)

        # Adiciona um botão para reiniciar a simulação
        btn_reiniciar = ttk.Button(self.root, text="Reiniciar Simulação",
                                   command=lambda: self.restart_simulation(algorithm_type))
        btn_reiniciar.pack(pady=5)

    def restart_simulation(self, algorithm_type):
        """Reinicia a simulação com o mesmo algoritmo"""
        self.start_simulation(algorithm_type)


class FilosofoBase(threading.Thread):
    def __init__(self, id, garfos, app):
        threading.Thread.__init__(self)
        self.id = id
        self.garfos = garfos
        self.app = app
        self.vez_esquerda = id
        self.vez_direita = (id + 1) % 5
        self.refeicoes = 0
        self.estado = "Pensando"
        self.daemon = True

    def atualizar_estado(self, novo_estado):
        self.estado = novo_estado
        self.app.atualizar_filosofo(self.id, self.estado, self.refeicoes)

    def atualizar_garfo(self, garfo_id, estado):
        self.app.atualizar_garfo(garfo_id, estado)


class FilosofoIngenuo(FilosofoBase):
    def run(self):
        while self.refeicoes < 5:
            self.pensar()
            self.comer()

    def pensar(self):
        self.atualizar_estado("Pensando")
        time.sleep(random.uniform(1, 3))
        self.atualizar_estado("Faminto")

    def comer(self):
        self.garfos[self.vez_esquerda].acquire()
        self.atualizar_garfo(self.vez_esquerda, "ocupado")
        time.sleep(0.5)

        self.garfos[self.vez_direita].acquire()
        self.atualizar_garfo(self.vez_direita, "ocupado")

        self.atualizar_estado("Comendo")
        self.refeicoes += 1
        time.sleep(random.uniform(1, 2))

        self.garfos[self.vez_esquerda].release()
        self.garfos[self.vez_direita].release()
        self.atualizar_garfo(self.vez_esquerda, "livre")
        self.atualizar_garfo(self.vez_direita, "livre")


class FilosofoTimeout(FilosofoBase):
    def run(self):
        while self.refeicoes < 5:
            self.pensar()
            self.comer()

    def pensar(self):
        self.atualizar_estado("Pensando")
        time.sleep(random.uniform(1, 3))
        self.atualizar_estado("Faminto")

    def comer(self):
        while True:
            self.garfos[self.vez_esquerda].acquire()
            self.atualizar_garfo(self.vez_esquerda, "ocupado")

            tem_direito = self.garfos[self.vez_direita].acquire(timeout=1.0)
            if tem_direito:
                self.atualizar_garfo(self.vez_direita, "ocupado")
                break
            else:
                self.garfos[self.vez_esquerda].release()
                self.atualizar_garfo(self.vez_esquerda, "livre")
                time.sleep(random.uniform(0.5, 1.5))

        self.atualizar_estado("Comendo")
        self.refeicoes += 1
        time.sleep(random.uniform(1, 2))

        self.garfos[self.vez_esquerda].release()
        self.garfos[self.vez_direita].release()
        self.atualizar_garfo(self.vez_esquerda, "livre")
        self.atualizar_garfo(self.vez_direita, "livre")


class FilosofoSemaforo(FilosofoBase):
    def __init__(self, id, garfos, app, mutex):
        super().__init__(id, garfos, app)
        self.mutex = mutex

    def run(self):
        while self.refeicoes < 5:
            self.pensar()
            self.comer()

    def pensar(self):
        self.atualizar_estado("Pensando")
        time.sleep(random.uniform(1, 3))
        self.atualizar_estado("Faminto")

    def comer(self):
        with self.mutex:
            self.garfos[self.vez_esquerda].acquire()
            self.atualizar_garfo(self.vez_esquerda)