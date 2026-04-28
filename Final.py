import pygame, sys, time, random

# ================= CONFIG =================
pygame.init()
WINDOW_W, WINDOW_H = 1100, 680
CELL = 36
GRID = 15
LEFT_W = GRID * CELL
PANEL_W = WINDOW_W - LEFT_W
FPS = 30

SCREEN = pygame.display.set_mode((WINDOW_W, WINDOW_H))
pygame.display.set_caption("Simultaneous Ludo — BFS vs DFS vs A*")
CLOCK = pygame.time.Clock()

FONT = pygame.font.SysFont("Arial", 14)
BIG = pygame.font.SysFont("Arial", 20, bold=True)

WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY  = (210,210,210)
PANEL_BG = (245,245,245)

RED   = (200,50,50)
BLUE  = (40,100,230)
GREEN = (40,170,70)
COLORS = [RED, BLUE, GREEN]
NAMES = ["BFS","DFS","A*"]

AUTO_DELAY = 0.8

# ================= PATH =================
PATH = [
 (6,14),(6,13),(6,12),(6,11),(6,10),
 (5,9),(4,9),(3,9),(2,9),(1,9),(0,9),
 (0,8),(0,7),
 (1,6),(2,6),(3,6),(4,6),(5,6),
 (6,5),(6,4),(6,3),(6,2),(6,1),(6,0),
 (7,0),(8,0),
 (9,1),(9,2),(9,3),(9,4),(9,5),
 (10,6),(11,6),(12,6),(13,6),(14,6),
 (14,7),(14,8),
 (13,9),(12,9),(11,9),(10,9),(9,9),
 (9,10),(9,11),(9,12),(9,13),(9,14),
 (8,14),(7,14)
]
PATH_LEN = len(PATH)
HOME_LEN = 6

START = {0:1, 1:13, 2:31}

HOME_LANES = {
 0:[(6,6),(6,5),(6,4),(7,4),(7,5),(7,6)],
 1:[(5,6),(4,6),(3,6),(3,7),(4,7),(5,7)],
 2:[(8,6),(9,6),(10,6),(10,7),(9,7),(8,7)]
}

# ================= STATE =================
class State:
    def __init__(self):
        self.pos = {p:[-1,-1,-1,-1] for p in range(3)}

def encode_home(p,h): return PATH_LEN + p*HOME_LEN + h
def decode_home(x): return (x-PATH_LEN)//HOME_LEN,(x-PATH_LEN)%HOME_LEN

def distance_to_goal(p,x):
    if x < 0: return PATH_LEN + HOME_LEN
    if x < PATH_LEN: return PATH_LEN-x+HOME_LEN
    _,h = decode_home(x)
    return HOME_LEN-1-h

# ================= MOVE =================
def move_token(st,p,t,d):
    x = st.pos[p][t]
    if x < 0:
        st.pos[p][t] = d-1
        return x, st.pos[p][t]
    if x < PATH_LEN:
        nx = x+d
        if nx < PATH_LEN:
            st.pos[p][t] = nx
        else:
            h = nx-PATH_LEN
            if h < HOME_LEN:
                st.pos[p][t] = encode_home(p,h)
        return x, st.pos[p][t]
    pl,h = decode_home(x)
    if h+d < HOME_LEN:
        st.pos[p][t] = encode_home(p,h+d)
    return x, st.pos[p][t]

# ================= STRATEGIES =================

# -------- BFS (FINAL STRICT LOGIC) --------
bfs_turn = 0

def is_finished(p, x):
    return x >= PATH_LEN and decode_home(x)[1] == HOME_LEN - 1

def all_unlocked(state):
    return all(state.pos[0][t] >= 0 for t in range(4))

def choose_bfs(state, dice):
    global bfs_turn

    # ---------------- PHASE 1: Unlock all tokens first ----------------
    if not all_unlocked(state):
        t = bfs_turn  # strictly follow order T1 → T2 → T3 → T4

        x = state.pos[0][t]

        # If this token is still locked → try unlocking
        if x < 0:
            if dice == 6:
                bfs_turn = (bfs_turn + 1) % 4
                return t
            else:
                return None  # wait, do not move others

        # If already unlocked → skip to next token in order
        bfs_turn = (bfs_turn + 1) % 4
        return None

    # ---------------- PHASE 2: All unlocked → normal round robin ----------------
    for _ in range(4):
        t = bfs_turn
        bfs_turn = (bfs_turn + 1) % 4

        x = state.pos[0][t]

        if is_finished(0, x):
            continue

        return t

    return None

# -------- DFS (UNCHANGED) --------
def choose_dfs(state):
    for t in range(4):
        x = state.pos[1][t]
        if x >= 0 and not (x>=PATH_LEN and decode_home(x)[1]==HOME_LEN-1):
            return t
    for t in range(4):
        if state.pos[1][t] < 0:
            return t
    return 0

# -------- A* (UNCHANGED) --------
def choose_astar(state, dice):
    if dice == 6:
        for t in range(4):
            if state.pos[2][t] < 0:
                return t

    candidates=[]
    for t in range(4):
        x = state.pos[2][t]
        if x < 0: continue
        if x >= PATH_LEN and decode_home(x)[1]==HOME_LEN-1:
            continue
        candidates.append((t, distance_to_goal(2,x)))

    if not candidates:
        return 0

    return min(candidates, key=lambda e:e[1])[0]

# ================= LOGGER =================
class Logger:
    def __init__(self):
        self.rows=[]
    def push(self,dice,moves):
        self.rows.append({"dice":dice,"moves":moves})

# ================= DRAW =================
def draw_grid():
    for r in range(GRID):
        for c in range(GRID):
            pygame.draw.rect(SCREEN,GRAY,(c*CELL,r*CELL,CELL,CELL),1)

def draw_path():
    for i,(c,r) in enumerate(PATH):
        color=WHITE
        if i==1: color=RED
        if i==13: color=BLUE
        if i==31: color=GREEN
        pygame.draw.rect(SCREEN,color,(c*CELL,r*CELL,CELL,CELL))
        pygame.draw.rect(SCREEN,BLACK,(c*CELL,r*CELL,CELL,CELL),1)
        SCREEN.blit(FONT.render(str(i),True,BLACK),(c*CELL+3,r*CELL+3))

def draw_home():
    pygame.draw.rect(SCREEN,(235,235,200),(6*CELL,6*CELL,3*CELL,3*CELL))
    pygame.draw.rect(SCREEN,BLACK,(6*CELL,6*CELL,3*CELL,3*CELL),2)
    SCREEN.blit(FONT.render("HOME",True,BLACK),(6*CELL+CELL,7*CELL))

def draw_tokens(state):
    offs=[(-10,-10),(10,-10),(-10,10),(10,10)]
    for p in range(3):
        for i in range(4):
            x=state.pos[p][i]
            if x<0:
                if p==0: c,r=PATH[1]; r+=1
                elif p==1: c,r=PATH[13]; c-=1
                else: c30,r30=PATH[30]; c=c30+1; r=r30
            elif x<PATH_LEN:
                c,r=PATH[(START[p]+x)%PATH_LEN]
            else:
                _,h=decode_home(x); c,r=HOME_LANES[p][h]
            cx=c*CELL+CELL//2+offs[i][0]
            cy=r*CELL+CELL//2+offs[i][1]
            pygame.draw.circle(SCREEN,COLORS[p],(cx,cy),CELL//2-6)
            SCREEN.blit(FONT.render(f"T{i+1}",True,WHITE),(cx-6,cy-6))

def draw_panel(logger,dice,auto):
    x=LEFT_W+10
    pygame.draw.rect(SCREEN,PANEL_BG,(LEFT_W,0,PANEL_W,WINDOW_H))
    SCREEN.blit(BIG.render("Logs",True,BLACK),(x,10))
    SCREEN.blit(FONT.render(
        f"Dice: BFS={dice.get(0,'-')} DFS={dice.get(1,'-')} A*={dice.get(2,'-')}",
        True,BLACK),(x,40))

    y=80
    headers=["Strategy","Dice","t1","t2","t3","t4"]
    widths=[80,40,70,70,70,70]
    cx=x
    for h,w in zip(headers,widths):
        SCREEN.blit(FONT.render(h,True,BLACK),(cx,y))
        cx+=w
    y+=24

    LOG_BOTTOM=WINDOW_H-140
    for row in logger.rows[-10:]:
        for p in range(3):
            if y>LOG_BOTTOM: break
            cx=x
            SCREEN.blit(FONT.render(NAMES[p],True,BLACK),(cx,y)); cx+=widths[0]
            SCREEN.blit(FONT.render(str(row["dice"][p]),True,BLACK),(cx,y)); cx+=widths[1]
            moved={t:(a,b) for t,a,b in row["moves"][p]}
            for t in range(4):
                a,b=moved.get(t,(0,0))
                SCREEN.blit(FONT.render(f"{a}→{b}",True,BLACK),(cx,y))
                cx+=widths[2]
            y+=18

    by=WINDOW_H-120
    nr=pygame.Rect(x,by,140,40)
    at=pygame.Rect(x+160,by,140,40)
    pygame.draw.rect(SCREEN,(200,200,200),nr); pygame.draw.rect(SCREEN,BLACK,nr,1)
    pygame.draw.rect(SCREEN,(200,200,200),at); pygame.draw.rect(SCREEN,BLACK,at,1)
    SCREEN.blit(FONT.render("Next Round",True,BLACK),(x+15,by+12))
    SCREEN.blit(FONT.render(f"Auto: {'ON' if auto else 'OFF'}",True,BLACK),(x+185,by+12))
    return nr,at

# ================= MAIN =================
state=State()
logger=Logger()
round_dice={}
first=True
auto=False
last=0

nr=pygame.Rect(0,0,0,0)
at=pygame.Rect(0,0,0,0)

def simulate_round():
    global first,round_dice
    dice=6 if first else random.randint(1,6)
    first=False
    round_dice={0:dice,1:dice,2:dice}

    moves={0:[],1:[],2:[]}

    t=choose_bfs(state,dice)
    if t is not None:
        moves[0].append((t,*move_token(state,0,t,dice)))

    t=choose_dfs(state)
    moves[1].append((t,*move_token(state,1,t,dice)))

    t=choose_astar(state,dice)
    moves[2].append((t,*move_token(state,2,t,dice)))

    logger.push(round_dice,moves)

running=True
while running:
    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            running=False
        if e.type==pygame.MOUSEBUTTONDOWN:
            if nr.collidepoint(e.pos): simulate_round()
            elif at.collidepoint(e.pos): auto=not auto

    if auto and time.time()-last>AUTO_DELAY:
        simulate_round(); last=time.time()

    SCREEN.fill(WHITE)
    draw_grid(); draw_path(); draw_home(); draw_tokens(state)
    nr,at=draw_panel(logger,round_dice,auto)
    pygame.display.flip()
    CLOCK.tick(FPS)

pygame.quit()
sys.exit()