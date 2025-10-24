import json
from collections import Counter

def solve(dataset_txt):
    """
    Fonction principale qui résout le problème de reconstruction d'images.
    
    STRATÉGIE OPTIMISÉE POUR GRANDES GRILLES (comme wplace):
    1. Remplissage initial par la couleur dominante (pour couvrir rapidement la majorité).
    2. Boucle principale: Chercher le meilleur JOKER (s'il reste) et le meilleur RECT.
    3. RECT est optimisé pour trouver de grandes zones d'une seule couleur qui sont incorrectes.
    4. JOKER cherche à corriger le maximum d'erreurs dans les limites de taille.
    """
    
    # Lecture des données du dataset
    dataset = json.loads(dataset_txt)
    
    target_grid = dataset['grid']
    max_actions = dataset['maxActions']
    max_jokers = dataset['maxJokers']
    max_joker_size = dataset['maxJokerSize']
    grid_height = len(target_grid)
    grid_width = len(target_grid[0])

    actions = []
    current_grid = [[0 for _ in range(grid_width)] for _ in range(grid_height)]
    jokers_used = 0

    # ========================================
    # STRATÉGIE 1: Remplissage initial intelligent
    # ========================================
    color_counts = Counter()
    for row in target_grid:
        for color in row:
            color_counts[color] += 1
            
    # La couleur dominante inclut 0
    most_common_color = color_counts.most_common(1)[0][0]
    
    # Appliquer l'action de remplissage si elle n'est pas la couleur initiale (0)
    if most_common_color != 0:
        actions.append(f'RECT 0 0 {grid_width-1} {grid_height-1} {most_common_color}')
        # Mettre à jour la grille courante
        for y in range(grid_height):
            for x in range(grid_width):
                current_grid[y][x] = most_common_color
    # Si la couleur dominante est 0, on garde la grille initiale à 0.

    # ========================================
    # STRATÉGIE 2: Fonction pour trouver le meilleur JOKER (Inchangée mais essentielle)
    # ========================================
    def find_best_joker(grid, target, max_size):
        """
        Trouve le meilleur JOKER (zone à copier exactement depuis la cible).
        C'est coûteux (O(W^2 H^2)) mais le joker est limité en taille, ce qui atténue.
        """
        best_score = 0
        best_action = None
        best_new_grid = None
        
        # Tester toutes les positions et tailles possibles
        for y1 in range(grid_height):
            for x1 in range(grid_width):
                # Nous limitons la recherche de y2 et x2 en fonction de max_size
                # pour ne pas tester des rectangles trop grands inutiles
                max_h = max_size # Une hauteur ou largeur maximale
                for y2 in range(y1, min(y1 + max_h, grid_height)):
                    for x2 in range(x1, min(x1 + max_h, grid_width)):
                        
                        area = (x2 - x1 + 1) * (y2 - y1 + 1)
                        if area > max_size:
                            continue
                        
                        corrections = 0
                        for y in range(y1, y2 + 1):
                            for x in range(x1, x2 + 1):
                                if grid[y][x] != target[y][x]:
                                    corrections += 1
                        
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
    # STRATÉGIE 3: Fonction pour trouver le meilleur rectangle RECT (Optimisée)
    # ========================================
    def find_best_rect(grid, target):
        """
        Trouve le meilleur rectangle RECT qui améliore le plus la grille.
        
        HEURISTIQUE: On explore moins de rectangles pour gagner en temps,
        mais ceux explorés sont plus pertinents (rectangles maximaux de même couleur).
        """
        best_score = 0
        best_action = None
        best_new_grid = None
        
        # Déjà_Traité_RECT: Marquer les pixels déjà inclus dans un grand RECT testé
        # pour éviter la redondance et le temps de calcul.
        already_processed = [[False for _ in range(grid_width)] for _ in range(grid_height)]
        
        # Tester uniquement les couleurs qui ne sont pas la couleur dominante de départ
        for color in range(8):
            if color == most_common_color:
                continue
            
            for y1 in range(grid_height):
                for x1 in range(grid_width):
                    # On ne cherche un nouveau grand rectangle que s'il y a une erreur à corriger
                    # et si on n'a pas déjà trouvé un grand rectangle ici.
                    if grid[y1][x1] != target[y1][x1] and target[y1][x1] == color and not already_processed[y1][x1]:
                        
                        # Trouver le plus grand rectangle uniforme de cette couleur 'color'
                        # à partir de (x1, y1) dans la GRILLE CIBLE (target_grid).
                        
                        # 1. Trouver la largeur maximale (x2_max)
                        x2_max = x1
                        while x2_max + 1 < grid_width and target[y1][x2_max + 1] == color:
                            x2_max += 1
                        
                        # 2. Trouver la hauteur maximale (y2_max)
                        y2_max = y1
                        while y2_max + 1 < grid_height:
                            # Vérifier si toute la ligne (de x1 à x2_max) est de la couleur 'color'
                            is_uniform_line = True
                            for x in range(x1, x2_max + 1):
                                if target[y2_max + 1][x] != color:
                                    is_uniform_line = False
                                    break
                            
                            if is_uniform_line:
                                y2_max += 1
                            else:
                                break
                        
                        # Définir le rectangle R = (x1, y1, x2_max, y2_max)
                        x2, y2 = x2_max, y2_max
                        
                        # Marquer les pixels couverts par ce grand rectangle pour ne pas les ré-examiner
                        # comme point de départ de recherche dans cette même itération de couleur.
                        for y_proc in range(y1, y2 + 1):
                            for x_proc in range(x1, x2 + 1):
                                if target[y_proc][x_proc] == color:
                                    already_processed[y_proc][x_proc] = True
                                
                        # Calculer l'amélioration apportée par ce rectangle
                        improvement = 0
                        current_improvement = 0 # Score temporaire
                        for y in range(y1, y2 + 1):
                            for x in range(x1, x2 + 1):
                                # +1 si on corrige un pixel incorrect
                                if grid[y][x] != target[y][x] and target[y][x] == color:
                                    current_improvement += 1
                                # -1 si on casse un pixel correct (on remet la couleur du fond)
                                elif grid[y][x] == target[y][x] and target[y][x] != color:
                                    current_improvement -= 1
                                
                        # Si l'amélioration est positive, on la compare au meilleur score global
                        if current_improvement > best_score:
                            best_score = current_improvement
                            best_action = f'RECT {x1} {y1} {x2} {y2} {color}'
                            
                            # Simuler l'application du rectangle
                            sim_grid = [row[:] for row in grid]
                            for y in range(y1, y2 + 1):
                                for x in range(x1, x2 + 1):
                                    sim_grid[y][x] = color
                            best_new_grid = sim_grid
        
        # Cas de la couleur 0 (qui est souvent le fond)
        # On ne cherche pas le 'plus grand rectangle' de 0 car ça risque de tout effacer
        # On peut faire une recherche locale pour corriger les 0 oubliés.
        if best_action is None or best_score < 10: # Si la recherche de grand RECT n'a rien donné
             for y in range(grid_height):
                 for x in range(grid_width):
                     if grid[y][x] != target[y][x] and target[y][x] == 0:
                         # Corriger le pixel (x, y) en 0
                         action = f'RECT {x} {y} {x} {y} 0'
                         sim_grid = [row[:] for row in grid]
                         sim_grid[y][x] = 0
                         return action, sim_grid, 1 # Retourne immédiatement pour un gain de temps
                         
        return best_action, best_new_grid, best_score

    # ========================================
    # BOUCLE PRINCIPALE D'OPTIMISATION
    # ========================================
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
        # On donne un avantage au JOKER en multipliant son score par une prime,
        # car il garantit une perfection locale.
        joker_bonus = 1.2 
        if jokers_used < max_jokers:
            joker_action, joker_grid, joker_score = find_best_joker(current_grid, target_grid, max_joker_size)
            joker_score *= joker_bonus # Appliquer le bonus
        
        # ========================================
        # DÉCISION: Choisir la meilleure action
        # ========================================
        if joker_score > rect_score and joker_action:
            # Le JOKER est plus efficace
            actions.append(joker_action)
            current_grid = joker_grid
            jokers_used += 1
        elif rect_action and rect_score > 0:
            # Le RECT est plus efficace (ou pas de JOKER dispo)
            actions.append(rect_action)
            current_grid = rect_grid
        elif errors > 0 and len(actions) < max_actions:
            # Cas d'urgence: aucune action de bloc bénéfique n'a été trouvée.
            # On applique une correction ponctuelle (pixel par pixel)
            # pour avancer et éviter la boucle infinie si max_actions n'est pas atteint.
            
            # Trouver la première erreur et la corriger avec un RECT 1x1
            found_error = False
            for y in range(grid_height):
                for x in range(grid_width):
                    if current_grid[y][x] != target_grid[y][x]:
                        color = target_grid[y][x]
                        actions.append(f'RECT {x} {y} {x} {y} {color}')
                        current_grid[y][x] = color
                        found_error = True
                        break
                if found_error:
                    break
            
            if not found_error: # S'il n'y a plus d'erreurs, on sort (au cas où)
                break 
            
        else:
            # Aucune action bénéfique (y compris le fallback), on arrête.
            break

    return "\n".join(actions)


# Le reste du code de test (if __name__ == '__main__':) reste inchangé
if __name__ == '__main__':
    import test_solution
    import datetime
    
    # Remplacer par le nom du dataset 'wplace' quand il sera disponible.
    dataset_file = "6_wplace" 
    try:
        dataset = open(f'datasets/{dataset_file}.json').read()
    except FileNotFoundError:
        print(f"Le fichier de données 'datasets/{dataset_file}.json' n'a pas été trouvé.")
        exit()

    print('---------------------------------')
    print(f'Résolution de {dataset_file}')
    solution = solve(dataset)
    print('---------------------------------')
    score, is_valid, message = test_solution.get_solution_score(solution, dataset)

    if is_valid:
        print('✅ Solution valide!')
        print(f'Message: {message}')
        print(f'Score: {score:_}')
        
        # Sauvegarde (optionnelle)
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