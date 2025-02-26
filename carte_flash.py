#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 21:20:57 2024

@author: fmenage
"""
import pdb
import random
import tkinter as tk
import time
import os
import csv
import pandas as pd
import socket
import pyttsx3
import platform
from gtts import gTTS
import threading

def is_connected():
    """Vérifie si l'ordinateur est connecté à Internet."""
    try:
        # Essayer de se connecter à un serveur (par exemple Google)
        socket.create_connection(("www.google.com", 80), timeout=2)
        return True
    except (socket.timeout, socket.gaierror):
        return False
    
def speak(text, lang="fr"):
    """Convertit un texte en parole et le joue sur macOS ou Windows."""
    
    #Si on est connecté à internet on passe par gTTs de google
    if(is_connected()):
        tts = gTTS(text=text, lang=lang)
        filename = "temp.mp3"
        tts.save(filename)
    
        # Détecter l'OS et utiliser la bonne commande
        if platform.system() == "Darwin":  # macOS
            os.system(f"afplay {filename}")
        elif platform.system() == "Windows":
            os.system(f"start {filename}")  # Utilise le lecteur par défaut sous Windows
        
        #os.remove(filename)  # Supprimer le fichier après lecture
        
    #Sinon on passe par un moteur interne pyttsx3
    else:
        print("pyttsx3")
        engine = pyttsx3.init()
        # Liste les voix disponibles
        voices = engine.getProperty('voices')
        
        # Choisir la voix correspondant à la langue
        for voice in voices:
            # Pour le français
            if lang in voice.languages[0]:
                engine.setProperty('voice', voice.id)
                break
            
        # Si hors ligne, utiliser pyttsx3 pour la lecture locale
        engine.setProperty('rate', 150)  # Ajuste la vitesse si nécessaire
        engine.setProperty('volume', 1)  # Volume max
        print("say")
        engine.say(text)

class Flashcard:
    def __init__(self, ID, question, answer, difficulty):
        self.ID = ID
        self.question = question
        self.answer = answer
        self.difficulty = difficulty
        self.first_time = True
        self.is_swapped = False

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
        
    def increase_difficulty(self):
        if(self.difficulty<2):
            self.difficulty = self.difficulty+1

    def decrease_difficulty(self):
        if(self.difficulty>0):
            self.difficulty = self.difficulty-1
            
    def swap_sides(self):
        if(self.is_swapped):
            self.is_swapped = False
        else:
            self.is_swapped = True

class Flashcards:
    def __init__(self):
        self.cards = []
        self.finished_cards = []
        self.is_swapped = False
        self.langue_pile = None
        self.langue_face = None

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
    
    def random_extraction(self, N, prop_easy=0.1, prop_medium = 0.1, prop_hard = 0.8):
        #On va extraire du jeu les cartes mais avec une proportion qui varie selon la difficulité

        N0_voulu = int(prop_easy*N)
        N1_voulu = int(prop_medium*N)
        N2_voulu = int(prop_hard*N)
        
        #Quand la somme ne fait pas le nombre total de cartes voulu
        #on comble le manque avec des cartes faciles pour qu'il y ait bien N cartes tirées au total
        if(N0_voulu + N1_voulu + N2_voulu < N):
            N0_voulu += (N - (N0_voulu + N1_voulu + N2_voulu))

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
        
        # Agrandir la fenêtre principale
        self.master.geometry("900x700")

        # Style général plus grand
        big_font = ("Helvetica", 24)
        medium_font = ("Helvetica", 20)
        small_font = ("Helvetica", 18)

        self.label = tk.Label(master, text="", font=big_font)
        self.label.pack(pady=30)

        self.answer_entry = tk.Entry(master, font=medium_font, width=30)
        self.answer_entry.pack(pady=15, ipady=10)

        self.show_answer_button = tk.Button(master, text="👁 Afficher la réponse", command=self.show_answer, font=medium_font)
        self.show_answer_button.pack(pady=15, ipadx=20, ipady=10)

        #------
        self.response_label = tk.Label(master, text="", font=medium_font, fg="blue")
        self.response_label.pack(pady=15)

        button_frame = tk.Frame(master)
        button_frame.pack(pady=15)

        self.correct_button = tk.Button(button_frame, text="✅ Correct", command=self.on_correct_click, font=medium_font, bg="lightgreen", width=10)
        self.correct_button.pack(side=tk.LEFT, padx=20, ipadx=10, ipady=10)

        self.faux_button = tk.Button(button_frame, text="❌ Faux", command=self.on_faux_click, font=medium_font, bg="lightcoral", width=10)
        self.faux_button.pack(side=tk.LEFT, padx=20, ipadx=10, ipady=10)

        self.swap_button = tk.Button(master, text="↔ Inverser Question/Définition", command=self.flashcards.swap_all_sides, font=medium_font)
        self.swap_button.pack(pady=30, ipadx=20, ipady=10)

        self.score_label = tk.Label(master, text="", font=small_font, fg="gray")
        self.score_label.pack(pady=15)
        self.score = 0
        self.nb_questions = 0
        self.update_score()

        self.timer_label = tk.Label(master, text="", font=small_font, fg="gray")
        self.timer_label.pack(pady=15)
        self.update_timer()
        
        self.speaker_button = None

        self.load_next_card()
        self.master.bind('<Return>', self.handle_enter_key)
        

    def load_next_card(self):
        
        if self.speaker_button is not None:
            self.speaker_button.pack_forget()
            self.speaker_button = None
        
        self.current_card = self.flashcards.get_first_card()
        
        if not self.current_card:
            self.label.config(text="Jeu fini !")
            self.save_difficulty(self.data,self.file_path_save)
            return None
        
        if self.current_card:
            if(self.current_card.is_swapped):
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
            if(self.current_card.is_swapped):
                self.response_label.config(text=self.current_card.answer)
            else:
                self.response_label.config(text=self.current_card.question)
        
        if not self.speaker_button:
            self.speaker_button = tk.Button(self.master, text="🔊", font=("Helvetica", 20), command = self.speak_current_answer)
            self.speaker_button.pack(pady=15, ipadx=10, ipady=10)

    def speak_current_answer(self):
        
        
        
        if self.current_card:
            if(self.current_card.is_swapped):
                thread = threading.Thread(target=speak, args=(self.current_card.answer,self.flashcards.langue_face))
            else:
                thread = threading.Thread(target=speak, args=(self.current_card.question,self.flashcards.langue_pile))
        
        thread.start()
        
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
            
        f = open(file_path_csv, 'w')
        f.write("#langue_pile=\"" + self.flashcards.langue_pile + "\"\n")
        f.write("#langue_face=\"" + self.flashcards.langue_face + "\"\n")
        df.to_csv(f, index=False, sep=";")
        f.close()


            
def read_flashcards_from_csv(file_path_csv, taille_jeu, prop_easy, prop_medium, prop_hard, subset_start = None, subset_stop = None):
    
    #Le jeu avec lequel on va jouer
    flashcards = Flashcards()

    #Par défaut, on met tout en français
    langue_pile = "fr"
    langue_face = "fr"
    
    #On lit les métadonnées s'il y en a 
    with open(file_path_csv, "r") as f:
        for _ in range(10):  #On lit les métadonnées dans les 10 premières lignes
            line = f.readline()
            if line.startswith("#langue_pile"):
                langue_pile = line.split('=')[1].strip().strip('"')
            elif line.startswith("#langue_face"):
                langue_face = line.split('=')[1].strip().strip('"')
    
    flashcards.langue_pile = langue_pile
    flashcards.langue_face = langue_face
    
    #On lit le contenu
    df = pd.read_csv(file_path_csv, sep=";", comment = "#")
    
    for index, row in df.iterrows():
        #On selectionne le subset : par exemple les cartes de 0 à 100
        if( subset_start != None and subset_stop != None):
            if(index>= subset_start and index< subset_stop):
                flashcards.add_card(index, row["Pile"], row["Face"], int(row["Difficulté"]))
        else:
            flashcards.add_card(index, row["Pile"], row["Face"], row["Difficulté"])
            
    if(flashcards.get_nb_mots_restants()>taille_jeu):
        #On extrait le nombre de cartes demandé
        flashcards.random_extraction(taille_jeu, prop_easy, prop_medium, prop_hard)
    else:
        #Si le nb de cartes demandé est inférieur au nb de cartes disponibles on mélange juste le jeu
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
    
def main(file_path_csv, swap=0, nb_cartes=20, subset_start=None, subset_stop=None, prop_easy=0.1, prop_medium=0.1, prop_hard=0.8):

    flashcards, df = read_flashcards_from_csv(file_path_csv, nb_cartes, prop_easy, prop_medium, prop_hard, subset_start, subset_stop)
    if(swap):
        flashcards.swap_all_sides()
        
    if not flashcards.cards:
        print("Aucune flashcard disponible. Vérifiez le contenu du fichier.")
        return

    root = tk.Tk()
    root.title("Flashcards App")
    app = FlashcardsApp(root, flashcards, df, file_path_csv)
    root.mainloop()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Jeu de flashcards')
    parser.add_argument('--fp', default = "dico/test.csv", metavar='',help='path to dico csv')
    parser.add_argument('--swap', default = 0, type=int, help="swap ou pas les questions")
    parser.add_argument('--nb_cartes', default=20, type=int, help="nb de cartes")
    parser.add_argument('--subset_start', default=None, type=int, help="debut du subet")
    parser.add_argument('--subset_stop', default=None, type=int, help="fin du subset")
    parser.add_argument('--prop_easy',  default = 0.1, type=float, help = "proportion de cartes faciles")
    parser.add_argument('--prop_medium',  default = 0.1, type=float, help = "proportion de cartes faciles")
    parser.add_argument('--prop_hard',  default = 0.8, type=float, help = "proportion de cartes faciles")

    args = parser.parse_args()

    if( (args.subset_start != None) and (args.subset_stop != None) ):
        if(args.subset_start > args.subset_stop):
            print("Error : subset_start > subset_stop. Ignoring subsets")
            args.subset_start = None
            args.subset_stop = None
    
    if(args.prop_easy + args.prop_medium + args.prop_hard != 1.0):
        raise ValueError("Somme des proportions de diffulté différent de 1")
        args.prop_easy = 0.1
        args.prop_medium = 0.1
        args.prop_hard = 0.8

    
    main(args.fp, swap=args.swap, nb_cartes=args.nb_cartes, subset_start=args.subset_start, subset_stop=args.subset_stop, prop_easy = args.prop_easy, prop_medium = args.prop_medium, prop_hard = args.prop_hard)


#python carte_flash.py --fp dico/dico_allemand.csv --swap=0 --nb_cartes=10 --subset_start=0 --subset_stop=20