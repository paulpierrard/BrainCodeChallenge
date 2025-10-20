import json
import random
from collections import Counter

def solve(dataset_txt):
    """
    Fonction principale qui résout le problème de reconstruction d'image.
    
    DIFFÉRENCE PRINCIPALE AVEC L'ANCIEN CODE:
    - Ancien: Approche Monte Carlo (teste des actions aléatoires)
    - Nouveau: Approche déterministe et intelligente (analyse systématique)
    """
    
    # Lecture des données du dataset
    dataset = json.loads(dataset_txt)
    
    target_grid = dataset['grid']           # Grille cible à reproduire
    max_actions = dataset['maxActions']     # Nombre max d'actions autorisées
    max_jokers = dataset['maxJokers']       # Nombre max de JOKERs
    max_joker_size = dataset['maxJokerSize'] # Surface max par JOKER
    grid_height = len(target_grid)          # Hauteur de la grille
    grid_width = len(target_grid[0])        # Largeur de la grille

    actions = []  # Liste des actions à effectuer
    current_grid = [[0 for _ in range(grid_width)] for _ in range(grid_height)]  # Grille de travail (vide au départ)
    jokers_used = 0  # Compteur de JOKERs utilisés

    # ========================================
    # STRATÉGIE 1: Remplissage initial intelligent
    # ========================================
    # DIFFÉRENCE: L'ancien code partait d'une grille vide (tout à 0)
    # Le nouveau code remplit d'abord avec la couleur dominante
    
    # Compter la fréquence de chaque couleur (sauf 0)
    color_counts = Counter()
    for row in target_grid:
        for color in row:
            if color != 0:
                color_counts[color] += 1
    
    # Si on trouve une couleur dominante, remplir toute la grille avec
    if color_counts:
        most_common_color = color_counts.most_common(1)[0][0]
        actions.append(f'RECT 0 0 {grid_width-1} {grid_height-1} {most_common_color}')
        # Mettre à jour la grille courante
        for y in range(grid_height):
            for x in range(grid_width):
                current_grid[y][x] = most_common_color

    # ========================================
    # STRATÉGIE 2: Fonction pour trouver le meilleur rectangle
    # ========================================
    # DIFFÉRENCE: L'ancien code testait des rectangles aléatoires
    # Le nouveau explore systématiquement toutes les possibilités
    
    def find_best_rect(grid, target):
        """
        Trouve le meilleur rectangle RECT qui améliore le plus la grille.
        
        Retourne: (action, nouvelle_grille, score_amélioration)
        """
        best_score = 0          # Meilleure amélioration trouvée
        best_action = None      # Meilleure action trouvée
        best_new_grid = None    # État de la grille après cette action
        
        # Tester toutes les couleurs possibles (0 à 7)
        for color in range(8):
            # Tester tous les rectangles possibles
            for y1 in range(grid_height):
                for x1 in range(grid_width):
                    # Limiter la taille pour éviter trop de calculs
                    for y2 in range(y1, min(y1 + 20, grid_height)):
                        for x2 in range(x1, min(x1 + 20, grid_width)):
                            
                            # Calculer l'amélioration apportée par ce rectangle
                            improvement = 0
                            for y in range(y1, y2 + 1):
                                for x in range(x1, x2 + 1):
                                    # +1 si on corrige un pixel incorrect
                                    if grid[y][x] != target[y][x] and target[y][x] == color:
                                        improvement += 1
                                    # -1 si on casse un pixel correct
                                    elif grid[y][x] == target[y][x] and target[y][x] != color:
                                        improvement -= 1
                            
                            # Garder le meilleur rectangle trouvé
                            if improvement > best_score:
                                best_score = improvement
                                best_action = f'RECT {x1} {y1} {x2} {y2} {color}'
                                
                                # Simuler l'application du rectangle
                                sim_grid = [row[:] for row in grid]
                                for y in range(y1, y2 + 1):
                                    for x in range(x1, x2 + 1):
                                        sim_grid[y][x] = color
                                best_new_grid = sim_grid
        
        return best_action, best_new_grid, best_score

    # ========================================
    # STRATÉGIE 3: Fonction pour trouver le meilleur JOKER
    # ========================================
    # DIFFÉRENCE: L'ancien code testait des JOKERs aléatoires
    # Le nouveau trouve le JOKER qui corrige le plus d'erreurs
    
    def find_best_joker(grid, target, max_size):
        """
        Trouve le meilleur JOKER (zone à copier exactement depuis la cible).
        
        Retourne: (action, nouvelle_grille, nombre_corrections)
        """
        best_score = 0
        best_action = None
        best_new_grid = None
        
        # Tester toutes les positions et tailles possibles
        for y1 in range(grid_height):
            for x1 in range(grid_width):
                for y2 in range(y1, grid_height):
                    for x2 in range(x1, grid_width):
                        # Vérifier que la surface ne dépasse pas la limite
                        area = (x2 - x1 + 1) * (y2 - y1 + 1)
                        if area > max_size:
                            continue
                        
                        # Compter combien de pixels seraient corrigés
                        corrections = 0
                        for y in range(y1, y2 + 1):
                            for x in range(x1, x2 + 1):
                                if grid[y][x] != target[y][x]:
                                    corrections += 1
                        
                        # Garder le meilleur JOKER
                        if corrections > best_score:
                            best_score = corrections
                            best_action = f'JOKER {x1} {y1} {x2} {y2}'
                            
                            # Simuler l'application du JOKER
                            sim_grid = [row[:] for row in grid]
                            for y in range(y1, y2 + 1):
                                for x in range(x1, x2 + 1):
                                    sim_grid[y][x] = target[y][x]
                            best_new_grid = sim_grid
        
        return best_action, best_new_grid, best_score

    # ========================================
    # BOUCLE PRINCIPALE D'OPTIMISATION
    # ========================================
    # DIFFÉRENCE: L'ancien code faisait 100 tirages aléatoires par itération
    # Le nouveau compare intelligemment RECT vs JOKER et choisit le meilleur
    
    while len(actions) < max_actions:
        # Vérifier si la grille est parfaite
        errors = sum(1 for y in range(grid_height) for x in range(grid_width) 
                    if current_grid[y][x] != target_grid[y][x])
        if errors == 0:
            break  # Succès! On arrête
        
        # Chercher le meilleur rectangle RECT
        rect_action, rect_grid, rect_score = find_best_rect(current_grid, target_grid)
        
        # Chercher le meilleur JOKER (si on en a encore)
        joker_action, joker_grid, joker_score = None, None, 0
        if jokers_used < max_jokers:
            joker_action, joker_grid, joker_score = find_best_joker(current_grid, target_grid, max_joker_size)
        
        # ========================================
        # DÉCISION: Choisir la meilleure action
        # ========================================
        # DIFFÉRENCE: L'ancien code choisissait aléatoirement
        # Le nouveau compare les scores et choisit le meilleur
        
        if joker_score > rect_score and joker_action:
            # Le JOKER est plus efficace
            actions.append(joker_action)
            current_grid = joker_grid
            jokers_used += 1
        elif rect_action and rect_score > 0:
            # Le RECT est plus efficace (ou pas de JOKER dispo)
            actions.append(rect_action)
            current_grid = rect_grid
        else:
            # Aucune bonne action trouvée: corriger pixel par pixel
            # (en dernier recours)
            for y in range(grid_height):
                for x in range(grid_width):
                    if current_grid[y][x] != target_grid[y][x]:
                        color = target_grid[y][x]
                        actions.append(f'RECT {x} {y} {x} {y} {color}')
                        current_grid[y][x] = color
                        if len(actions) >= max_actions:
                            return "\n".join(actions)
            break

    return "\n".join(actions)


# ========================================
# CODE DE TEST (identique à l'ancien)
# ========================================
if __name__ == '__main__':
    import test_solution
    import datetime
    
    dataset_file = "1_example"
    dataset = open(f'datasets/{dataset_file}.json').read()

    print('---------------------------------')
    print(f'Résolution de {dataset_file}')
    solution = solve(dataset)
    print('---------------------------------')
    score, is_valid, message = test_solution.get_solution_score(solution, dataset)

    if is_valid:
        print('✅ Solution valide!')
        print(f'Message: {message}')
        print(f'Score: {score:_}')
        
        save = input('Sauvegarder la solution? (o/n): ')
        if save.lower() in ['o', 'y', 'oui', 'yes']:
            date = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f'solutions/{dataset_file}_{score}_{date}.txt'

            with open(file_name, 'w') as f:
                f.write(solution)
            print('Solution sauvegardée')
        else:
            print('Solution non sauvegardée')
    else:
        print('❌ Solution invalide')
        print(f'Message: {message}')