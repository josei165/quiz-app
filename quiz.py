# -*- coding: utf-8 -*-
"""
Quiz de Engenharia de Software
--------------------------------
Programa com interface gráfica (tkinter) que carrega perguntas de um
arquivo JSON estruturado, permite responder (seleção ou texto livre) e
depois conferir a resposta/gabarito com explicação.

Uso:
    python3 quiz_app.py [caminho_para_perguntas.json]

Se nenhum caminho for passado, o programa procura "perguntas.json" na
mesma pasta deste script.
"""
import json
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

WRAP = 760


class QuizApp(tk.Tk):
    def __init__(self, json_path):
        super().__init__()
        self.title("Quiz - Engenharia de Software")
        self.geometry("1100x720")
        self.minsize(900, 600)

        self.json_path = json_path
        self.data = {"sections": []}
        self.answers = {}       # qid -> resposta do usuário (str ou dict/list)
        self.revealed = {}      # qid -> True/False (se resposta já foi mostrada)
        self.flat_questions = []  # lista de (section_idx, question_idx, qid)
        self.current_index = 0

        # ---- Atributos declarados aqui para o Pylance não reclamar ----
        # (eles são de fato atribuídos dinamicamente conforme a pergunta
        # atual é renderizada, mas declará-los no __init__ dá ao analisador
        # de tipos algo para seguir)
        self.current_var: Optional[tk.StringVar] = None
        self.current_text_widget: Optional[tk.Text] = None
        self.tf_vars: list = []
        self._tf_vars_current: list = []
        self.result_frame: Optional[ttk.Frame] = None

        self._build_layout()
        self.load_json(self.json_path, silent=True)

    # ---------------------------------------------------------------
    # Layout geral
    # ---------------------------------------------------------------
    def _build_layout(self):
        # ---- Barra superior ----
        top = ttk.Frame(self, padding=8)
        top.pack(side="top", fill="x")

        ttk.Button(top, text="Abrir arquivo JSON...", command=self.open_file_dialog).pack(side="left")
        self.file_label = ttk.Label(top, text="Nenhum arquivo carregado", foreground="#555")
        self.file_label.pack(side="left", padx=10)

        self.score_label = ttk.Label(top, text="", font=("Segoe UI", 10, "bold"))
        self.score_label.pack(side="right")

        # ---- Corpo: sidebar + conteúdo ----
        body = ttk.Frame(self)
        body.pack(side="top", fill="both", expand=True)

        # Sidebar com árvore de seções/perguntas
        sidebar = ttk.Frame(body, width=300)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="Seções e Perguntas", font=("Segoe UI", 11, "bold")).pack(
            anchor="w", padx=8, pady=(8, 4))

        tree_frame = ttk.Frame(sidebar)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Conteúdo principal (scrollable)
        content_outer = ttk.Frame(body)
        content_outer.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(content_outer, highlightthickness=0, background="#ffffff")
        vscroll = ttk.Scrollbar(content_outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.content_frame = ttk.Frame(self.canvas, padding=20)
        self.content_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.content_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.content_window, width=e.width))
        self._bind_mousewheel(self.canvas)

        # ---- Barra inferior de navegação ----
        bottom = ttk.Frame(self, padding=8)
        bottom.pack(side="bottom", fill="x")
        self.prev_btn = ttk.Button(bottom, text="<< Anterior", command=self.go_prev)
        self.prev_btn.pack(side="left")
        self.reveal_btn = ttk.Button(bottom, text="Ver Resposta", command=self.reveal_answer)
        self.reveal_btn.pack(side="left", padx=8)
        self.next_btn = ttk.Button(bottom, text="Próxima >>", command=self.go_next)
        self.next_btn.pack(side="left")
        self.progress_label = ttk.Label(bottom, text="")
        self.progress_label.pack(side="right")

    def _bind_mousewheel(self, widget):
        def _on_mousewheel(event):
            delta = int(-1 * (event.delta / 120)) if event.delta else (1 if event.num == 5 else -1)
            self.canvas.yview_scroll(delta, "units")
        widget.bind_all("<MouseWheel>", _on_mousewheel)
        widget.bind_all("<Button-4>", _on_mousewheel)
        widget.bind_all("<Button-5>", _on_mousewheel)

    # ---------------------------------------------------------------
    # Carregamento de dados
    # ---------------------------------------------------------------
    def open_file_dialog(self):
        path = filedialog.askopenfilename(
            title="Selecione o arquivo JSON de perguntas",
            filetypes=[("JSON", "*.json"), ("Todos os arquivos", "*.*")])
        if path:
            self.load_json(path)

    def load_json(self, path, silent=False):
        if not path or not os.path.exists(path):
            if not silent:
                messagebox.showerror("Erro", f"Arquivo não encontrado:\n{path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception as e:
            messagebox.showerror("Erro ao carregar JSON", str(e))
            return

        self.json_path = path
        self.file_label.config(text=os.path.basename(path))
        self.answers.clear()
        self.revealed.clear()
        self._rebuild_tree()
        self.current_index = 0
        if self.flat_questions:
            self.show_question(0)
        self.update_score()

    def _rebuild_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.flat_questions = []
        for si, section in enumerate(self.data.get("sections", [])):
            sec_id = self.tree.insert("", "end", text=section.get("title", f"Seção {si+1}"), open=False)
            for qi, q in enumerate(section.get("questions", [])):
                idx = len(self.flat_questions)
                label = f"{qi+1}. {self._short_prompt(q.get('prompt',''))}"
                self.tree.insert(sec_id, "end", text=label, values=(idx,))
                self.flat_questions.append((si, qi, q.get("id", f"s{si}q{qi}")))

    @staticmethod
    def _short_prompt(text, limit=48):
        text = " ".join(text.split())
        return text if len(text) <= limit else text[:limit].rstrip() + "..."

    # ---------------------------------------------------------------
    # Navegação
    # ---------------------------------------------------------------
    def on_tree_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        values = self.tree.item(item, "values")
        if values:
            idx = int(values[0])
            self.show_question(idx)

    def go_prev(self):
        if self.current_index > 0:
            self.show_question(self.current_index - 1)

    def go_next(self):
        if self.current_index < len(self.flat_questions) - 1:
            self.show_question(self.current_index + 1)

    def get_current_question(self):
        if not self.flat_questions:
            return None, None
        si, qi, qid = self.flat_questions[self.current_index]
        q = self.data["sections"][si]["questions"][qi]
        return q, qid

    # ---------------------------------------------------------------
    # Renderização da pergunta
    # ---------------------------------------------------------------
    def show_question(self, index):
        self.current_index = index
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        si, qi, qid = self.flat_questions[index]
        section = self.data["sections"][si]
        q = section["questions"][qi]

        # Cabeçalho
        ttk.Label(self.content_frame, text=section["title"], font=("Segoe UI", 10, "italic"),
                  foreground="#777").pack(anchor="w")
        ttk.Label(self.content_frame, text=f"Pergunta {qi+1}", font=("Segoe UI", 11, "bold")).pack(
            anchor="w", pady=(0, 6))
        prompt_lbl = ttk.Label(self.content_frame, text=q["prompt"], font=("Segoe UI", 12),
                                wraplength=WRAP, justify="left")
        prompt_lbl.pack(anchor="w", pady=(0, 14))

        qtype = q.get("type")
        if qtype == "multiple_choice":
            self._render_multiple_choice(q, qid)
        elif qtype == "true_false_list":
            self._render_true_false_list(q, qid)
        elif qtype == "discursive":
            self._render_discursive(q, qid)
        else:
            ttk.Label(self.content_frame, text="[Tipo de pergunta desconhecido]").pack(anchor="w")

        # Área de resultado (preenchida ao clicar em "Ver Resposta")
        self.result_frame = ttk.Frame(self.content_frame)
        self.result_frame.pack(anchor="w", fill="x", pady=(16, 0))
        if self.revealed.get(qid):
            self._show_result(q, qid)

        self.progress_label.config(text=f"{index+1} / {len(self.flat_questions)}")
        self.prev_btn.config(state=("normal" if index > 0 else "disabled"))
        self.next_btn.config(state=("normal" if index < len(self.flat_questions) - 1 else "disabled"))
        self.canvas.yview_moveto(0)

    def _render_multiple_choice(self, q, qid):
        var = tk.StringVar(value=self.answers.get(qid, ""))
        self.current_var = var
        for opt in q["options"]:
            txt = f"{opt['key']})  {opt['text']}"
            rb = ttk.Radiobutton(self.content_frame, text=txt, value=opt["key"], variable=var,
                                  command=lambda v=var: self.answers.__setitem__(qid, v.get()))
            rb.pack(anchor="w", pady=2, fill="x")

    def _render_true_false_list(self, q, qid):
        stored = self.answers.get(qid)
        if not isinstance(stored, list) or len(stored) != len(q["items"]):
            stored = [""] * len(q["items"])
        self.tf_vars = stored
        vars_list = []
        for i, item_text in enumerate(q["items"]):
            row = ttk.Frame(self.content_frame)
            row.pack(anchor="w", fill="x", pady=4)
            lbl = ttk.Label(row, text=f"({i+1}) {item_text}", wraplength=WRAP - 140, justify="left")
            lbl.grid(row=0, column=0, sticky="w")
            v = tk.StringVar(value=self.tf_vars[i] if self.tf_vars[i] else "")
            vars_list.append(v)
            btn_frame = ttk.Frame(row)
            btn_frame.grid(row=0, column=1, sticky="e", padx=(10, 0))
            ttk.Radiobutton(btn_frame, text="V", value="V", variable=v,
                             command=lambda idx=i: self._set_tf_answer(qid, idx)).pack(side="left")
            ttk.Radiobutton(btn_frame, text="F", value="F", variable=v,
                             command=lambda idx=i: self._set_tf_answer(qid, idx)).pack(side="left")
            row.grid_columnconfigure(0, weight=1)
        self._tf_vars_current = vars_list
        self.answers[qid] = [v.get() for v in vars_list]

    def _set_tf_answer(self, qid, idx):
        vals = [v.get() for v in self._tf_vars_current]
        self.answers[qid] = vals

    def _render_discursive(self, q, qid):
        ttk.Label(self.content_frame, text="Escreva sua resposta:", font=("Segoe UI", 10, "bold")).pack(
            anchor="w", pady=(0, 4))
        text = tk.Text(self.content_frame, height=8, width=90, wrap="word", font=("Segoe UI", 11))
        text.pack(anchor="w", fill="x")
        existing = self.answers.get(qid, "")
        if existing:
            text.insert("1.0", existing)
        self.current_text_widget = text

        def save_text(_event=None):
            self.answers[qid] = text.get("1.0", "end-1c")
        text.bind("<KeyRelease>", save_text)
        text.bind("<FocusOut>", save_text)

    # ---------------------------------------------------------------
    # Revelar resposta
    # ---------------------------------------------------------------
    def reveal_answer(self):
        q, qid = self.get_current_question()
        if q is None or self.result_frame is None:
            return
        self.revealed[qid] = True
        for w in self.result_frame.winfo_children():
            w.destroy()
        self._show_result(q, qid)
        self.update_score()

    def _show_result(self, q, qid):
        if self.result_frame is None:
            return
        ttk.Separator(self.result_frame, orient="horizontal").pack(fill="x", pady=(6, 10))
        qtype = q.get("type")

        if qtype == "multiple_choice":
            user = self.answers.get(qid, "")
            correct = q["correct"]
            correct_text = next((o["text"] for o in q["options"] if o["key"] == correct), "")
            is_right = (user == correct)
            status = "✔ Você acertou!" if user else "Você não respondeu."
            if user and not is_right:
                status = "✘ Você errou."
            color = "#1a7f37" if is_right else ("#c0392b" if user else "#555")
            ttk.Label(self.result_frame, text=status, foreground=color,
                      font=("Segoe UI", 11, "bold")).pack(anchor="w")
            ttk.Label(self.result_frame, text=f"Resposta correta: {correct}) {correct_text}",
                      wraplength=WRAP, justify="left", font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 4))
            ttk.Label(self.result_frame, text=f"Explicação: {q.get('explanation','')}",
                      wraplength=WRAP, justify="left", foreground="#333").pack(anchor="w")

        elif qtype == "true_false_list":
            user_list = self.answers.get(qid, [])
            correct_list = q["correct"]
            n_right = sum(1 for u, c in zip(user_list, correct_list) if u == c)
            ttk.Label(self.result_frame, text=f"Você acertou {n_right} de {len(correct_list)} itens.",
                      font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
            for i, (item_text, corr) in enumerate(zip(q["items"], correct_list)):
                u = user_list[i] if i < len(user_list) else ""
                mark = "✔" if u == corr else ("✘" if u else "—")
                mcolor = "#1a7f37" if u == corr else ("#c0392b" if u else "#555")
                line = f"{mark} ({i+1}) Gabarito: {corr}" + (f"  |  Sua resposta: {u}" if u else "")
                ttk.Label(self.result_frame, text=line, foreground=mcolor,
                          wraplength=WRAP, justify="left").pack(anchor="w")
            ttk.Label(self.result_frame, text=f"Explicação: {q.get('explanation','')}",
                      wraplength=WRAP, justify="left", foreground="#333").pack(anchor="w", pady=(8, 0))

        elif qtype == "discursive":
            ttk.Label(self.result_frame, text="Resposta modelo / referência:",
                      font=("Segoe UI", 11, "bold")).pack(anchor="w")
            ttk.Label(self.result_frame, text=q.get("model_answer", ""), wraplength=WRAP,
                      justify="left", foreground="#333").pack(anchor="w", pady=(4, 0))

    # ---------------------------------------------------------------
    # Placar
    # ---------------------------------------------------------------
    def update_score(self):
        total_objective = 0
        correct_count = 0
        answered = 0
        for section in self.data.get("sections", []):
            for q in section["questions"]:
                qid = q["id"]
                if q["type"] == "multiple_choice":
                    total_objective += 1
                    if self.revealed.get(qid):
                        answered += 1
                        if self.answers.get(qid) == q["correct"]:
                            correct_count += 1
                elif q["type"] == "true_false_list":
                    total_objective += 1
                    if self.revealed.get(qid):
                        answered += 1
                        ul = self.answers.get(qid, [])
                        if ul == q["correct"]:
                            correct_count += 1
        if answered:
            self.score_label.config(text=f"Conferidas: {answered}/{total_objective}  |  Certas: {correct_count}")
        else:
            self.score_label.config(text=f"Perguntas objetivas: {total_objective}")


def main():
    default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "perguntas.json")
    json_path = sys.argv[1] if len(sys.argv) > 1 else default_path
    app = QuizApp(json_path)

    # Fix para tela em branco no WSLg: força um redraw depois que a janela
    # já foi mapeada na tela, contornando um bug conhecido do compositor.
    app.after(150, lambda: app.geometry(app.winfo_geometry()))

    app.mainloop()


if __name__ == "__main__":
    main()