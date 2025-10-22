import json
import datetime
from collections import Counter

def solve(dataset_txt):
    """
    Fonction principale qui résout le problème de reconstruction d'images.
    Stratégie optimisée pour les grandes images sans JOKER.
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
    
    # Grille de travail pour suivre ce qui a déjà été dessiné
    current_grid = [[None for _ in range(grid_width)] for _ in range(grid_height)]
    
    # Compter la fréquence de chaque couleur
    color_counts = Counter()
    for row in target_grid:
        for color in row:
            color_counts[color] += 1
    
    # Étape 1: Remplir avec la couleur dominante
    if color_counts:
        most_common_color = color_counts.most_common(1)[0][0]
        actions.append(f'RECT 0 0 {grid_width-1} {grid_height-1} {most_common_color}')
        for y in range(grid_height):
            for x in range(grid_width):
                current_grid[y][x] = most_common_color
    
    # Étape 2: Grille pour marquer les pixels déjà traités
    processed = [[False] * grid_width for _ in range(grid_height)]
    
    # Étape 3: Pour chaque couleur, trouver des rectangles optimaux
    for color in range(8):
        if color == most_common_color:
            continue  # Déjà rempli
        
        for y in range(grid_height):
            for x in range(grid_width):
                # Si le pixel doit être de cette couleur et n'est pas encore traité
                if target_grid[y][x] == color and not processed[y][x]:
                    # Trouver le plus grand rectangle possible
                    
                    # Déterminer la largeur maximale sur cette ligne
                    max_width = 0
                    for w in range(x, grid_width):
                        if target_grid[y][w] == color and not processed[y][w]:
                            max_width += 1
                        else:
                            break
                    
                    # Déterminer la hauteur maximale avec cette largeur
                    best_width = max_width
                    best_height = 1
                    best_area = max_width
                    
                    # Tester différentes hauteurs
                    for h in range(1, grid_height - y + 1):
                        # Vérifier la largeur disponible pour cette hauteur
                        available_width = max_width
                        for test_y in range(y, y + h):
                            if test_y >= grid_height:
                                available_width = 0
                                break
                            current_width = 0
                            for test_x in range(x, x + max_width):
                                if test_x >= grid_width:
                                    break
                                if target_grid[test_y][test_x] == color and not processed[test_y][test_x]:
                                    current_width += 1
                                else:
                                    break
                            available_width = min(available_width, current_width)
                        
                        if available_width <= 0:
                            break
                        
                        area = available_width * h
                        if area > best_area:
                            best_area = area
                            best_width = available_width
                            best_height = h
                    
                    # Créer le rectangle si on a trouvé quelque chose
                    if best_area > 0:
                        x2 = x + best_width - 1
                        y2 = y + best_height - 1
                        
                        actions.append(f'RECT {x} {y} {x2} {y2} {color}')
                        
                        # Marquer les pixels comme traités
                        for py in range(y, y2 + 1):
                            for px in range(x, x2 + 1):
                                if py < grid_height and px < grid_width:
                                    processed[py][px] = True
                                    current_grid[py][px] = color
                        
                        # Vérifier si on dépasse le nombre d'actions
                        if len(actions) >= max_actions:
                            print(f"⚠️ Limite d'actions atteinte: {max_actions}")
                            return "\n".join(actions)
    
    print(f"✓ Solution générée avec {len(actions)} actions sur {max_actions} autorisées")
    return "\n".join(actions)


def solve_simple(dataset_txt):
    """
    Version simple qui dessine pixel par pixel si nécessaire.
    Utilisé comme fallback.
    """
    dataset = json.loads(dataset_txt)
    
    target_grid = dataset['grid']
    max_actions = dataset['maxActions']
    grid_height = len(target_grid)
    grid_width = len(target_grid[0])

    actions = []
    
    # Remplir avec la couleur dominante
    color_counts = Counter()
    for row in target_grid:
        for color in row:
            color_counts[color] += 1
    
    most_common_color = color_counts.most_common(1)[0][0]
    actions.append(f'RECT 0 0 {grid_width-1} {grid_height-1} {most_common_color}')
    
    # Corriger pixel par pixel les différences
    for y in range(grid_height):
        for x in range(grid_width):
            if target_grid[y][x] != most_common_color:
                actions.append(f'RECT {x} {y} {x} {y} {target_grid[y][x]}')
                
                if len(actions) >= max_actions:
                    return "\n".join(actions)
    
    return "\n".join(actions)


# ========================================
# CODE DE TEST
# ========================================
if __name__ == '__main__':
    import test_solution
    
    # Choisir le dataset à résoudre
    dataset_file = "3_mchat"
    
    print('=================================')
    print(f'Résolution de {dataset_file}')
    print('=================================')
    
    # Charger le dataset
    with open(f'datasets/{dataset_file}.json', 'r') as f:
        dataset = f.read()
    
    # Résoudre
    print("Génération de la solution...")
    solution = solve(dataset)
    
    print('---------------------------------')
    print('Test de la solution...')
    score, is_valid, message = test_solution.get_solution_score(solution, dataset)

    if is_valid:
        print('✅ Solution valide!')
        print(f'Message: {message}')
        print(f'Score: {score:_}')
        
        save = input('\nSauvegarder la solution? (o/n): ')
        if save.lower() in ['o', 'y', 'oui', 'yes']:
            date = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f'solutions/{dataset_file}_{score}_{date}.txt'

            with open(file_name, 'w') as f:
                f.write(solution)
            print(f'✓ Solution sauvegardée: {file_name}')
        else:
            print('Solution non sauvegardée')
    else:
        print('❌ Solution invalide')
        print(f'Message: {message}')
        print(f'\nEssai avec la méthode simple...')
        
        # Essayer la méthode simple en fallback
        solution = solve_simple(dataset)
        score, is_valid, message = test_solution.get_solution_score(solution, dataset)
        
        if is_valid:
            print('✅ Solution simple valide!')
            print(f'Message: {message}')
            print(f'Score: {score:_}')
        else:
            print('❌ Solution simple également invalide')
            print(f'Message: {message}')