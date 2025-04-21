import os
import sys
import pygame
import random
import time

EASY = (9, 9, 10)
MEDIUM = (16, 16, 40)
HARD = (16, 30, 99)

CASE_SIZES = {
    EASY: 100,
    MEDIUM: 57,
    HARD: 57
}

COLORS = {
    1: (0, 0, 0),
    2: (0, 0, 0),
    3: (0, 0, 0),
    4: (0, 0, 0),
    5: (0, 0, 0),
    6: (0, 0, 0),
    7: (0, 0, 0),
    8: (0, 0, 0)
}

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def play_sound(path, volume=0.5):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(resource_path(path))
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"Error playing sound {path}: {e}")

def play_background_music(path, volume=0.5):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(resource_path(path))
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"Error playing background music {path}: {e}")

def stop_music():
    try:
        pygame.mixer.music.stop()
    except Exception as e:
        print(f"Error stopping music: {e}")

def load_best_times():
    best_times = {
        EASY: 9999.0,
        MEDIUM: 9999.0,
        HARD: 9999.0
    }

    filepath = "best_times.txt"
    if not os.path.exists(filepath):
        return best_times

    with open(filepath, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        diff_str, val = line.split("=")
        val = float(val)
        if diff_str == "easy":
            best_times[EASY] = val
        elif diff_str == "medium":
            best_times[MEDIUM] = val
        elif diff_str == "hard":
            best_times[HARD] = val

    return best_times

def save_best_times(best_times):
    filepath = "best_times.txt"
    lines = [
        f"easy={best_times[EASY]}",
        f"medium={best_times[MEDIUM]}",
        f"hard={best_times[HARD]}"
    ]
    with open(filepath, "w") as f:
        for line in lines:
            f.write(line + "\n")

class Cell:
    def __init__(self, row, col, is_mine=False):
        self.row = row
        self.col = col
        self.is_mine = is_mine
        self.is_revealed = False
        self.is_flagged = False
        self.adjacent_mines = 0

class Minesweeper:
    def __init__(self, difficulty, home_screen, music_volume, sound_volume):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
        pygame.display.toggle_fullscreen()
        self.screen_width, self.screen_height = self.screen.get_size()
        pygame.display.set_caption("Démineur Démoniaque")

        pygame.display.set_icon(pygame.image.load(resource_path('icon.ico')))

        self.difficulty = difficulty
        self.num_rows, self.num_cols, self.num_mines = difficulty
        self.cell_size = CASE_SIZES[difficulty]
        self.grid_width = self.num_cols * self.cell_size
        self.grid_height = self.num_rows * self.cell_size
        self.grid_start_x = (self.screen_width - self.grid_width) // 2
        self.grid_start_y = (self.screen_height - self.grid_height) // 2 - 20
        self.grid = [[Cell(r, c) for c in range(self.num_cols)] for r in range(self.num_rows)]
        self.game_over_handled = False

        self.start_time = None
        self.timer_running = False

        self.first_move = True
        self.font = pygame.font.SysFont("Algerian", 60)

        # Background
        self.background_image = pygame.image.load(resource_path("background_game.jpg"))
        self.background_image = pygame.transform.scale(self.background_image, (self.screen_width, self.screen_height))

        self.flag_image = pygame.image.load(resource_path("flag.png"))
        self.flag_image = pygame.transform.scale(self.flag_image, (self.cell_size, self.cell_size))

        self.hidden_cell_image = pygame.image.load(resource_path("hidden_cell.png"))
        self.hidden_cell_image = pygame.transform.scale(self.hidden_cell_image, (self.cell_size, self.cell_size))

        self.home_screen = home_screen
        self.music_volume = music_volume
        self.sound_volume = sound_volume

        # Chargement des meilleurs temps
        self.best_times = load_best_times()
        self.reset_game()

        # --- Chargement des boutons PNG (dimension fixe + survol) ---
        self.reset_btn_img = pygame.image.load(resource_path("reset_btn.png")).convert_alpha()
        self.home_btn_img = pygame.image.load(resource_path("home_btn.png")).convert_alpha()

        # On définit une taille de base (ex. 180×60) et on applique un factor d'échelle
        self.reset_base_size = (200, 50)
        self.home_base_size  = (200, 50)


        # Échelles
        self.reset_scale = 1.0
        self.home_scale  = 1.0

        # Paramètres de zoom
        self.scale_speed = 0.02
        self.min_scale = 1.0
        self.max_scale = 1.2

    def draw_grid(self):
        for r in range(self.num_rows):
            for c in range(self.num_cols):
                cell = self.grid[r][c]
                rect = pygame.Rect(
                    self.grid_start_x + c * self.cell_size,
                    self.grid_start_y + r * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                if cell.is_revealed:
                    temp_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                    temp_surface.fill((139, 0, 0, 128))
                    self.screen.blit(temp_surface, rect.topleft)
                    if cell.is_mine:
                        pygame.draw.circle(self.screen, (0,0,0), rect.center, self.cell_size//4)
                    elif cell.adjacent_mines>0:
                        text_surface = self.font.render(str(cell.adjacent_mines), True, COLORS[cell.adjacent_mines])
                        text_rect = text_surface.get_rect(center=rect.center)
                        self.screen.blit(text_surface, text_rect)
                else:
                    self.screen.blit(self.hidden_cell_image, rect.topleft)
                    if cell.is_flagged:
                        self.screen.blit(self.flag_image, rect.topleft)
                pygame.draw.rect(self.screen, (0,0,0), rect, 1)

    def reveal_cell(self, row, col):
        cell = self.grid[row][col]
        if cell.is_revealed or cell.is_flagged:
            return
        if self.first_move:
            self.first_move=False
            self.place_mines(row,col)
            self.calculate_adjacent_mines()
            self.start_timer()
            play_background_music("Démineur démoniaque son d_ambiance.mp3", self.music_volume)
        if cell.is_mine:
            cell.is_revealed=True
            self.game_over(False)
            return
        cell.is_revealed=True
        if cell.adjacent_mines==0:
            for rr in range(max(0,row-1),min(self.num_rows,row+2)):
                for cc in range(max(0,col-1),min(self.num_cols,col+2)):
                    if not self.grid[rr][cc].is_revealed:
                        self.reveal_cell(rr, cc)
        if self.check_win():
            self.game_over(True)

    def place_mines(self, initial_row, initial_col):
        mines_placed = 0
        while mines_placed<self.num_mines:
            r = random.randint(0,self.num_rows-1)
            c = random.randint(0,self.num_cols-1)
            if (not self.grid[r][c].is_mine and
                not self.is_initial_area(r, c, initial_row, initial_col)):
                self.grid[r][c].is_mine=True
                mines_placed+=1

    def is_initial_area(self, row, col, initial_row, initial_col):
        return (
            max(0, initial_row-1) <= row <= min(self.num_rows-1, initial_row+1)
            and max(0, initial_col-1) <= col <= min(self.num_cols-1, initial_col+1)
        )

    def calculate_adjacent_mines(self):
        for r in range(self.num_rows):
            for c in range(self.num_cols):
                if not self.grid[r][c].is_mine:
                    self.grid[r][c].adjacent_mines = self.count_adjacent_mines(r,c)

    def count_adjacent_mines(self, row, col):
        count=0
        for rr in range(max(0, row-1), min(self.num_rows, row+2)):
            for cc in range(max(0,col-1), min(self.num_cols,col+2)):
                if self.grid[rr][cc].is_mine:
                    count+=1
        return count

    def toggle_flag(self, row,col):
        cell=self.grid[row][col]
        if cell.is_revealed:
            return
        cell.is_flagged = not cell.is_flagged

    def fade_in_image(self, image_path, duration=7):
        image = pygame.image.load(resource_path(image_path))
        image = pygame.transform.scale(image, (self.screen.get_width(),self.screen.get_height()))
        temp_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        for alpha in range(0,256,5):
            temp_surface.fill((0,0,0,0))
            temp_surface.blit(image,(0,0))
            temp_surface.set_alpha(alpha)
            self.screen.blit(temp_surface,(0,0))
            pygame.display.flip()
            pygame.time.delay(int(duration*10))
        self.reset_game()

    def game_over(self, won):
        self.game_over_handled=True
        self.stop_timer()
        stop_music()
        if won:
            elapsed_time=self.get_elapsed_time()
            if elapsed_time< self.best_times[self.difficulty]:
                self.best_times[self.difficulty]=elapsed_time
                save_best_times(self.best_times)
            play_sound("Rire démoniaque.mp3", self.sound_volume)
            self.fade_in_image("Image victoire.jpg")
        else:
            play_sound("Screamer.mp3", self.sound_volume)
            self.show_screamer("Screamer démoniaque.jpg")

    def show_screamer(self, image_path):
        image=pygame.image.load(resource_path(image_path))
        image=pygame.transform.scale(image,(self.screen.get_width(),self.screen.get_height()))
        self.screen.blit(image,(0,0))
        pygame.display.flip()
        time.sleep(0.1)
        self.reset_game()

    def check_win(self):
        for r in range(self.num_rows):
            for c in range(self.num_cols):
                if not self.grid[r][c].is_revealed and not self.grid[r][c].is_mine:
                    return False
        return True

    def reset_game(self):
        self.first_move=True
        self.game_over_handled=False
        self.stop_timer()
        stop_music()
        for r in range(self.num_rows):
            for c in range(self.num_cols):
                self.grid[r][c]=Cell(r,c)
        self.calculate_adjacent_mines()

    def start_timer(self):
        self.start_time=time.time()
        self.timer_running=True

    def stop_timer(self):
        self.timer_running=False

    def get_elapsed_time(self):
        if self.start_time is None:
            return 0.0
        return round(time.time()-self.start_time,1)

    def update_timer(self):
        if self.timer_running:
            elapsed_time=self.get_elapsed_time()
            best_time_for_diff=self.best_times[self.difficulty]
            timer_font=pygame.font.SysFont("Algerian",30)
            record_text=timer_font.render(f"Record: {best_time_for_diff}s",True,(255,255,255))
            self.screen.blit(record_text,(10,self.screen_height-70))
            timer_text=timer_font.render(f"Stress: {elapsed_time}s",True,(255,255,255))
            self.screen.blit(timer_text,(10,self.screen_height-40))

    def update_scales(self, mouse_x, mouse_y, reset_rect, home_rect):
        # Survol reset
        if reset_rect.collidepoint(mouse_x, mouse_y):
            self.reset_scale = min(self.reset_scale + self.scale_speed, self.max_scale)
        else:
            self.reset_scale = max(self.reset_scale - self.scale_speed, self.min_scale)

        # Survol home
        if home_rect.collidepoint(mouse_x, mouse_y):
            self.home_scale = min(self.home_scale + self.scale_speed, self.max_scale)
        else:
            self.home_scale = max(self.home_scale - self.scale_speed, self.min_scale)


    def draw_buttons(self):
        """
        On part de base 180×60 => on applique self.reset_scale, etc.
        """
        rw, rh = self.reset_base_size
        hw, hh = self.home_base_size


        # Dimensions scalées
        reset_w = int(rw * self.reset_scale)
        reset_h = int(rh * self.reset_scale)
        home_w  = int(hw * self.home_scale)
        home_h  = int(hh * self.home_scale)

        # On scale l'image
        reset_surf = pygame.transform.scale(self.reset_btn_img, (reset_w, reset_h))
        home_surf  = pygame.transform.scale(self.home_btn_img,  (home_w,  home_h))


        # On place ces images
        # On veut par ex. center= (screen_width//4, screen_height - 40 + reset_h/2) etc.
        # pour que la base du bouton soit à ~screen_height-40
        # Pas obligatoire, à vous de caler la position.

        reset_centerx = self.screen_width // 4
        home_centerx  = self.screen_width * 3 // 4
        baseline_y    = self.screen_height - 40  # "bas" du bouton

        # On place le centre en x, et en y => baseline - half height
        reset_rect = reset_surf.get_rect(center=(reset_centerx + 50, baseline_y - reset_h//2 + 20))
        home_rect  = home_surf.get_rect(center=(home_centerx - 50,   baseline_y - home_h//2 + 20))


        # On blit
        self.screen.blit(reset_surf, reset_rect)
        self.screen.blit(home_surf, home_rect)


        return reset_rect, home_rect

    def run(self):
        running=True
        while running:
            self.screen.blit(self.background_image,(0,0))
            reset_rect, home_rect = self.draw_buttons()

            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    running=False
                elif event.type==pygame.MOUSEBUTTONDOWN:
                    x,y=event.pos
                    if reset_rect.collidepoint(x,y):
                        self.reset_game()
                    elif home_rect.collidepoint(x,y):
                        running=False
                        self.home_screen.run()
                    else:
                        x-=self.grid_start_x
                        y-=self.grid_start_y
                        if 0<=x<self.grid_width and 0<=y<self.grid_height:
                            row, col = y//self.cell_size, x//self.cell_size
                            if event.button==1:
                                self.reveal_cell(row,col)
                            elif event.button==3:
                                self.toggle_flag(row,col)

            # Survol => update scales
            mx,my = pygame.mouse.get_pos()
            self.update_scales(mx, my, reset_rect, home_rect)

            self.draw_grid()
            self.update_timer()
            pygame.display.flip()

        pygame.quit()

class HomeScreen:
    def __init__(self):
        pygame.init()
        self.screen=pygame.display.set_mode((0,0),pygame.RESIZABLE)
        pygame.display.toggle_fullscreen()
        self.screen_width, self.screen_height = self.screen.get_size()
        pygame.display.set_caption("Démineur Démoniaque")

        pygame.display.set_icon(pygame.image.load(resource_path('icon.ico')))

        self.background_image=pygame.image.load(resource_path("background.png"))
        self.background_image=pygame.transform.scale(self.background_image,(self.screen_width,self.screen_height))
        self.title_image=pygame.image.load(resource_path("title_image.png"))
        self.title_image=pygame.transform.scale(self.title_image,(900,225))

        self.easy_img=pygame.image.load(resource_path("easy_button.png")).convert_alpha()
        self.medium_img=pygame.image.load(resource_path("medium_button.png")).convert_alpha()
        self.hard_img=pygame.image.load(resource_path("hard_button.png")).convert_alpha()

        # On fixe des tailles de base pour easy/medium/hard
        self.easy_base_size   = (300,300)
        self.medium_base_size = (300,300)
        self.hard_base_size   = (300,300)

        self.easy_scale=1.0
        self.medium_scale=1.0
        self.hard_scale=1.0

        self.scale_speed=0.02
        self.min_scale=1.0
        self.max_scale=1.2

        # Boutons Quit / Settings
        self.settings_icon=pygame.image.load(resource_path("settings_icon.png")).convert_alpha()
        self.quit_icon    =pygame.image.load(resource_path("quit_icon.png")).convert_alpha()

        self.settings_base_size=(80,80)
        self.quit_base_size   =(60,60)

        self.settings_scale=1.0
        self.quit_scale=1.0

        self.settings_screen=None
        self.music_volume=0.0
        self.sound_volume=0.0

    def draw(self):
        stop_music()
        self.screen.blit(self.background_image,(0,0))
        title_rect=self.title_image.get_rect(center=(self.screen_width//2,100))
        self.screen.blit(self.title_image,title_rect)

        # easy/medium/hard
        easy_w  = int(self.easy_base_size[0]*self.easy_scale)
        easy_h  = int(self.easy_base_size[1]*self.easy_scale)
        med_w   = int(self.medium_base_size[0]*self.medium_scale)
        med_h   = int(self.medium_base_size[1]*self.medium_scale)
        hard_w  = int(self.hard_base_size[0]*self.hard_scale)
        hard_h  = int(self.hard_base_size[1]*self.hard_scale)

        easy_surf=pygame.transform.scale(self.easy_img, (easy_w,easy_h))
        med_surf =pygame.transform.scale(self.medium_img,(med_w,med_h))
        hard_surf=pygame.transform.scale(self.hard_img,(hard_w,hard_h))

        easy_rect = easy_surf.get_rect(center=(self.screen_width//2-400, self.screen_height//2))
        med_rect  = med_surf.get_rect(center=(self.screen_width//2,       self.screen_height//2))
        hard_rect = hard_surf.get_rect(center=(self.screen_width//2+400, self.screen_height//2))

        self.screen.blit(easy_surf, easy_rect)
        self.screen.blit(med_surf,  med_rect)
        self.screen.blit(hard_surf, hard_rect)

        # Quit/Settings
        set_w  = int(self.settings_base_size[0]*self.settings_scale)
        set_h  = int(self.settings_base_size[1]*self.settings_scale)
        quit_w = int(self.quit_base_size[0]*self.quit_scale)
        quit_h = int(self.quit_base_size[1]*self.quit_scale)

        set_surf =pygame.transform.scale(self.settings_icon,(set_w,set_h))
        quit_surf=pygame.transform.scale(self.quit_icon,(quit_w,quit_h))

        quit_rect=quit_surf.get_rect(topright=(self.screen_width-10,10))
        set_rect =set_surf.get_rect(topleft=(10,10))

        self.screen.blit(quit_surf, quit_rect)
        self.screen.blit(set_surf,  set_rect)

        pygame.display.flip()

        return easy_rect, med_rect, hard_rect, quit_rect, set_rect

    def update_scales(self, mouse_x, mouse_y, easy_rect, med_rect, hard_rect, quit_rect, set_rect):
        # Survol easy
        if easy_rect.collidepoint(mouse_x, mouse_y):
            self.easy_scale=min(self.easy_scale+self.scale_speed,self.max_scale)
        else:
            self.easy_scale=max(self.easy_scale-self.scale_speed,self.min_scale)

        # Survol medium
        if med_rect.collidepoint(mouse_x, mouse_y):
            self.medium_scale=min(self.medium_scale+self.scale_speed,self.max_scale)
        else:
            self.medium_scale=max(self.medium_scale-self.scale_speed,self.min_scale)

        # Survol hard
        if hard_rect.collidepoint(mouse_x, mouse_y):
            self.hard_scale=min(self.hard_scale+self.scale_speed,self.max_scale)
        else:
            self.hard_scale=max(self.hard_scale-self.scale_speed,self.min_scale)

        # Survol quit
        if quit_rect.collidepoint(mouse_x, mouse_y):
            self.quit_scale=min(self.quit_scale+self.scale_speed,1.2)
        else:
            self.quit_scale=max(self.quit_scale-self.scale_speed,self.min_scale)

        # Survol settings
        if set_rect.collidepoint(mouse_x, mouse_y):
            self.settings_scale=min(self.settings_scale+self.scale_speed,1.2)
        else:
            self.settings_scale=max(self.settings_scale-self.scale_speed,self.min_scale)

    def run(self):
        running=True
        while running:
            easy_rect, med_rect, hard_rect, quit_rect, set_rect = self.draw()

            mx,my=pygame.mouse.get_pos()
            self.update_scales(mx,my,easy_rect,med_rect,hard_rect,quit_rect,set_rect)

            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type==pygame.MOUSEBUTTONDOWN:
                    x,y=event.pos
                    if easy_rect.collidepoint(x,y):
                        game=Minesweeper(EASY,self,self.music_volume,self.sound_volume)
                        game.run()
                    elif med_rect.collidepoint(x,y):
                        game=Minesweeper(MEDIUM,self,self.music_volume,self.sound_volume)
                        game.run()
                    elif hard_rect.collidepoint(x,y):
                        game=Minesweeper(HARD,self,self.music_volume,self.sound_volume)
                        game.run()
                    elif quit_rect.collidepoint(x,y):
                        pygame.quit()
                        sys.exit()
                    elif set_rect.collidepoint(x,y):
                        self.settings_screen=SettingsScreen(self)
                        self.settings_screen.run()
            pygame.time.delay(10)


class SettingsScreen:
    def __init__(self, home_screen):
        pygame.init()
        # Titre "Réglages"
        pygame.display.set_caption("Réglages - Démineur Démoniaque")

        self.screen=pygame.display.set_mode((0,0),pygame.RESIZABLE)
        pygame.display.toggle_fullscreen()
        self.screen_width, self.screen_height=self.screen.get_size()

        self.home_screen=home_screen
        self.music_volume=self.home_screen.music_volume
        self.sound_volume=self.home_screen.sound_volume

        self.background_imagesettings=pygame.image.load(resource_path("backgroundsettings.png"))
        self.background_imagesettings=pygame.transform.scale(self.background_imagesettings,(self.screen_width,self.screen_height))

        # On remplace "Musique" et "Effets Sonores" par des images => label, SANS effet de survol
        self.music_label_img=pygame.image.load(resource_path("music_label.png")).convert_alpha()
        self.sound_label_img=pygame.image.load(resource_path("sound_label.png")).convert_alpha()

        # Dimensions qu’on veut (fixes, pas de zoom)
        self.music_label_size=(200,50)
        self.sound_label_size=(200,50)

        self.music_label_img=pygame.transform.scale(self.music_label_img,self.music_label_size)
        self.sound_label_img=pygame.transform.scale(self.sound_label_img,self.sound_label_size)

        # On remplace "Retour" par une image, AVEC zoom
        self.back_btn_img=pygame.image.load(resource_path("back_btn.png")).convert_alpha()
        self.back_btn_base_size=(200,50)
        self.back_btn_scale=1.0

        self.scale_speed=0.02
        self.min_scale=1.0
        self.max_scale=1.2

    def draw(self):
        self.screen.blit(self.background_imagesettings,(0,0))

        # On blit le label "Musique"
        music_label_rect=self.music_label_img.get_rect(topleft=(100,150))
        self.screen.blit(self.music_label_img,music_label_rect)

        # On blit le label "Effets Sonores"
        sound_label_rect=self.sound_label_img.get_rect(topleft=(100,250))
        self.screen.blit(self.sound_label_img,sound_label_rect)

        # Sliders
        music_slider_rect, music_handle_rect=self.draw_slider(self.music_volume,150)
        sound_slider_rect, sound_handle_rect=self.draw_slider(self.sound_volume,250)

        # Bouton "Retour" (image) + zoom
        bw, bh=self.back_btn_base_size
        back_w=int(bw*self.back_btn_scale)
        back_h=int(bh*self.back_btn_scale)
        back_surf=pygame.transform.scale(self.back_btn_img,(back_w,back_h))

        back_btn_rect=back_surf.get_rect(center=(self.screen_width//2,
                                                 self.screen_height-80+back_h//2-50))
        self.screen.blit(back_surf,back_btn_rect)

        pygame.display.flip()

        return back_btn_rect, music_slider_rect, music_handle_rect, sound_slider_rect, sound_handle_rect, music_label_rect, sound_label_rect

    def draw_slider(self, value, y_pos):
        slider_width=300
        slider_height=20
        slider_x=320
        slider_y=y_pos + 15
        slider_rect=pygame.Rect(slider_x,slider_y,slider_width,slider_height)
        pygame.draw.rect(self.screen,(0,0,0),slider_rect)

        handle_x=slider_x+int(value*slider_width)-5
        handle_rect=pygame.Rect(handle_x,slider_y,10,20)
        pygame.draw.rect(self.screen,(255,255,255),handle_rect)

        return slider_rect, handle_rect

    def update_back_scale(self, mouse_x, mouse_y, back_rect):
        # Survol back
        if back_rect.collidepoint(mouse_x,mouse_y):
            self.back_btn_scale=min(self.back_btn_scale+self.scale_speed,self.max_scale)
        else:
            self.back_btn_scale=max(self.back_btn_scale-self.scale_speed,self.min_scale)

    def run(self):
        running=True
        dragging=False
        slider_dragging=None

        while running:
            (back_btn_rect,
             music_slider_rect,
             music_handle_rect,
             sound_slider_rect,
             sound_handle_rect,
             music_label_rect,
             sound_label_rect)=self.draw()

            # Les labels ne bougent pas, ils n’ont pas d'effet de survol
            # Seul le bouton "Retour" peut zoomer
            mx,my=pygame.mouse.get_pos()
            self.update_back_scale(mx,my,back_btn_rect)

            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type==pygame.MOUSEBUTTONDOWN:
                    x,y=event.pos
                    if back_btn_rect.collidepoint(x,y):
                        self.home_screen.music_volume=self.music_volume
                        self.home_screen.sound_volume=self.sound_volume
                        running=False
                        self.home_screen.run()
                    elif music_handle_rect.collidepoint(x,y):
                        dragging=True
                        slider_dragging='music'
                    elif sound_handle_rect.collidepoint(x,y):
                        dragging=True
                        slider_dragging='sound'
                elif event.type==pygame.MOUSEBUTTONUP:
                    dragging=False
                    slider_dragging=None
                elif event.type==pygame.MOUSEMOTION and dragging:
                    mx,my=event.pos
                    if slider_dragging=='music':
                        new_val=(mx-320)/300
                        self.music_volume=min(max(new_val,0.0),1.0)
                        pygame.mixer.music.set_volume(self.music_volume)
                    elif slider_dragging=='sound':
                        new_val=(mx-320)/300
                        self.sound_volume=min(max(new_val,0.0),1.0)
            pygame.time.delay(10)

# Point d'entrée
if __name__=="__main__":
    home_screen=HomeScreen()
    home_screen.run()
