import json
from collections import Counter

def solve(dataset_txt):
    """
    Solver ultra-rapide pour Botksy - Optimisé pour la vitesse.
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
    # STRATÉGIE 1: Remplissage initial rapide
    # ========================================
    color_counts = Counter()
    for row in target_grid:
        for color in row:
            color_counts[color] += 1
    
    if color_counts:
        most_common_color = color_counts.most_common(1)[0][0]
        total_pixels = grid_height * grid_width
        
        if color_counts[most_common_color] / total_pixels > 0.2:
            actions.append(f'RECT 0 0 {grid_width-1} {grid_height-1} {most_common_color}')
            for y in range(grid_height):
                for x in range(grid_width):
                    current_grid[y][x] = most_common_color

    # ========================================
    # STRATÉGIE 2: Rectangles optimisés (recherche rapide)
    # ========================================
    def find_fast_rectangles():
        """Recherche rapide de rectangles avec échantillonnage."""
        candidates = []
        
        # Échantillonnage adaptatif
        step_x = max(1, grid_width // 20)
        step_y = max(1, grid_height // 20)
        max_rect_size = min(25, grid_width, grid_height)
        
        for color in range(8):
            for y1 in range(0, grid_height, step_y):
                for x1 in range(0, grid_width, step_x):
                    if target_grid[y1][x1] != color:
                        continue
                    
                    # Expansion rapide
                    x2 = x1
                    while x2 + 1 < grid_width and x2 - x1 < max_rect_size and target_grid[y1][x2 + 1] == color:
                        x2 += 1
                    
                    y2 = y1
                    while y2 + 1 < grid_height and y2 - y1 < max_rect_size:
                        valid = all(target_grid[y2 + 1][x] == color for x in range(x1, x2 + 1))
                        if not valid:
                            break
                        y2 += 1
                    
                    # Gain rapide (sans vérifier chaque pixel)
                    area = (x2 - x1 + 1) * (y2 - y1 + 1)
                    if area < 3:
                        continue
                    
                    # Estimation rapide du gain
                    gain = 0
                    for y in range(y1, y2 + 1):
                        for x in range(x1, x2 + 1):
                            if current_grid[y][x] != target_grid[y][x]:
                                gain += 1
                    
                    if gain > 0:
                        candidates.append((gain, area, x1, y1, x2, y2, color))
        
        return sorted(candidates, key=lambda c: c[0], reverse=True)

    # Appliquer top rectangles rapidement
    rects = find_fast_rectangles()
    applied = set()
    
    for gain, area, x1, y1, x2, y2, color in rects[:min(50, max_actions)]:
        if len(actions) >= max_actions - max_jokers - 5:
            break
        
        # Check rapide de chevauchement (échantillonnage)
        sample_points = [(x1, y1), (x2, y2), ((x1+x2)//2, (y1+y2)//2)]
        if any(p in applied for p in sample_points):
            continue
        
        actions.append(f'RECT {x1} {y1} {x2} {y2} {color}')
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                current_grid[y][x] = color
                applied.add((x, y))

    # ========================================
    # STRATÉGIE 3: JOKERs ultra-rapides
    # ========================================
    if jokers_used < max_jokers and max_joker_size > 0:
        # Recherche rapide des zones à forte densité d'erreurs
        best_jokers = []
        
        # Échantillonnage grossier
        step = max(2, min(grid_width, grid_height) // 15)
        
        for y1 in range(0, grid_height, step):
            for x1 in range(0, grid_width, step):
                # Tester quelques tailles seulement
                for size_ratio in [1.0, 0.75, 0.5]:
                    size = int(max_joker_size * size_ratio)
                    if size < 2:
                        continue
                    
                    # Forme carrée approximative
                    side = int(size ** 0.5)
                    x2 = min(x1 + side - 1, grid_width - 1)
                    y2 = min(y1 + side - 1, grid_height - 1)
                    
                    actual_area = (x2 - x1 + 1) * (y2 - y1 + 1)
                    if actual_area > max_joker_size:
                        continue
                    
                    errors = sum(1 for y in range(y1, y2+1) 
                               for x in range(x1, x2+1) 
                               if current_grid[y][x] != target_grid[y][x])
                    
                    if errors > actual_area * 0.3:
                        best_jokers.append((errors, x1, y1, x2, y2))
        
        # Appliquer les meilleurs JOKERs
        for errors, x1, y1, x2, y2 in sorted(best_jokers, reverse=True)[:max_jokers]:
            if jokers_used >= max_jokers or len(actions) >= max_actions:
                break
            
            actions.append(f'JOKER {x1} {y1} {x2} {y2}')
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    current_grid[y][x] = target_grid[y][x]
            jokers_used += 1

    # ========================================
    # STRATÉGIE 4: Correction finale rapide
    # ========================================
    iterations = 0
    max_iterations = max_actions - len(actions)
    
    while iterations < max_iterations and len(actions) < max_actions:
        best_improvement = 0
        best_action = None
        best_grid = None
        
        # Recherche très limitée
        search_size = 8
        step_search = max(1, min(grid_width, grid_height) // 30)
        
        for color in range(8):
            for y1 in range(0, grid_height, step_search):
                for x1 in range(0, grid_width, step_search):
                    for size in [1, 2, 4, 8]:
                        x2 = min(x1 + size - 1, grid_width - 1)
                        y2 = min(y1 + size - 1, grid_height - 1)
                        
                        improvement = 0
                        for y in range(y1, y2 + 1):
                            for x in range(x1, x2 + 1):
                                if current_grid[y][x] != target_grid[y][x] and target_grid[y][x] == color:
                                    improvement += 1
                                elif current_grid[y][x] == target_grid[y][x] and target_grid[y][x] != color:
                                    improvement -= 1
                        
                        if improvement > best_improvement:
                            best_improvement = improvement
                            best_action = f'RECT {x1} {y1} {x2} {y2} {color}'
                            best_grid = [row[:] for row in current_grid]
                            for y in range(y1, y2 + 1):
                                for x in range(x1, x2 + 1):
                                    best_grid[y][x] = color
        
        if best_action and best_improvement > 0:
            actions.append(best_action)
            current_grid = best_grid
            iterations += 1
        else:
            break
        
        # Check rapide si terminé (échantillonnage)
        if iterations % 5 == 0:
            sample_size = min(100, total_pixels)
            sample_correct = sum(1 for _ in range(sample_size)
                               if current_grid[_ % grid_height][_ % grid_width] == 
                                  target_grid[_ % grid_height][_ % grid_width])
            if sample_correct == sample_size:
                break

    return "\n".join(actions)


# ========================================
# CODE DE TEST
# ========================================
if __name__ == '__main__':
    import test_solution
    import datetime
    import time
    
    dataset_file = "5_banksy"
    dataset = open(f'datasets/{dataset_file}.json').read()

    print('---------------------------------')
    print(f'Résolution de {dataset_file}')
    start_time = time.time()
    solution = solve(dataset)
    elapsed_time = time.time() - start_time
    print(f'Temps d\'exécution: {elapsed_time:.2f}s')
    print(f'Nombre d\'actions: {len(solution.splitlines())}')
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