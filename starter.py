import json
from collections import Counter

def solve(dataset_txt):
    """
    Solution RAPIDE et efficace pour le problème Botksy.
    Optimisée pour la vitesse tout en gardant un bon score.
    """
    
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
    # STRATÉGIE 1: Remplissage couleur dominante
    # ========================================
    color_counts = Counter()
    for row in target_grid:
        for color in row:
            color_counts[color] += 1
    
    if color_counts:
        most_common_color, count = color_counts.most_common(1)[0]
        if count > (grid_width * grid_height * 0.3):
            actions.append(f'RECT 0 0 {grid_width-1} {grid_height-1} {most_common_color}')
            for y in range(grid_height):
                for x in range(grid_width):
                    current_grid[y][x] = most_common_color

    # ========================================
    # STRATÉGIE 2: Détection RAPIDE de rectangles par lignes
    # ========================================
    def find_horizontal_rects(grid, target):
        """Trouve rapidement des rectangles horizontaux uniformes."""
        best_actions = []
        
        for y in range(grid_height):
            x = 0
            while x < grid_width:
                if grid[y][x] != target[y][x]:
                    color = target[y][x]
                    x_start = x
                    
                    # Étendre horizontalement
                    while x < grid_width and target[y][x] == color and grid[y][x] != color:
                        x += 1
                    x_end = x - 1
                    
                    # Essayer d'étendre verticalement
                    y_end = y
                    can_extend = True
                    while can_extend and y_end < grid_height - 1:
                        for x_check in range(x_start, x_end + 1):
                            if target[y_end + 1][x_check] != color or grid[y_end + 1][x_check] == color:
                                can_extend = False
                                break
                        if can_extend:
                            y_end += 1
                    
                    # Ajouter si le rectangle est assez grand
                    area = (x_end - x_start + 1) * (y_end - y + 1)
                    if area >= 3:  # Au moins 3 pixels
                        best_actions.append((area, f'RECT {x_start} {y} {x_end} {y_end} {color}', x_start, y, x_end, y_end, color))
                else:
                    x += 1
        
        return best_actions

    # ========================================
    # STRATÉGIE 3: JOKERs ciblés sur zones complexes
    # ========================================
    def find_strategic_jokers(grid, target, max_size):
        """Trouve des JOKERs dans les zones avec beaucoup d'erreurs."""
        joker_candidates = []
        
        # Échantillonnage : tester seulement certaines positions (grille 5x5)
        step = max(5, min(grid_height, grid_width) // 10)
        
        for y1 in range(0, grid_height, step):
            for x1 in range(0, grid_width, step):
                # Tester quelques tailles populaires
                for size_factor in [0.5, 0.75, 1.0]:
                    side = int((max_size * size_factor) ** 0.5)
                    y2 = min(y1 + side - 1, grid_height - 1)
                    x2 = min(x1 + side - 1, grid_width - 1)
                    
                    area = (x2 - x1 + 1) * (y2 - y1 + 1)
                    if area > max_size:
                        continue
                    
                    corrections = sum(
                        1 for y in range(y1, y2 + 1)
                        for x in range(x1, x2 + 1)
                        if grid[y][x] != target[y][x]
                    )
                    
                    if corrections > 0:
                        ratio = corrections / area
                        joker_candidates.append((ratio, corrections, f'JOKER {x1} {y1} {x2} {y2}', x1, y1, x2, y2))
        
        # Trier par ratio décroissant
        joker_candidates.sort(reverse=True)
        return joker_candidates

    # ========================================
    # APPLICATION RAPIDE: Rectangles d'abord
    # ========================================
    iteration = 0
    max_iterations = 20  # Limiter les itérations
    
    while len(actions) < max_actions and iteration < max_iterations:
        iteration += 1
        
        errors = sum(
            1 for y in range(grid_height) 
            for x in range(grid_width) 
            if current_grid[y][x] != target_grid[y][x]
        )
        
        if errors == 0:
            break
        
        # Trouver les meilleurs rectangles horizontaux
        rect_actions = find_horizontal_rects(current_grid, target_grid)
        
        if rect_actions:
            # Trier par taille décroissante et prendre les meilleurs
            rect_actions.sort(reverse=True)
            
            applied = 0
            for area, action, x1, y, x2, y2, color in rect_actions[:10]:  # Max 10 par itération
                # Vérifier si toujours valide
                valid = all(
                    current_grid[yy][xx] != target_grid[yy][xx] and target_grid[yy][xx] == color
                    for yy in range(y, y2 + 1)
                    for xx in range(x1, x2 + 1)
                )
                
                if valid and len(actions) < max_actions:
                    actions.append(action)
                    for yy in range(y, y2 + 1):
                        for xx in range(x1, x2 + 1):
                            current_grid[yy][xx] = color
                    applied += 1
            
            if applied > 0:
                continue
        
        # Utiliser des JOKERs si nécessaire
        if jokers_used < max_jokers:
            joker_candidates = find_strategic_jokers(current_grid, target_grid, max_joker_size)
            
            for ratio, corrections, action, x1, y1, x2, y2 in joker_candidates[:3]:  # Top 3
                if ratio >= 0.4 and jokers_used < max_jokers and len(actions) < max_actions:
                    # Vérifier validité
                    actual_corrections = sum(
                        1 for y in range(y1, y2 + 1)
                        for x in range(x1, x2 + 1)
                        if current_grid[y][x] != target_grid[y][x]
                    )
                    
                    if actual_corrections > 0:
                        actions.append(action)
                        for y in range(y1, y2 + 1):
                            for x in range(x1, x2 + 1):
                                current_grid[y][x] = target_grid[y][x]
                        jokers_used += 1
                        break
        
        # Si rien ne marche, passer à la correction ciblée
        if len(rect_actions) == 0:
            break
    
    # ========================================
    # PHASE FINALE: Corrections par petits rectangles
    # ========================================
    errors_remaining = [
        (y, x) for y in range(grid_height) 
        for x in range(grid_width) 
        if current_grid[y][x] != target_grid[y][x]
    ]
    
    # Grouper les erreurs proches
    processed = set()
    for y, x in errors_remaining:
        if (y, x) in processed or len(actions) >= max_actions:
            continue
        
        color = target_grid[y][x]
        
        # Trouver un petit rectangle autour de ce pixel
        x_end = x
        while x_end < grid_width - 1 and target_grid[y][x_end + 1] == color and current_grid[y][x_end + 1] != color:
            x_end += 1
        
        y_end = y
        can_extend = True
        while can_extend and y_end < grid_height - 1:
            for x_check in range(x, x_end + 1):
                if target_grid[y_end + 1][x_check] != color or current_grid[y_end + 1][x_check] == color:
                    can_extend = False
                    break
            if can_extend:
                y_end += 1
        
        actions.append(f'RECT {x} {y} {x_end} {y_end} {color}')
        for yy in range(y, y_end + 1):
            for xx in range(x, x_end + 1):
                current_grid[yy][xx] = color
                processed.add((yy, xx))

    return "\n".join(actions)


# ========================================
# CODE DE TEST
# ========================================
if __name__ == '__main__':
    import test_solution
    import datetime
    import time
    
    dataset_file = "4_pacman"
    dataset = open(f'datasets/{dataset_file}.json').read()

    print('---------------------------------')
    print(f'Résolution de {dataset_file}')
    start_time = time.time()
    solution = solve(dataset)
    elapsed_time = time.time() - start_time
    print(f'Temps d\'exécution: {elapsed_time:.2f}s')
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