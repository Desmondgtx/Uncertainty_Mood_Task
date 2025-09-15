import pygame
from datetime import datetime
import os
import sys
import csv
import random
from itertools import zip_longest
from scipy.stats import bernoulli
from collections import OrderedDict
import asyncio
import pyautogui
from pylsl import StreamInfo, StreamOutlet
from pupil_labs.realtime_api import Device, Network, StatusUpdateNotifier
from pupil_labs.realtime_api.models import Recording

# MARCADORES 
MARKERS = {
    # Eventos de estímulo
    'STIM_START': 100,          # Inicio de presentación del par de símbolos
    'STIM_RESPONSE': 101,       # Respuesta del participante 
    
    # Eventos de confianza
    'CONFIDENCE_START': 120,    # Aparición de la escala de confianza
    # Valores de la respuesta (0-9)
    'CONFIDENCE_0': 110,
    'CONFIDENCE_1': 111,
    'CONFIDENCE_2': 112,
    'CONFIDENCE_3': 113,
    'CONFIDENCE_4': 114,
    'CONFIDENCE_5': 115,
    'CONFIDENCE_6': 116,
    'CONFIDENCE_7': 117,
    'CONFIDENCE_8': 118,
    'CONFIDENCE_9': 119,
    
    # Eventos de feedback
    'FEEDBACK_CORRECT': 130,    # Feedback correcto
    'FEEDBACK_INCORRECT': 131,  # Feedback incorrecto
    
    # Bloques y fases
    'BLOCK_START_PHASE1': 200,  # Inicio de bloque en fase 1 (bloques 1 y 2)
    'BLOCK_END_PHASE1': 201,    # Fin de bloque en fase 1
    'BLOCK_START_PHASE2': 202,  # Inicio de bloque en fase 2 (bloques 3 y 4)
    'BLOCK_END_PHASE2': 203,    # Fin de bloque en fase 2
    
    # Otros eventos
    'EXPERIMENT_START': 254,    # Inicio del experimento
    'EXPERIMENT_END': 255,      # Fin del experimento
}


# Posiciones del mouse para Shimmer
SHIMMER_POSITIONS = {
    'PHASE1_START': (1800, 215),   # Primera casilla - Inicio Phase 1
    'PHASE1_END': (1800, 275),     # Segunda casilla - Fin Phase 1
    'PHASE2_START': (1800, 335),   # Tercera casilla - Inicio Phase 2
    'PHASE2_END': (1800, 395),     # Cuarta casilla - Fin Phase 2
}

# CONFIGURACIÓN ORIGINAL
CONFIG = {
    "GRAY" : (180, 180, 180),
    "BLACK" : (0, 0, 0),
    "RED" : (210, 43, 43),
    "GREEN" : (111, 152, 0),
    "BLUE" : (10, 97, 195),
    "SIZE" : (1050, 700),
    "DB" : None,
    "FPS" : 60,
    "SCR" : None,
    "RECT" : None,
    "WIDTH" : None,
    "HEIGHT" : None,
    "PATH" : None,
    "FILE" : None,
    "Font" : None,
    "TitleFont" : None,
    "FeedbackFont" : None,
    "MarkFont" : None,
    "StimFont" : None,
    "FixFont" : None,
    "TicksFont" : None,
    "DATAPATH" : None,
    "continue" : 0,
    "starter" : 0,
    "quit" : 0,
    "stimulus" : [],
    "pairs" : []
}

CACHE = {
    "id" : None,
    "response" : None,
    "choice" : None,
    "reward" : None,
    "phase" : 0,
    "block" : 0,
    "trial" : 0,
    "position" : None,
    "continue" : True,
}

RESULTS = OrderedDict([
    ("id", []), 
    ("phase", []), 
    ("block", []), 
    ("trial", []), 
    ("pairs", []), 
    ("stimulus", []), 
    ("responses", []), 
    ("rts", []), 
    ("reward", []), 
    ("confidence", []), 
])

STIMULUS = {
    'AB': ['むふ', [0.50, 0.50],[0.20, 0.20]],
    "CD": ['るょ', [0.50, 0.50], [0.80, 0.80]],
    "EF": ['ぽれ', [0.80, 0.20],[0.20, 0.80]],
    "GH": ['ゆぎ', [0.20, 0.80],[0.80, 0.20]]
}

INSTRUCTIONS = [
    """A continuación aparecerán una serie de pares de símbolos,
uno a la derecha y otro a la izquierda de la pantalla.

Para elegir un símbolo, debe mover la marca azul utilizando
la RUEDA DEL RATÓN:
• Gire la rueda hacia ARRIBA para mover a la izquierda
• Gire la rueda hacia ABAJO para mover a la derecha

Para confirmar su elección, PRESIONE LA RUEDA DEL RATÓN
(haga clic con el botón central).""",
    
    """Luego de cada elección se le solicitará indicar
la confianza que tiene en que su respuesta es correcta.

Para ajustar su nivel de confianza (del 0 al 9):
• Gire la RUEDA DEL RATÓN hacia ARRIBA o ABAJO
  para mover el indicador en la escala
• PRESIONE LA RUEDA para confirmar su respuesta

Al finalizar cada decisión, se le entregará retroalimentación
CORRECTO o INCORRECTO, y se presentará un nuevo par de símbolos.""",
    
    """Su objetivo es encontrar para cada par de símbolos,
el mejor de ellos.

Pero tenga cuidado: No existe un símbolo que SIEMPRE
sea mejor que otro, pero sí existen símbolos que son
mejores LA MAYOR PARTE DEL TIEMPO.

Para descubrir cuáles son, debe aprender por ENSAYO Y
ERROR cuál es el mejor LA MAYORÍA de las veces.

Recuerde: Use la RUEDA DEL RATÓN para navegar
y PRESIÓNELA para confirmar."""
]

# VARIABLES DE CONEXIÓN 
outlet = None  # Para LSL (EEG)
pupil_device = None  # Para Pupil Labs
SHIMMER_ENABLED = True  # Shimmer siempre habilitado si pyautogui funciona

# FUNCIONES DE CONEXIÓN Y ENVÍO DE MARCADORES

async def send_trigger_unified(trigger, include_shimmer=False, shimmer_position=None):
    """
    Envía triggers simultáneamente a los sistemas conectados.
    Usando el mismo formato que funciona en el script de videos.
    """
    print(f"\n→ Sending marker {trigger}")
    
    # 1. Enviar a EEG vía LSL
    if outlet:
        try:
            outlet.push_sample([trigger])
            print(f'  [EEG] Trigger {trigger} sent')
        except Exception as e:
            print(f'  [EEG] Error: {e}')
    
    # 2. Enviar a Pupil Labs
    if pupil_device:
        try:
            await pupil_device.send_event(str(trigger))
            print(f'  [Eyetracker] Event {trigger} sent')
        except Exception as e:
            print(f'  [Eyetracker] Error: {e}')
    
    # 3. Enviar a Shimmer si es necesario
    if include_shimmer and shimmer_position and SHIMMER_ENABLED:
        try:
            position = SHIMMER_POSITIONS[shimmer_position]
            pyautogui.moveTo(position[0], position[1], duration=0.1)
            pyautogui.click()
            print(f'  [Shimmer] Marker sent at {shimmer_position}: {position}')
        except Exception as e:
            print(f'  [Shimmer] Error: {e}')

# FUNCIONES DEL EXPERIMENTO 

def flatten(xss):
    return [x for xs in xss for x in xs]

def TextObject(text, font, width, height, color):
    paragraphSize = (width, height)
    fontSize = font.get_height()
    paragraphSurface = pygame.Surface(paragraphSize)
    paragraphSurface.fill((255, 255, 255))
    paragraphSurface.set_colorkey((255, 255, 255))
    splitLines = text.splitlines()
    offSet = (paragraphSize[1] - len(splitLines) * (fontSize + 1)) // 2
    for idx, line in enumerate(splitLines):
        currentTextline = font.render(line, False, color)
        currentPosition = ((paragraphSize[0] - currentTextline.get_width()) // 2, idx * fontSize + offSet) 
        paragraphSurface.blit(currentTextline, currentPosition)
    return paragraphSurface

def SaveOutputs(filename, resultsdict):
    with open(os.path.join(CONFIG["DATAPATH"], filename), 'w', newline="") as file:
        w = csv.writer(file, delimiter=';')
        w.writerow(resultsdict.keys())
        w.writerows(zip_longest(*resultsdict.values()))

def QuitEvent():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            asyncio.run(ExitTask())
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                CONFIG["quit"] = 1

def StartEvent():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            asyncio.run(ExitTask())
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                CONFIG["starter"] = 1

def InstructionNavigationEvent():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            asyncio.run(ExitTask())
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                return "PREV"
            elif event.key == pygame.K_RIGHT:
                return "NEXT"
            elif event.key == pygame.K_RETURN:
                return "START"
    return None

def DrawInstructions():
    current_page = 0
    total_pages = len(INSTRUCTIONS)
    
    textkargs = {
        "font": CONFIG["InstructionFont"],
        "width": CONFIG["WIDTH"],
        "height": CONFIG["HEIGHT"] - 100,
        "color": CONFIG["BLACK"]
    }
    
    navkargs = {
        "font": CONFIG["NavigationFont"],
        "width": CONFIG["WIDTH"],
        "height": 50,
        "color": CONFIG["BLUE"]
    }
    
    CENTERX, CENTERY = CONFIG["RECT"].centerx, CONFIG["RECT"].centery
    X, Y = CENTERX - (CONFIG["WIDTH"] // 2), CENTERY - (CONFIG["HEIGHT"] // 2)
    
    while True:
        CONFIG["SCR"].fill(CONFIG["GRAY"])
        
        title_text = f"INSTRUCCIONES ({current_page + 1}/{total_pages})"
        title_surface = CONFIG["TitleFont"].render(title_text, True, CONFIG["BLACK"])
        title_x = CENTERX - title_surface.get_width() // 2
        CONFIG["SCR"].blit(title_surface, (title_x, 50))
        
        instruction_text = TextObject(INSTRUCTIONS[current_page], **textkargs)
        CONFIG["SCR"].blit(instruction_text, (X, Y - 30))
        
        if current_page == 0:
            nav_text = "Siguiente [→]"
        elif current_page == total_pages - 1:
            nav_text = "Anterior [←]                    Comenzar [Enter]"
        else:
            nav_text = "Anterior [←]                    Siguiente [→]"
        
        nav_surface = TextObject(nav_text, **navkargs)
        CONFIG["SCR"].blit(nav_surface, (X, CONFIG["RECT"].bottom - 100))
        
        pygame.display.flip()
        
        action = InstructionNavigationEvent()
        if action == "PREV" and current_page > 0:
            current_page -= 1
        elif action == "NEXT" and current_page < total_pages - 1:
            current_page += 1
        elif action == "START" and current_page == total_pages - 1:
            break

def StartTask():
    textkargs = {"font": CONFIG["Font"], "width": CONFIG["WIDTH"], "height": CONFIG["HEIGHT"], "color": CONFIG["BLACK"]}
    TEXT = "BIENVENIDO\n\nPresione [ENTER] para continuar"
    CONFIG["starter"] = 0
    CONFIG["SCR"].fill(CONFIG["GRAY"])
    TextStart = TextObject(TEXT, **textkargs)
    X, Y = CONFIG["RECT"].centerx - (CONFIG["WIDTH"] // 2), CONFIG["RECT"].centery - (CONFIG["HEIGHT"] // 2)

    t0 = pygame.time.get_ticks()
    MIN_TIME_RESPONSE = 500
    while CONFIG["starter"] != 1:
        if (pygame.time.get_ticks() - t0) > MIN_TIME_RESPONSE:
            StartEvent()
        else:
            pygame.event.clear()

        CONFIG["SCR"].blit(TextStart, (X, Y))
        pygame.display.flip()

def GetFeedback(cue):
    choice = CACHE['choice']
    phase = CACHE['phase']
    reward_prob = STIMULUS[cue][phase][choice]
    reward = bernoulli.rvs(reward_prob, size=1)[0]
    return reward

def GetPosition(LAST_POS, KEYPRESS, KEYLIMIT):
    LEFT_LIMIT, RIGHT_LIMIT = KEYLIMIT
    if KEYPRESS == 'LEFT':
        if LAST_POS == LEFT_LIMIT:
            CUR_POS = LAST_POS
        else:
            CUR_POS = LAST_POS - 1
    elif KEYPRESS == 'RIGHT':
        if LAST_POS == RIGHT_LIMIT:
            CUR_POS = LAST_POS
        else:
            CUR_POS = LAST_POS + 1
    else:
        CUR_POS = LAST_POS
    return CUR_POS

def DrawEmpty(duration):
    CONFIG["SCR"].fill(CONFIG["GRAY"])
    STARTTIME = pygame.time.get_ticks() / 1000
    while (pygame.time.get_ticks() / 1000) - STARTTIME < duration:
        pygame.display.flip()

def DrawFix():
    DURATION = 1.0
    textkargs = {"font": CONFIG["FixFont"], "width": CONFIG["WIDTH"], "height": CONFIG["HEIGHT"], "color": CONFIG["BLACK"]}
    CENTERX, CENTERY = CONFIG["RECT"].centerx, CONFIG["RECT"].centery
    X, Y = CENTERX - (CONFIG["WIDTH"] // 2), CENTERY - (CONFIG["HEIGHT"] // 2)

    TextFix = TextObject("+", **textkargs)
    CONFIG["SCR"].fill(CONFIG["GRAY"])

    STARTTIME = pygame.time.get_ticks() / 1000
    while (pygame.time.get_ticks() / 1000) - STARTTIME < DURATION:
        CONFIG["SCR"].blit(TextFix, (X, Y))
        pygame.display.flip()

def ScrollSliderEvent(KEYLIMIT):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # SCROLL UP
                CACHE["continue"] = True
                CACHE["position"] = GetPosition(CACHE["position"], "LEFT", KEYLIMIT)
            elif event.button == 5:  # SCROLL DOWN
                CACHE["continue"] = True
                CACHE["position"] = GetPosition(CACHE["position"], "RIGHT", KEYLIMIT)
            elif event.button == 2:  # SCROLL BUTTON CLICK
                CACHE["continue"] = False
            else:
                CACHE["continue"] = True

# FUNCIONES ASYNC DEL EXPERIMENTO (PUPIL EYETRACKER)

async def InitTask():
    """Inicialización async del experimento - ORDEN CORREGIDO"""
    global pupil_device, outlet
    
    print("\n" + "="*50)
    print("INITIALIZING DEVICE CONNECTIONS")
    print("="*50)
    
    # PASO 1:
    # 1. Inicializar LSL (EEG) - USANDO LA CONFIGURACIÓN QUE FUNCIONA
    print("\n1. Creating LSL stream for EEG (EMOTIV)...")
    info = StreamInfo(name="TriggerStream",
                      type="Markers",
                      channel_count=1,
                      channel_format="int32", 
                      source_id="TaskNotebook") 
    outlet = StreamOutlet(info)
    print('✓ LSL stream created successfully')
    print('  Please connect to EMOTIV application now...')
    input("  Press ENTER when EMOTIV is connected...")
    
    # 2. Conectar con Pupil Labs
    print("\n2. Connecting to Eyetracker (Pupil Labs)...")
    print("   Searching for device (10 seconds)...")
    
    async with Network() as network:
        dev_info = await network.wait_for_new_device(timeout_seconds=10)
    
    if dev_info is None:
        print("✗ No Pupil Labs device found. Continuing without eye-tracking...")
        pupil_device = None
    else:
        pupil_device = Device.from_discovered_device(dev_info)
        await pupil_device.__aenter__()
        # Iniciar grabación
        recording_id = await pupil_device.recording_start()
        print(f"✓ Pupil Labs connected (Recording ID: {recording_id})")
    
    # 3. Verificar Shimmer
    print("\n3. Checking Shimmer markers...")
    try:
        current_pos = pyautogui.position()
        print(f'✓ Shimmer markers ready (mouse at {current_pos})')
    except:
        print('✗ Shimmer markers disabled')
        global SHIMMER_ENABLED
        SHIMMER_ENABLED = False
    
    print("\n" + "="*50)
    print("DEVICE INITIALIZATION COMPLETE")
    print(f"EEG (LSL): ✓ Connected")
    print(f"Eyetracker: {'✓ Connected' if pupil_device else '✗ Disabled'}")
    print(f"Shimmer: {'✓ Ready' if SHIMMER_ENABLED else '✗ Disabled'}")
    print("="*50 + "\n")
    
    #  PASO 2: PEDIR ID
    id_subject = input("Please enter participant ID: ")
    CACHE["id"] = id_subject
    CONFIG["FILE"] = str(id_subject) + "_data_" + datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + '.csv'
    CONFIG["PATH"] = os.path.abspath(os.curdir)
    CONFIG["DATAPATH"] = os.path.join(CONFIG["PATH"], "data")

    if not os.path.exists(CONFIG["DATAPATH"]):
        os.makedirs(CONFIG["DATAPATH"])
    
    input("Press ENTER to start the experiment...")
    
    # Inicializar pygame
    pygame.init()
    infoObject = pygame.display.Info()
    CONFIG["SIZE"] = (infoObject.current_w, infoObject.current_h)
    CONFIG["SCR"] = pygame.display.set_mode(CONFIG["SIZE"], pygame.FULLSCREEN)
    pygame.mouse.set_visible(True)
    pygame.display.flip()
    clock = pygame.time.Clock()
    clock.tick(CONFIG["FPS"])

    # Configurar fuentes
    CONFIG["Font"] = pygame.font.SysFont("Arial", 30)
    CONFIG["FixFont"] = pygame.font.SysFont("Arial", 30)
    CONFIG["TitleFont"] = pygame.font.SysFont("Arial", 30)
    CONFIG["FeedbackFont"] = pygame.font.SysFont("Arial", 30, bold=True)
    CONFIG["MarkFont"] = pygame.font.SysFont("Arial", 30)
    CONFIG["TicksFont"] = pygame.font.SysFont("Arial", 40)
    CONFIG["LabsFont"] = pygame.font.SysFont("Arial", 25)
    CONFIG["InstructionFont"] = pygame.font.SysFont("Arial", 28)
    CONFIG["NavigationFont"] = pygame.font.SysFont("Arial", 24)
    CONFIG["StimFont"] = pygame.font.Font("umeboshi.ttf", 100)
    CONFIG["Stim2Font"] = pygame.font.Font("umeboshi.ttf", 60)

    CONFIG["RECT"] = CONFIG["SCR"].get_rect()
    CONFIG["WIDTH"] = CONFIG["SIZE"][0] - (CONFIG["SIZE"][0] // 10)
    CONFIG["HEIGHT"] = CONFIG["SIZE"][1] - (CONFIG["SIZE"][1] // 10)

async def ExitTask():
    """Cierre async del experimento"""
    global pupil_device
    
    # Enviar marcador de fin
    await send_trigger_unified(MARKERS['EXPERIMENT_END'])
    
    # Cerrar conexión con Pupil Labs si está activa
    if pupil_device:
        try:
            await pupil_device.recording_stop_and_save()
            await pupil_device.__aexit__(None, None, None)
            print("✓ Pupil Labs recording saved and closed")
        except:
            pass
    
    pygame.quit()
    sys.exit()

async def LoadStimulus(phase, block):
    """Carga de estímulos con marcadores async"""
    CACHE['phase'] = phase
    CACHE['block'] = block
    
    # Enviar marcador de inicio de bloque
    if phase == 1:
        if block == 1:
            await send_trigger_unified(MARKERS['BLOCK_START_PHASE1'], 
                                     include_shimmer=True, 
                                     shimmer_position='PHASE1_START')
        else:
            await send_trigger_unified(MARKERS['BLOCK_START_PHASE1'])
    else:
        if block == 1:
            await send_trigger_unified(MARKERS['BLOCK_START_PHASE2'], 
                                     include_shimmer=True, 
                                     shimmer_position='PHASE2_START')
        else:
            await send_trigger_unified(MARKERS['BLOCK_START_PHASE2'])

    items = []
    for i in range(8):
        items += [['AB', "EF"], ["CD", "GH"]]
    for i in range(2):
        items += [["AB", "GH"], ["CD", "EF"]]

    random.shuffle(items)
    pairs = [[''.join(s), ''.join(s)] for s in items]
    items = flatten(items)
    pairs = flatten(pairs)

    CONFIG["stimulus"] = items
    CONFIG["pairs"] = pairs

async def BreakTask():
    """Pausa async entre bloques"""
    textkargs = {"font": CONFIG["Font"], "width": CONFIG["WIDTH"], "height": CONFIG["HEIGHT"], "color": CONFIG["BLACK"]}
    TEXT = "PAUSA\n\nTome un breve momento para descansar.\n\nPresione [ENTER] para continuar"
    CONFIG["starter"] = 0
    CONFIG["SCR"].fill(CONFIG["GRAY"])
    TextStart = TextObject(TEXT, **textkargs)
    X, Y = CONFIG["RECT"].centerx - (CONFIG["WIDTH"] // 2), CONFIG["RECT"].centery - (CONFIG["HEIGHT"] // 2)
    
    # Enviar marcador de fin de bloque
    phase = CACHE['phase']
    if phase == 1:
        await send_trigger_unified(MARKERS['BLOCK_END_PHASE1'])
    else:
        await send_trigger_unified(MARKERS['BLOCK_END_PHASE2'])
    
    t0 = pygame.time.get_ticks()
    MIN_TIME_RESPONSE = 500
    while CONFIG["starter"] != 1:
        if (pygame.time.get_ticks() - t0) > MIN_TIME_RESPONSE:
            StartEvent()
        else:
            pygame.event.clear()
        CONFIG["SCR"].blit(TextStart, (X, Y))
        pygame.display.flip()
        await asyncio.sleep(0.01) 

async def MidBreakTask():
    """Pausa async a mitad del experimento"""
    textkargs = {"font": CONFIG["Font"], "width": CONFIG["WIDTH"], "height": CONFIG["HEIGHT"], "color": CONFIG["BLACK"]}
    TEXT = "¡LLEVAS MÁS DE LA MITAD COMPLETADA!\n\nTome un breve momento para descansar.\n\nPresione [ENTER] para continuar"
    CONFIG["starter"] = 0
    CONFIG["SCR"].fill(CONFIG["GRAY"])
    TextStart = TextObject(TEXT, **textkargs)
    X, Y = CONFIG["RECT"].centerx - (CONFIG["WIDTH"] // 2), CONFIG["RECT"].centery - (CONFIG["HEIGHT"] // 2)
    
    # Enviar marcador de fin de fase 1
    await send_trigger_unified(MARKERS['BLOCK_END_PHASE1'], 
                             include_shimmer=True, 
                             shimmer_position='PHASE1_END')
    
    t0 = pygame.time.get_ticks()
    MIN_TIME_RESPONSE = 500
    while CONFIG["starter"] != 1:
        if (pygame.time.get_ticks() - t0) > MIN_TIME_RESPONSE:
            StartEvent()
        else:
            pygame.event.clear()
        CONFIG["SCR"].blit(TextStart, (X, Y))
        pygame.display.flip()
        await asyncio.sleep(0.01)

async def QuitTask():
    """Pantalla final async"""
    textkargs = {"font": CONFIG["Font"], "width": CONFIG["WIDTH"], "height": CONFIG["HEIGHT"], "color": CONFIG["BLACK"]}
    TEXT = "El experimento ha finalizado.\n\nMuchas gracias por participar.\n\nPresione [Q] para salir"
    CONFIG["quit"] = 0
    CONFIG["SCR"].fill(CONFIG["GRAY"])
    TextQuit = TextObject(TEXT, **textkargs)
    X, Y = CONFIG["RECT"].centerx - (CONFIG["WIDTH"] // 2), CONFIG["RECT"].centery - (CONFIG["HEIGHT"] // 2)
    
    # Enviar marcador de fin de fase 2
    await send_trigger_unified(MARKERS['BLOCK_END_PHASE2'], 
                             include_shimmer=True, 
                             shimmer_position='PHASE2_END')
    
    t0 = pygame.time.get_ticks()
    MIN_TIME_RESPONSE = 500
    while CONFIG["quit"] != 1:
        if (pygame.time.get_ticks() - t0) > MIN_TIME_RESPONSE:
            QuitEvent()
        else:
            pygame.event.clear()
        CONFIG["SCR"].blit(TextQuit, (X, Y))
        pygame.display.flip()
        await asyncio.sleep(0.01)

async def DrawBinaryChoiceRect(stimulus, pairs):
    """Presentación async de elección binaria"""
    textkargs = {"font": CONFIG["TitleFont"], "width": CONFIG["WIDTH"], "height": CONFIG["HEIGHT"], "color": CONFIG["BLACK"]}
    stimkargs = {"font": CONFIG["StimFont"], "width": CONFIG["WIDTH"], "height": CONFIG["HEIGHT"], "color": CONFIG["BLACK"]}
    markkargs = {"font": CONFIG["MarkFont"], "width": CONFIG["WIDTH"], "height": CONFIG["HEIGHT"], "color": CONFIG["BLUE"]}
    instruckkargs = {"font": CONFIG["NavigationFont"], "width": CONFIG["WIDTH"], "height": 50, "color": CONFIG["BLUE"]}
    
    CENTERX, CENTERY = CONFIG["RECT"].centerx, CONFIG["RECT"].centery
    X, Y = CENTERX - (CONFIG["WIDTH"] // 2), CENTERY - (CONFIG["HEIGHT"] // 2)

    KEYLIMIT = (0, 1)
    CUE = STIMULUS[stimulus][0]
    STIM = CUE[0] + "   " + CUE[1]

    CACHE["continue"] = True
    INIT_POSITION = random.randint(KEYLIMIT[0], KEYLIMIT[1])
    CACHE["position"] = INIT_POSITION

    CONFIG["SCR"].fill(CONFIG["GRAY"])
    TextMark = TextObject("▼", **markkargs)
    TextStim = TextObject(STIM, **stimkargs)
    TextFix = TextObject("+", **textkargs)
    TextInstruct = TextObject("Gire la rueda del ratón para mover - Presione la rueda para confirmar", **instruckkargs)

    POS, RPOS = [X-125, X+125], [CENTERX-185, CENTERX+60]
    
    # Enviar marcador de inicio de estímulo
    await send_trigger_unified(MARKERS['STIM_START'])

    t0 = pygame.time.get_ticks()
    MIN_TIME_RESPONSE = 300
    while CACHE["continue"]:
        if (pygame.time.get_ticks() - t0) > MIN_TIME_RESPONSE:
            ScrollSliderEvent(KEYLIMIT)
        else:
            pygame.event.clear()

        CONFIG["SCR"].fill(CONFIG["GRAY"])
        pygame.draw.rect(CONFIG["SCR"], CONFIG["BLUE"], [RPOS[CACHE["position"]], CENTERY-70, 130, 150], 2)
        CONFIG["SCR"].blit(TextMark, (POS[CACHE["position"]], Y-100))
        CONFIG["SCR"].blit(TextStim, (X, Y))
        CONFIG["SCR"].blit(TextFix, (X, Y))
        CONFIG["SCR"].blit(TextInstruct, (X, CONFIG["RECT"].bottom - 100))
        pygame.display.flip()
        await asyncio.sleep(0.001)  # Permitir procesamiento async

    rt = pygame.time.get_ticks() - t0
    print(f'  Choice RT: {rt}ms')
    
    # Enviar marcador de respuesta
    await send_trigger_unified(MARKERS['STIM_RESPONSE'])

    CACHE["choice"] = CACHE["position"]

    RESULTS["id"].append(CACHE["id"])
    RESULTS["phase"].append(CACHE["phase"])
    RESULTS["block"].append(CACHE["block"])
    RESULTS["trial"].append(CACHE["trial"])
    RESULTS["pairs"].append(pairs)
    RESULTS["stimulus"].append(stimulus)
    RESULTS["responses"].append(CACHE["position"])
    RESULTS["rts"].append(rt)

async def DrawConfidenceRatingRect(stimulus):
    """Escala de confianza async"""
    textkargs = {"font": CONFIG["TitleFont"], "width": CONFIG["WIDTH"], "height": CONFIG["HEIGHT"], "color": CONFIG["BLACK"]}
    tickskargs = {"font": CONFIG["TicksFont"], "width": CONFIG["WIDTH"], "height": CONFIG["HEIGHT"], "color": CONFIG["BLACK"]}
    labskargs = {"font": CONFIG["LabsFont"], "width": CONFIG["WIDTH"], "height": CONFIG["HEIGHT"], "color": CONFIG["BLACK"]}
    markkargs = {"font": CONFIG["MarkFont"], "width": CONFIG["WIDTH"], "height": CONFIG["HEIGHT"], "color": CONFIG["BLUE"]}
    stimkargs = {"font": CONFIG["Stim2Font"], "width": CONFIG["WIDTH"], "height": CONFIG["HEIGHT"], "color": CONFIG["BLACK"]}
    instruckkargs = {"font": CONFIG["NavigationFont"], "width": CONFIG["WIDTH"], "height": 50, "color": CONFIG["BLUE"]}

    CENTERX, CENTERY = CONFIG["RECT"].centerx, CONFIG["RECT"].centery
    X, Y = CENTERX - (CONFIG["WIDTH"] // 2), CENTERY - (CONFIG["HEIGHT"] // 2)

    KEYLIMIT = (0, 9)
    TITLE = "Confianza en su respuesta"
    TICKS = "   ".join(["|", "|", "|", "|", "|", "|", "|", "|", "|", "|"])
    LABS = "    ".join(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])

    CUE = STIMULUS[stimulus][0]
    STIM = CUE[0] + "   " + CUE[1]

    CACHE["continue"] = True
    CACHE["position"] = random.randint(KEYLIMIT[0], KEYLIMIT[1])
    POS = [X-193, X-150, X-106, X-63, X-22, X+22, X+63, X+106, X+150, X+193]
    RPOS = [CENTERX-120, CENTERX+30]

    TextMark = TextObject("▼", **markkargs)
    TextTitle = TextObject(TITLE, **textkargs)
    TextTicks = TextObject(TICKS, **tickskargs)
    TextLabs = TextObject(LABS, **labskargs)
    TextStim = TextObject(STIM, **stimkargs)
    TextInstruct = TextObject("Gire la rueda para ajustar - Presione la rueda para confirmar", **instruckkargs)
    
    # Enviar marcador de inicio de escala de confianza
    await send_trigger_unified(MARKERS['CONFIDENCE_START'])
    
    t0 = pygame.time.get_ticks()
    MIN_TIME_RESPONSE = 300
    while CACHE["continue"]:
        if (pygame.time.get_ticks() - t0) > MIN_TIME_RESPONSE:
            ScrollSliderEvent(KEYLIMIT)
        else:
            pygame.event.clear()

        CONFIG["SCR"].fill(CONFIG["GRAY"])
        CONFIG["SCR"].blit(TextMark, (POS[CACHE["position"]], Y+50))
        CONFIG["SCR"].blit(TextTitle, (X, Y-280))
        CONFIG["SCR"].blit(TextTicks, (X, Y+100))
        CONFIG["SCR"].blit(TextLabs, (X, Y+150))
        CONFIG["SCR"].blit(TextStim, (X, Y-80))
        CONFIG["SCR"].blit(TextInstruct, (X, CONFIG["RECT"].bottom - 100))
        pygame.draw.rect(CONFIG["SCR"], CONFIG["BLUE"], [RPOS[CACHE["choice"]], CENTERY-130, 90, 110], 2)
        pygame.draw.line(CONFIG["SCR"], CONFIG["BLACK"], (CENTERX-193, CENTERY+100), (CENTERX+193, CENTERY+100), 5)
        pygame.display.flip()
        await asyncio.sleep(0.001) 
    
    # Enviar marcador de respuesta de confianza
    confidence_value = CACHE["position"]
    confidence_marker = 110 + confidence_value  # Valores 110-119
    await send_trigger_unified(confidence_marker)
    print(f'  Confidence response: {confidence_value}')

    RESULTS["confidence"].append(CACHE["position"])

async def DrawFeedback(reward):
    """Feedback async con marcadores"""
    DURATION = 0.5
    FEEDBACK, COLOR = ("CORRECTO", CONFIG["GREEN"]) if bool(reward) else ("INCORRECTO", CONFIG["RED"])
    
    # Enviar marcador de feedback
    if bool(reward):
        await send_trigger_unified(MARKERS['FEEDBACK_CORRECT'])
    else:
        await send_trigger_unified(MARKERS['FEEDBACK_INCORRECT'])
    
    textkargs = {"font": CONFIG["FeedbackFont"], "width": CONFIG["WIDTH"], "height": CONFIG["HEIGHT"], "color": COLOR}
    CENTERX, CENTERY = CONFIG["RECT"].centerx, CONFIG["RECT"].centery
    X, Y = CENTERX - (CONFIG["WIDTH"] // 2), CENTERY - (CONFIG["HEIGHT"] // 2)

    CONFIG["SCR"].fill(CONFIG["GRAY"])
    TextFeedback = TextObject(FEEDBACK, **textkargs)

    STARTTIME = pygame.time.get_ticks() / 1000
    while (pygame.time.get_ticks() / 1000) - STARTTIME < DURATION:
        CONFIG["SCR"].blit(TextFeedback, (X, Y))
        pygame.display.flip()
        await asyncio.sleep(0.001)

    RESULTS["reward"].append(reward)

async def MainLoopTask():
    """Loop principal async de trials"""
    for trial, (stimulus, pairs) in enumerate(zip(CONFIG['stimulus'], CONFIG['pairs'])):
        CACHE['trial'] = trial
        print(f"\nTrial {trial+1}/20 - Phase {CACHE['phase']}, Block {CACHE['block']}")
        
        DrawFix()
        await DrawBinaryChoiceRect(stimulus, pairs)
        DrawFix()
        await DrawConfidenceRatingRect(stimulus)
        reward = GetFeedback(stimulus)
        DrawFix()
        await DrawFeedback(reward)
        SaveOutputs(CONFIG["FILE"], RESULTS)

async def RunTask():
    """Función principal async del experimento"""
    global pupil_device
    
    await InitTask()
    StartTask()
    DrawInstructions()
    
    # Enviar marcador de inicio del experimento
    await send_trigger_unified(MARKERS['EXPERIMENT_START'])
    print("\n" + "="*50)
    print("EXPERIMENT STARTED")
    print("="*50)

    # FASE 1 - Bloques 1 y 2
    print("\n>>> PHASE 1 - BLOCK 1")
    await LoadStimulus(phase=1, block=1)
    await MainLoopTask()
    await BreakTask()

    print("\n>>> PHASE 1 - BLOCK 2")
    await LoadStimulus(phase=1, block=2)
    await MainLoopTask()
    await MidBreakTask()

    # FASE 2 - Bloques 3 y 4
    print("\n>>> PHASE 2 - BLOCK 1")
    await LoadStimulus(phase=2, block=1)
    await MainLoopTask()
    await BreakTask()
    
    print("\n>>> PHASE 2 - BLOCK 2")
    await LoadStimulus(phase=2, block=2)
    await MainLoopTask()

    await QuitTask()
    await ExitTask()

if __name__ == '__main__':
    asyncio.run(RunTask())