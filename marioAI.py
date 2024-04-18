import pygame
import sys
import random
import math
import numpy as np

# Initialize Pygame
pygame.init()
clock = pygame.time.Clock()

# Set up the window
window_size = (800, 600)
window = pygame.display.set_mode(window_size)
pygame.display.set_caption("Mario AI")

# Load images and scale them down
brick_image = pygame.transform.scale(pygame.image.load("Images/Brick_Block_Super_Mario.png").convert_alpha(), (30, 30))
pipe_image = pygame.transform.scale(pygame.image.load("Images/Pipe_SuperMario.png").convert_alpha(), (30, 30))
question_block_image = pygame.transform.scale(pygame.image.load("Images/Question_Block_NSMB_Super_Mario.png").convert_alpha(), (30, 30))
enemy_image = pygame.transform.scale(pygame.image.load("Images/Goomba.png").convert_alpha(), (30, 30))
game_over_image = pygame.transform.scale(pygame.image.load("Images/game-over.png").convert_alpha(), (800, 600))

# Load Mario image and define its dimensions
mario_image = pygame.transform.scale(pygame.image.load("Images/mario.jpg").convert_alpha(), (30, 30))
mario_width = 30
mario_height = 45

# Define Mario's position
mario_x = 100
mario_y = window_size[1] - mario_height
mario_dx = 0
mario_dy = 0

# Define enemy dimensions and position
enemy_width = 30
enemy_height = 30
enemy_x = 600
enemy_y = window_size[1] - enemy_height

# Define movement and physics parameters
move_speed = 2
jump_strength = 20
gravity = 1
max_fall_speed = 10
current_level = 1
score = 0
game_over = False

# List to store obstacles for each level
level_obstacles = {
    1: [],
    2: [],
    3: [],
}

# Define level boundaries
level_boundaries = {
    1: 400,
    2: 600,
    3: 800,
}

# Define state space size and action space size
state_space_size = 7  # Adjust based on the actual state representation
action_space_size = 4  # LEFT, RIGHT, UP, NONE

# Initialize Q-table with zeros
q_table = np.zeros((state_space_size, action_space_size))

# Define hyperparameters
learning_rate = 0.1
discount_factor = 0.99
epsilon = 1.0
epsilon_decay = 0.995
epsilon_min = 0.01

# Function to get the current state of the game
def get_game_state():
    global mario_x, mario_y, enemy_x, enemy_y, level_obstacles, score
    obstacles = level_obstacles[current_level]
    return (mario_x, mario_y, enemy_x, enemy_y, tuple((obstacle[0].x, obstacle[0].y) for obstacle in obstacles), score)

# Function to generate obstacles for a given level
def generate_obstacles(level):
    obstacles = []
    if level == 1:
        # Generate obstacles for level 1
        brick_spacing = 40  # Spacing between bricks
        brick_y = 400  # Y-coordinate of bricks
        brick_positions = [100, 150, 200, 250, 300]
        for x in brick_positions:
            obstacles.append((pygame.Rect(x, brick_y, 30, 30), "brick"))
        obstacles.append((pygame.Rect(350, 400, 30, 30), "question_block"))  # Add question block for level 1

        # Add a pipe at the end of level 1 to transition to level 2
        obstacles.append((pygame.Rect(level_boundaries[1], window_size[1] - 30, 30, 30), "pipe"))

    elif level == 2:
        # Generate obstacles for level 2 with fixed positions
        brick_spacing = 40  # Spacing between bricks
        brick_y = 400  # Y-coordinate of bricks
        brick_positions = [100, 150, 200, 250, 300]
        for x in brick_positions:
            obstacles.append((pygame.Rect(x, brick_y, 30, 30), "brick"))
        obstacles.append((pygame.Rect(350, 400, 30, 30), "question_block"))  # Add question block for level 2

        # Add a pipe at the end of level 2 to transition to level 3
        obstacles.append((pygame.Rect(level_boundaries[2], window_size[1] - 30, 30, 30), "pipe"))

    elif level == 3:
        # Generate obstacles for level 3
        brick_spacing = 40  # Spacing between bricks
        brick_y = 400  # Y-coordinate of bricks
        brick_positions = [100, 150, 200, 250, 300]
        for x in brick_positions:
            obstacles.append((pygame.Rect(x, brick_y, 30, 30), "brick"))
        obstacles.append((pygame.Rect(350, 400, 30, 30), "question_block"))  # Add question block for level 3

        # Add a pipe at the beginning of level 3 to transition back to level 2
        obstacles.append((pygame.Rect(0, window_size[1] - 30, 30, 30), "pipe"))

    return obstacles

# Function to discretize continuous state space
def discretize_state(state):
    # Implement discretization logic based on the actual state representation
    return 0  # Placeholder for now

# Function to select an action using ε-greedy policy
def select_action(state):
    if np.random.rand() < epsilon:
        return np.random.choice(action_space_size)  # Exploration
    else:
        # Change action mapping: 0 -> move right, 1 -> move left, 2 -> up, 3 -> none
        action_mapping = {0: 1, 1: 0, 2: 2, 3: 3}
        action = np.argmax(q_table[state])
        return action_mapping[action]

# Function to handle input
def handle_input():
    global mario_x, mario_y, mario_dx, mario_dy, current_level, game_over
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        if mario_x > 0:  # Check if Mario is not at the left boundary
            mario_dx = -move_speed
        else:
            mario_dx = 0  # Stop moving left if at the boundary
    elif keys[pygame.K_RIGHT]:
        if mario_x < window_size[0] - mario_width:  # Check if Mario is not at the right boundary
            mario_dx = move_speed
        else:
            mario_dx = 0  # Stop moving right if at the boundary
    else:
        mario_dx = 0
    if keys[pygame.K_UP] and mario_y >= window_size[1] - mario_height:
        mario_dy = -jump_strength

    # Check if Mario collides with the pipe to transition to the next level
    if current_level < len(level_boundaries):
        pipe_rect = pygame.Rect(level_boundaries[current_level], window_size[1] - 30, 30, 30)
        if pygame.Rect(mario_x, mario_y, mario_width, mario_height).colliderect(pipe_rect):
            current_level += 1
            if current_level > len(level_boundaries):
                current_level = 1
            mario_x = 0
            mario_y = window_size[1] - mario_height

# Function to handle physics
def handle_physics():
    global mario_x, mario_y, mario_dx, mario_dy, current_level, game_over
    if not game_over:
        mario_x += mario_dx
        mario_dy += gravity
        mario_y += mario_dy

        # Boundary check for left and right sides
        if mario_x < 0:
            mario_x = 0
        elif mario_x > window_size[0] - mario_width:
            mario_x = window_size[0] - mario_width

        if mario_y > window_size[1] - mario_height:
            mario_y = window_size[1] - mario_height
            mario_dy = 0

# Function to move the enemy towards Mario
def move_enemy_towards_mario():
    global enemy_x, enemy_y, mario_x, mario_y, game_over
    distance_threshold = 200
    distance = math.sqrt((mario_x - enemy_x)**2 + (mario_y - enemy_y)**2)
    if distance < distance_threshold and not game_over:
        if mario_x > enemy_x:
            enemy_x += move_speed
        elif mario_x < enemy_x:
            enemy_x -= move_speed
        if mario_y > enemy_y:
            enemy_y += move_speed
        elif mario_y < enemy_y:
            enemy_y -= move_speed

        # Check if Mario collides with the enemy
        if pygame.Rect(mario_x, mario_y, mario_width, mario_height).colliderect(
                pygame.Rect(enemy_x, enemy_y, enemy_width, enemy_height)):
            game_over = True

# Function to handle collecting points from question blocks
def handle_point_collection():
    global mario_x, mario_y, current_level, score
    obstacles = level_obstacles[current_level]
    for obstacle in obstacles:
        if obstacle[1] == "question_block":
            if mario_x < obstacle[0].x + obstacle[0].width and mario_x + mario_width > obstacle[0].x and \
               mario_y < obstacle[0].y + obstacle[0].height and mario_y + mario_height > obstacle[0].y:
                score += 10  # Increase score
                obstacles.remove(obstacle)
                # Add animation or effect here if needed

# Function to draw text on the screen
def draw_text(text, font, color, x, y):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.topleft = (x, y)
    window.blit(text_surface, text_rect)

# Main training loop
while True:
    # Reset game variables
    game_over = False
    score = 0
    current_level = 1
    mario_x = 100
    mario_y = window_size[1] - mario_height
    enemy_x = 600
    enemy_y = window_size[1] - enemy_height
    mario_dx = 0
    mario_dy = 0

    # Inner game loop
    while not game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        level_obstacles[current_level] = generate_obstacles(current_level)

        if current_level == 1:
            state = discretize_state(get_game_state())
            action = select_action(state)
            if action == 0:  # LEFT
                mario_dx = -move_speed
            elif action == 1:  # RIGHT
                mario_dx = move_speed
            elif action == 2:  # UP
                if mario_y >= window_size[1] - mario_height:
                    mario_dy = -jump_strength

        handle_physics()
        move_enemy_towards_mario()
        handle_point_collection()

        next_state = discretize_state(get_game_state())
        reward = 0
        q_table[state, action] += learning_rate * (reward + discount_factor * np.max(q_table[next_state]) - q_table[state, action])

        if epsilon > epsilon_min:
            epsilon *= epsilon_decay

        window.fill((0, 0, 0))

        if not game_over:
            window.blit(mario_image, (mario_x, mario_y))

            obstacles = level_obstacles[current_level]
            for obstacle in obstacles:
                if obstacle[1] == "brick":
                    window.blit(brick_image, obstacle[0])
                elif obstacle[1] == "question_block":
                    window.blit(question_block_image, obstacle[0])
                elif obstacle[1] == "pipe":
                    window.blit(pipe_image, obstacle[0])

            window.blit(enemy_image, (enemy_x, enemy_y))

            draw_text("Score: " + str(score), pygame.font.Font(None, 36), (255, 255, 255), 10, 10)
        else:
            window.blit(game_over_image, (0, 0))

        pygame.display.flip()
        clock.tick(60)

    # Check termination condition here, such as reaching a certain number of iterations or achieving a desired performance level
