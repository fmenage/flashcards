#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 21:20:57 2024

@author: fmenage
"""

import random
import tkinter as tk
import time
import os
import csv
import pandas as pd

class Flashcard:
    def __init__(self, ID, question, answer, difficulty):
        self.ID = ID
        self.question = question
        self.answer = answer
        self.difficulty = difficulty
        self.first_time = True

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
        
    def increase_difficulty(self):
        if(self.difficulty<2):
            self.difficulty = self.difficulty+1

    def decrease_difficulty(self):
        if(self.difficulty>0):
            self.difficulty = self.difficulty-1
            
    def swap_sides(self):
        self.question, self.answer = self.answer, self.question

class Flashcards:
    def __init__(self):
        self.cards = []
        self.finished_cards = []

    def add_card(self, ID, question, answer, difficulty):
        card = Flashcard(ID, question, answer, difficulty)
        self.cards.append(card)

    def add_complete_card(self, card):
        self.cards.append(card)
        
    def get_random_card(self):
        if not self.cards:
            return None

        random_card = random.choice(self.cards)
        return random_card

    def swap_all_sides(self):
        for card in self.cards:
            card.swap_sides()
            
    def get_first_card(self):
        if(self.cards):
            return self.cards.pop(0)
        else:
            return None
    
    def get_nb_mots_restants(self):
        return len(self.cards)
    
    def random_extraction(self, N):
        #On va extraire du jeu les cartes mais avec une proportion qui varie selon la difficulité
        prop_easy = 0.1
        prop_medium = 0.1
        prop_hard = 0.8
        N0_voulu = int(prop_easy*N)
        N1_voulu = int(prop_medium*N)
        N2_voulu = int(prop_hard*N)
        
        cards_difficulte_0 = [card for card in self.cards if card.difficulty==0]
        cards_difficulte_1 = [card for card in self.cards if card.difficulty==1]
        cards_difficulte_2 = [card for card in self.cards if card.difficulty==2]

        """
        if(len(cards_difficulte_0)<N0):
            nb_restant = N0-len(cards_difficulte_0)
            N0=len(cards_difficulte_0)
            #N1 = N1 + int(np.floor(nb_restant/2))
            #N2 = N2 + int(np.ceil(nb_restant/2))
        if(len(cards_difficulte_1)<N1):
            nb_restant = N1-len(cards_difficulte_1)
            N1 = len(cards_difficulte_1)
            N2 = max(N2, len(cards_difficulte_2))
        if(len(cards_difficulte_2)<N2):
            N2 = len(cards_difficulte_1)
        """
        N0_dispo = len(cards_difficulte_0)
        N1_dispo = len(cards_difficulte_1)
        N2_dispo = len(cards_difficulte_2)
        
        if(N2_voulu>N2_dispo):
            delta = N2_voulu-N2_dispo
            N1_voulu = N1_voulu + delta
        if(N1_voulu>N1_dispo):
            delta = N1_voulu-N1_dispo
            N0_voulu = N0_voulu + delta
            
        N0 = min(N0_voulu, N0_dispo)
        N1 = min(N1_voulu, N1_dispo)
        N2 = min(N2_voulu, N2_dispo)
        
        cards_difficulte_0 = random.sample(cards_difficulte_0, N0)
        cards_difficulte_1 = random.sample(cards_difficulte_1, N1)
        cards_difficulte_2 = random.sample(cards_difficulte_2, N2)

        self.cards = cards_difficulte_0 + cards_difficulte_1 + cards_difficulte_2
        
    def shuffle(self):
        random.shuffle(self.cards)
        
class FlashcardsApp:
    def __init__(self, master, flashcards, df, file_path_save):
        
        self.data = df
        self.file_path_save = file_path_save
        self.start_time = time.time()
        self.master = master
        self.flashcards = flashcards
        self.current_card = None
        self.is_swapped = 0
        
        self.label = tk.Label(master, text="", font=("Helvetica", 16))
        self.label.pack(pady=20)

        self.answer_entry = tk.Entry(master, font=("Helvetica", 14))
        self.answer_entry.pack(pady=10)

        self.show_answer_button = tk.Button(master, text="Afficher la réponse", command=self.show_answer, font=("Helvetica", 14))
        self.show_answer_button.pack(pady=10)

        self.response_label = tk.Label(master, text="", font=("Helvetica", 14), fg="blue")
        self.response_label.pack(pady=10)

        button_frame = tk.Frame(master)
        button_frame.pack(pady=10)

        self.correct_button = tk.Button(button_frame, text="Correct", command=self.on_correct_click, font=("Helvetica", 14), highlightbackground="green", highlightcolor="green")
        self.correct_button.pack(side=tk.LEFT, padx=10)

        self.faux_button = tk.Button(button_frame, text="Faux", command=self.on_faux_click, font=("Helvetica", 14), highlightbackground="red", highlightcolor="red")
        self.faux_button.pack(side=tk.LEFT, padx=10)

        self.swap_button = tk.Button(master, text="Inverser Question/Définition", command=self.swap_sides_all, font=("Helvetica", 14))
        self.swap_button.pack(pady=20)

        self.score_label = tk.Label(master, text="", font=("Helvetica", 12), fg="gray")
        self.score_label.pack(pady=10)
        self.score = 0
        self.nb_questions = 0
        self.update_score()

        self.timer_label = tk.Label(master, text="", font=("Helvetica", 12), fg="gray")
        self.timer_label.pack(pady=10)
        self.update_timer()
        
        self.load_next_card()
        self.master.bind('<Return>', self.handle_enter_key)

    def load_next_card(self):
        self.current_card = self.flashcards.get_first_card()
        
        if not self.current_card:
            self.label.config(text="Jeu fini !")
            self.save_difficulty(self.data,self.file_path_save)
            return None
        
        if self.current_card:
            if(self.is_swapped):
                self.label.config(text=self.current_card.question)
            else:
                self.label.config(text=self.current_card.answer)
                
            self.response_label.config(text="")
            self.answer_entry.delete(0, tk.END)  # Effacer le contenu de la boîte de texte
        else:
            self.label.config(text="Fin des cartes")
            self.response_label.config(text="")
            self.answer_entry.config(state=tk.DISABLED)
            self.show_answer_button.config(state=tk.DISABLED)
            self.swap_button.config(state=tk.DISABLED)

    def on_correct_click(self):
        if self.current_card:
            if(self.current_card.first_time == True):
                self.current_card.decrease_difficulty()
            self.current_card.first_time = False
            self.flashcards.finished_cards.append(self.current_card)
            self.load_next_card()
            self.score += 1
            self.nb_questions += 1
            self.update_score()

    def on_faux_click(self):
        if self.current_card:
            if(self.current_card.first_time == True):
                self.current_card.increase_difficulty()

            self.current_card.first_time = False
            self.flashcards.add_complete_card(self.current_card)
            self.load_next_card()
            self.nb_questions += 1
            self.update_score()

    def show_answer(self):
        if self.current_card:
            if(self.is_swapped):
                self.response_label.config(text=self.current_card.answer)
            else:
                self.response_label.config(text=self.current_card.question)

    def swap_sides_all(self):
        self.flashcards.is_swapped = ~self.flashcards.is_swapped & 1

    def update_timer(self):
        elapsed_time = int(time.time() - self.start_time)
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        timer_text = f"Temps écoulé : {hours:02}:{minutes:02}:{seconds:02}"
        self.timer_label.config(text=timer_text)
        self.master.after(1000, self.update_timer)  # Met à jour le timer chaque seconde

    def update_score(self):
        score_text = f"Score : {self.score:02}/{self.nb_questions:02}"
        self.score_label.config(text=score_text)

    def update_mots_restants(self):
        mots_restants_text = "Mots restants : " + str(self.flashcards.get_nb_mots_restants)
        self.mots_restants.config(text=mots_restants_text)
        
    def handle_enter_key(self, event):
        self.show_answer()
        
    def save_difficulty(self, df, file_path_csv):
        for card in self.flashcards.finished_cards:
            df.loc[card.ID,"Difficulté"] = card.difficulty
            
        df.to_csv(file_path_csv, index=False, sep=";")


            
def read_flashcards_from_csv(file_path_csv, taille_jeu):
    flashcards = Flashcards()

    df = pd.read_csv(file_path_csv, sep=";")
    
    for index, row in df.iterrows():
        flashcards.add_card(index, row["Pile"], row["Face"], row["Difficulté"])
            
    if(flashcards.get_nb_mots_restants()>taille_jeu):
        flashcards.random_extraction(taille_jeu)
    else:
        flashcards.shuffle()


    return flashcards, df

def get_infos_from_csv(file_path_csv):
    df = pd.read_csv(file_path_csv)
    
def remove_duplicates(file_path_csv):
    df = pd.read_csv(file_path_csv)
    dff = df.drop_duplicates(subset=['Pile'], keep = "first")
    dff.to_csv(file_path_csv, index=False)
    
def convert_busuu_dico_to_csv(file_path_txt):
    
    nom_base, extension = os.path.splitext(file_path_txt)
    file_path_csv = nom_base + ".csv"
    
    # Écrire dans le fichier CSV
    with open(file_path_csv, 'w', newline='') as fichier_csv:
        writer = csv.writer(fichier_csv)
        writer.writerow(["Pile", "Face", "Difficulté"])
        
        with open(file_path_txt, 'r', encoding='utf-8') as file:
            
            lines = file.readlines()
    
            question = None
            answer = None
            knowledge = None
            for line in lines:
                stripped_line = line.strip()
        
                if not stripped_line:
                    continue
        
                if question is None:
                    question = stripped_line
                elif answer is None:
                    answer = stripped_line
                elif knowledge is None:
                    knowledge = stripped_line  
                    
                    difficulty = 2 #par défaut c'est difficile
                    writer.writerow([question, answer,difficulty])
                    knowledge = None
                    question = None
                    answer = None
            
def merge_two_csv(filepath_1, filepath_2):
    #ajoute les elts de 2 dans le dico 1
    df1 = pd.read_csv(filepath_1)
    df2 = pd.read_csv(filepath_2)
    
    df_tot = pd.concat([df1, df2])
    df_tot.drop_duplicates(subset=['Pile'], keep = "first")
    df_tot.to_csv(filepath_1, index=False)
    
def main():
    file_path_csv = "dico/dico_allemand.csv"
    nb_cartes = 20
    flashcards, df = read_flashcards_from_csv(file_path_csv, nb_cartes)

    if not flashcards.cards:
        print("Aucune flashcard disponible. Vérifiez le contenu du fichier.")
        return

    root = tk.Tk()
    root.title("Flashcards App")
    app = FlashcardsApp(root, flashcards, df, file_path_csv)
    root.mainloop()

if __name__ == "__main__":
    main()
