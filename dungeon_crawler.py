#!/usr/bin/env python3
"""
DUNGEON CRAWLER RPG: The Crypt of Malakor
=========================================
A classic, text-based single-player roguelike adventure game.

Descend into a procedural 3-floor dungeon, fight lethal creatures in
turn-based tactical combat, discover ancient shrines, buy gear from the
wandering merchant, and slay the final Dragon Boss!

Zero external dependencies - runs with pure Python 3.
Run with:   python dungeon_crawler.py
Test with:  python dungeon_crawler.py --test
"""

import os
import random
import sys
import time


# ============================================================================
# COLOR & TERMINAL HELPERS
# ============================================================================

def setup_terminal():
    """Enable ANSI escape codes on Windows and configure UTF-8 encoding."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stdin, "reconfigure"):
        try:
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if os.name == "nt":
        os.system("")


setup_terminal()


def can_color():
    """Detect if the terminal supports ANSI color output."""
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return False
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    return True


USE_COLOR = can_color()


def color(text, code):
    """Wrap text in ANSI color sequence if supported."""
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


# Common ANSI color shortcuts
def c_red(text): return color(text, "1;31")
def c_green(text): return color(text, "1;32")
def c_yellow(text): return color(text, "1;33")
def c_blue(text): return color(text, "1;34")
def c_magenta(text): return color(text, "1;35")
def c_cyan(text): return color(text, "1;36")
def c_white(text): return color(text, "1;37")
def c_dim(text): return color(text, "2;37")
def c_bold(text): return color(text, "1")


def clear_screen(test_mode=False):
    """Clear terminal screen in an interactive session."""
    if test_mode:
        return
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")
    else:
        print("\n" + "=" * 50)


def pause(prompt="Press Enter to continue...", test_mode=False):
    """Wait for user to press Enter."""
    if test_mode or not hasattr(sys.stdin, "isatty") or not sys.stdin.isatty():
        return
    try:
        input(c_dim(f"\n[{prompt}] "))
    except (EOFError, KeyboardInterrupt):
        print()


def get_glyphs():
    """Return appropriate UI glyphs based on terminal encoding support."""
    try:
        "┌─┐█░▼✦".encode(sys.stdout.encoding or "ascii")
        return {
            "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
            "h": "─", "v": "│", "cross": "┼",
            "t_down": "┬", "t_up": "┴", "t_right": "├", "t_left": "┤",
            "fill": "█", "empty": "░",
            "stairs": "▼", "shrine": "✦", "chest": "T", "shop": "$",
            "player": "P", "unexplored": "?", "cleared": "."
        }
    except Exception:
        return {
            "tl": "+", "tr": "+", "bl": "+", "br": "+",
            "h": "-", "v": "|", "cross": "+",
            "t_down": "+", "t_up": "+", "t_right": "+", "t_left": "+",
            "fill": "#", "empty": "-",
            "stairs": ">", "shrine": "*", "chest": "T", "shop": "$",
            "player": "P", "unexplored": "?", "cleared": "."
        }


def make_bar(current, maximum, length=12, fill_color=c_green):
    """Generate a stylized visual ASCII bar (e.g. for HP or MP)."""
    glyphs = get_glyphs()
    fill_char = glyphs["fill"]
    empty_char = glyphs["empty"]
    current = max(0, min(current, maximum))
    fill_len = int((current / maximum) * length) if maximum > 0 else 0
    empty_len = length - fill_len
    bar_str = fill_color(fill_char * fill_len) + c_dim(empty_char * empty_len)
    return f"[{bar_str}] {current}/{maximum}"


# ============================================================================
# HERO & ENEMY CLASSES
# ============================================================================

class Hero:
    """The player character with stats, inventory, and skills."""

    def __init__(self, name, hero_class):
        self.name = name
        self.hero_class = hero_class
        self.level = 1
        self.xp = 0
        self.xp_to_next = 50
        self.gold = 30

        # Class presets
        if hero_class == "Warrior":
            self.max_hp = 120
            self.hp = 120
            self.max_mp = 30
            self.mp = 30
            self.base_attack = 14
            self.defense = 5
            self.crit_rate = 0.12
            self.dodge_rate = 0.05
            self.weapon_name = "Iron Broadsword"
            self.weapon_bonus = 4
            self.armor_name = "Chainmail Vest"
            self.armor_bonus = 3
            self.skills = [
                {
                    "name": "Shield Bash",
                    "cost": 12,
                    "desc": "Heavy strike that stuns the foe for 1 turn",
                    "type": "warrior_bash"
                },
                {
                    "name": "Whirlwind Strike",
                    "cost": 20,
                    "desc": "Brutal slash dealing 200% weapon damage",
                    "type": "warrior_whirlwind"
                }
            ]
        elif hero_class == "Mage":
            self.max_hp = 85
            self.hp = 85
            self.max_mp = 80
            self.mp = 80
            self.base_attack = 10
            self.defense = 2
            self.crit_rate = 0.15
            self.dodge_rate = 0.08
            self.weapon_name = "Apprentice Wand"
            self.weapon_bonus = 5
            self.armor_name = "Silk Robes"
            self.armor_bonus = 1
            self.skills = [
                {
                    "name": "Fireball",
                    "cost": 22,
                    "desc": "Hurls a searing flame for massive damage",
                    "type": "mage_fireball"
                },
                {
                    "name": "Arcane Restoration",
                    "cost": 20,
                    "desc": "Channel mystic energies to restore 40 HP",
                    "type": "mage_heal"
                }
            ]
        else:  # Rogue
            self.max_hp = 95
            self.hp = 95
            self.max_mp = 50
            self.mp = 50
            self.base_attack = 13
            self.defense = 3
            self.crit_rate = 0.30
            self.dodge_rate = 0.22
            self.weapon_name = "Dual Daggers"
            self.weapon_bonus = 5
            self.armor_name = "Leather Jerkin"
            self.armor_bonus = 2
            self.skills = [
                {
                    "name": "Shadow Strike",
                    "cost": 18,
                    "desc": "Guaranteed critical strike from the shadows",
                    "type": "rogue_strike"
                },
                {
                    "name": "Smoke Bomb",
                    "cost": 15,
                    "desc": "Blinds the target, dealing damage and evading next attack",
                    "type": "rogue_smoke"
                }
            ]

        # Consumables
        self.health_potions = 2
        self.mana_potions = 2

        # Progression tracker
        self.monsters_slain = 0
        self.turns_played = 0
        self.chests_opened = 0
        self.boss_slain = False

    @property
    def total_attack(self):
        return self.base_attack + self.weapon_bonus

    @property
    def total_defense(self):
        return self.defense + self.armor_bonus

    def is_alive(self):
        return self.hp > 0

    def heal(self, amount):
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp

    def restore_mp(self, amount):
        old_mp = self.mp
        self.mp = min(self.max_mp, self.mp + amount)
        return self.mp - old_mp

    def take_damage(self, raw_damage):
        mitigated = max(1, raw_damage - (self.total_defense // 2))
        self.hp = max(0, self.hp - mitigated)
        return mitigated

    def gain_xp(self, amount):
        """Add XP and handle level up."""
        self.xp += amount
        leveled_up = False
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.6)
            self.max_hp += 18
            self.max_mp += 12
            self.base_attack += 3
            self.defense += 1
            self.hp = self.max_hp
            self.mp = self.max_mp
            leveled_up = True
        return leveled_up

    def show_sheet(self):
        """Display detailed character sheet."""
        clear_screen()
        print(c_magenta("=" * 56))
        print(c_bold(f"  HERO PROFILE: {self.name} the {self.hero_class}"))
        print(c_magenta("=" * 56))
        print(f" Level: {c_yellow(str(self.level))}   XP: {self.xp}/{self.xp_to_next}   Gold: {c_yellow(str(self.gold))} G")
        print(f" HP: {make_bar(self.hp, self.max_hp, fill_color=c_green)}")
        print(f" MP: {make_bar(self.mp, self.max_mp, fill_color=c_cyan)}")
        print("-" * 56)
        print(f" Base Attack : {self.base_attack}  (+{self.weapon_bonus} from {self.weapon_name}) = {c_bold(str(self.total_attack))}")
        print(f" Base Defense: {self.defense}  (+{self.armor_bonus} from {self.armor_name}) = {c_bold(str(self.total_defense))}")
        print(f" Critical Hit: {int(self.crit_rate * 100)}%   |   Dodge Chance: {int(self.dodge_rate * 100)}%")
        print("-" * 56)
        print(f" Consumables: {c_green(str(self.health_potions))} Health Potions, {c_cyan(str(self.mana_potions))} Mana Potions")
        print(" Active Skills:")
        for idx, skill in enumerate(self.skills, 1):
            print(f"   [{idx}] {c_bold(skill['name'])} (Cost: {c_cyan(str(skill['cost']) + ' MP')}) - {skill['desc']}")
        print(c_magenta("=" * 56))
        pause()


class Monster:
    """Enemies found wandering the dungeon."""

    def __init__(self, name, hp, attack, defense, xp_reward, gold_reward, special_move=None, is_boss=False):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.xp_reward = xp_reward
        self.gold_reward = gold_reward
        self.special_move = special_move
        self.is_boss = is_boss
        self.stunned = False

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, raw_damage):
        mitigated = max(1, raw_damage - (self.defense // 2))
        self.hp = max(0, self.hp - mitigated)
        return mitigated


# Monster Bestiary per Floor
MONSTER_TEMPLATES = {
    1: [
        {"name": "Rabid Cave Bat", "hp": 28, "attack": 9, "defense": 1, "xp": 22, "gold": 12},
        {"name": "Goblin Sneak", "hp": 36, "attack": 11, "defense": 2, "xp": 28, "gold": 18, "special": "Dirty Shrewd Strike"},
        {"name": "Skeleton Warrior", "hp": 46, "attack": 13, "defense": 4, "xp": 35, "gold": 22},
        {"name": "Crypt Zombie", "hp": 55, "attack": 12, "defense": 3, "xp": 38, "gold": 25, "special": "Putrid Bite"},
    ],
    2: [
        {"name": "Corrupted Cultist", "hp": 65, "attack": 16, "defense": 4, "xp": 50, "gold": 35, "special": "Dark Hex"},
        {"name": "Armored Hobgoblin", "hp": 80, "attack": 18, "defense": 7, "xp": 60, "gold": 42},
        {"name": "Phantom Shade", "hp": 70, "attack": 20, "defense": 5, "xp": 65, "gold": 45, "special": "Soul Drain"},
        {"name": "Cave Troll", "hp": 105, "attack": 22, "defense": 6, "xp": 80, "gold": 55, "special": "Ground Slam"},
    ],
    3: [
        {"name": "Abyssal Guard", "hp": 95, "attack": 24, "defense": 8, "xp": 90, "gold": 60},
        {"name": "Flame Demon", "hp": 110, "attack": 27, "defense": 7, "xp": 105, "gold": 75, "special": "Hellfire Burst"},
        {"name": "Dread Knight", "hp": 130, "attack": 28, "defense": 10, "xp": 120, "gold": 85, "special": "Executioner Cleave"},
    ]
}


def create_monster(floor_num):
    """Spawn a thematic monster suitable for the current floor."""
    opts = MONSTER_TEMPLATES[min(floor_num, 3)]
    spec = random.choice(opts)
    return Monster(
        name=spec["name"],
        hp=spec["hp"],
        attack=spec["attack"],
        defense=spec["defense"],
        xp_reward=spec["xp"],
        gold_reward=spec["gold"] + random.randint(0, 8),
        special_move=spec.get("special")
    )


def create_boss():
    """Spawn the Final Boss: Malakor the Void Dragon."""
    return Monster(
        name="Malakor the Void Dragon",
        hp=240,
        attack=32,
        defense=12,
        xp_reward=350,
        gold_reward=250,
        special_move="Cataclysmic Void Breath",
        is_boss=True
    )


# ============================================================================
# DUNGEON MAP & PROCEDURAL GENERATION
# ============================================================================

class Room:
    """A single cell in the dungeon grid."""

    def __init__(self, r, c, room_type="empty"):
        self.r = r
        self.c = c
        self.room_type = room_type  # 'empty', 'monster', 'treasure', 'shop', 'shrine', 'stairs', 'boss'
        self.visited = False
        self.cleared = False
        self.monster = None
        self.treasure_gold = 0
        self.treasure_item = None


class DungeonFloor:
    """A grid of rooms representing one depth of the dungeon."""

    def __init__(self, floor_num, size=4):
        self.floor_num = floor_num
        self.size = size
        self.grid = [[Room(r, c) for c in range(size)] for r in range(size)]
        self.start_pos = (0, 0)
        self.stairs_pos = (size - 1, size - 1)
        self.build_floor()

    def build_floor(self):
        """Place monsters, chests, shrines, shop, and stairs."""
        size = self.size
        all_cells = [(r, c) for r in range(size) for c in range(size)]
        all_cells.remove((0, 0))  # Entrance

        # Final floor puts Boss at the end
        if self.floor_num == 3:
            boss_pos = (size - 1, size - 1)
            all_cells.remove(boss_pos)
            boss_room = self.grid[boss_pos[0]][boss_pos[1]]
            boss_room.room_type = "boss"
            boss_room.monster = create_boss()
            self.stairs_pos = boss_pos
        else:
            stairs_pos = (size - 1, size - 1)
            all_cells.remove(stairs_pos)
            self.grid[stairs_pos[0]][stairs_pos[1]].room_type = "stairs"
            self.stairs_pos = stairs_pos

        random.shuffle(all_cells)

        # Place 1 Merchant Shop
        shop_pos = all_cells.pop()
        self.grid[shop_pos[0]][shop_pos[1]].room_type = "shop"

        # Place 1 Ancient Shrine
        shrine_pos = all_cells.pop()
        self.grid[shrine_pos[0]][shrine_pos[1]].room_type = "shrine"

        # Place 3-4 Treasure Rooms
        chest_count = 3 if size == 4 else 4
        for _ in range(chest_count):
            if not all_cells:
                break
            t_pos = all_cells.pop()
            t_room = self.grid[t_pos[0]][t_pos[1]]
            t_room.room_type = "treasure"
            t_room.treasure_gold = random.randint(20, 45) * self.floor_num
            # Small chance of gear/potion find
            if random.random() < 0.40:
                t_room.treasure_item = "potion"

        # Remaining cells become Monster rooms or empty
        for pos in all_cells:
            r, c = pos
            if random.random() < 0.70:
                self.grid[r][c].room_type = "monster"
                self.grid[r][c].monster = create_monster(self.floor_num)
            else:
                self.grid[r][c].room_type = "empty"

        # Start room is always visited and cleared
        self.grid[0][0].visited = True
        self.grid[0][0].cleared = True

    def render_map(self, player_r, player_c):
        """Print an ASCII mini-map with clear borders and fog of war."""
        glyphs = get_glyphs()
        names = {1: "The Damp Crypts", 2: "The Sunken Catacombs", 3: "The Dragon's Sanctum"}
        floor_name = names.get(self.floor_num, f"Dungeon Floor {self.floor_num}")

        inner_w = self.size * 5 - 1
        print(c_cyan(glyphs["tl"] + glyphs["h"] * inner_w + glyphs["tr"]))
        title = f" FLOOR {self.floor_num}: {floor_name.upper()} "
        print(c_cyan(glyphs["v"]) + c_bold(title.center(inner_w)) + c_cyan(glyphs["v"]))

        sep = (glyphs["h"] * 4 + glyphs["t_down"]) * (self.size - 1) + glyphs["h"] * 4
        print(c_cyan(glyphs["t_right"] + sep + glyphs["t_left"]))

        for r in range(self.size):
            line = c_cyan(glyphs["v"])
            for c in range(self.size):
                room = self.grid[r][c]
                if r == player_r and c == player_c:
                    g = c_yellow(c_bold(" P  "))
                elif not room.visited:
                    g = c_dim(f" {glyphs['unexplored']}  ")
                elif room.room_type == "stairs":
                    g = c_magenta(c_bold(f" {glyphs['stairs']}  "))
                elif room.room_type == "boss":
                    g = c_red(c_bold(" X  ")) if not room.cleared else c_green(" .  ")
                elif room.room_type == "shop":
                    g = c_yellow(f" {glyphs['shop']}  ")
                elif room.room_type == "shrine":
                    g = c_blue(f" {glyphs['shrine']}  ")
                elif room.room_type == "treasure":
                    g = c_yellow(f" {glyphs['chest']}  ") if not room.cleared else c_dim(" .  ")
                elif room.room_type == "monster":
                    g = c_red(" M  ") if not room.cleared else c_dim(" .  ")
                else:
                    g = c_dim(" .  ")
                line += g + c_cyan(glyphs["v"])
            print(line)

            if r < self.size - 1:
                mid_sep = (glyphs["h"] * 4 + glyphs["cross"]) * (self.size - 1) + glyphs["h"] * 4
                print(c_cyan(glyphs["t_right"] + mid_sep + glyphs["t_left"]))
            else:
                bot_sep = (glyphs["h"] * 4 + glyphs["t_up"]) * (self.size - 1) + glyphs["h"] * 4
                print(c_cyan(glyphs["bl"] + bot_sep + glyphs["br"]))

        # Map Legend
        stairs_g = glyphs['stairs']
        shrine_g = glyphs['shrine']
        print(" " + c_dim("Legend:") + f" {c_yellow('P')}=You  {c_red('M')}=Monster  {c_yellow('T')}=Chest  {c_yellow('$')}=Shop  {c_blue(shrine_g)}=Shrine  {c_magenta(stairs_g)}=Stairs  {c_dim('?')}=Hidden")


# ============================================================================
# COMBAT SYSTEM
# ============================================================================

def execute_combat(hero, monster, test_mode=False):
    """Run turn-based tactical combat between Hero and Monster."""
    if not test_mode:
        clear_screen()
    if monster.is_boss:
        print(c_red("=" * 60))
        print(c_bold(c_red("  [!] BOSS ENCOUNTER: MALAKOR THE VOID DRAGON HAS AWOKEN! [!]  ".center(60))))
        print(c_red("=" * 60))
    else:
        print(c_yellow(f"\n[!] A wild {c_bold(monster.name)} blocks your path!\n"))

    turn = 1
    combat_log = []
    smoke_active = False

    while hero.is_alive() and monster.is_alive():
        print("-" * 60)
        # Display Status Bars
        hero_bar = make_bar(hero.hp, hero.max_hp, length=12, fill_color=c_green)
        hero_mp_bar = make_bar(hero.mp, hero.max_mp, length=8, fill_color=c_cyan)
        print(f" {c_bold(hero.name)}: HP {hero_bar} | MP {hero_mp_bar}")

        mon_color = c_red if monster.is_boss else c_yellow
        mon_bar = make_bar(monster.hp, monster.max_hp, length=14, fill_color=mon_color)
        print(f" {c_bold(monster.name)}: HP {mon_bar}")
        print("-" * 60)

        # Recent Combat Log
        if combat_log:
            print(c_dim("Combat Log:"))
            for msg in combat_log[-3:]:
                print(f"  * {msg}")
            print("-" * 60)
            combat_log.clear()

        # Action Menu
        if test_mode:
            cmd = "a"
        else:
            print(f" [A] {c_bold('Attack')}   [S] {c_bold('Skill')}   [H] {c_bold('Health Potion')} ({hero.health_potions})   [M] {c_bold('Mana Potion')} ({hero.mana_potions})   [D] {c_bold('Defend')}   [F] {c_bold('Flee')}")
            cmd = input(c_bold("Choose action: ")).strip().lower()

        hero_acted = False
        defending = False

        if cmd in ("a", "attack", "1"):
            # Regular weapon attack
            dmg = hero.total_attack + random.randint(-2, 3)
            is_crit = random.random() < hero.crit_rate
            if is_crit:
                dmg = int(dmg * 1.8)
                crit_text = c_yellow(" **CRITICAL HIT!**")
            else:
                crit_text = ""

            actual_dmg = monster.take_damage(dmg)
            combat_log.append(f"You struck {monster.name} with {hero.weapon_name} for {c_bold(str(actual_dmg))} damage!{crit_text}")
            hero_acted = True

        elif cmd in ("s", "skill", "2"):
            # Skill selection
            print("\nSelect a skill:")
            for i, sk in enumerate(hero.skills, 1):
                cost_str = c_cyan(f"{sk['cost']} MP")
                print(f"  [{i}] {sk['name']} ({cost_str}) - {sk['desc']}")
            print("  [0] Cancel")
            sk_choice = input("Skill number: ").strip()

            if sk_choice in ("1", "2"):
                chosen_idx = int(sk_choice) - 1
                sk = hero.skills[chosen_idx]
                if hero.mp < sk["cost"]:
                    print(c_red("Not enough MP to cast that!"))
                    if not test_mode:
                        time.sleep(1)
                    continue

                hero.mp -= sk["cost"]
                sk_type = sk["type"]

                if sk_type == "warrior_bash":
                    dmg = int(hero.total_attack * 1.3) + random.randint(2, 5)
                    actual_dmg = monster.take_damage(dmg)
                    monster.stunned = True
                    combat_log.append(f"You bashed {monster.name} for {c_bold(str(actual_dmg))} damage and {c_yellow('STUNNED')} them!")
                elif sk_type == "warrior_whirlwind":
                    dmg = int(hero.total_attack * 2.1) + random.randint(3, 7)
                    actual_dmg = monster.take_damage(dmg)
                    combat_log.append(f"You spun in a violent whirlwind, hitting {monster.name} for {c_bold(str(actual_dmg))} massive damage!")
                elif sk_type == "mage_fireball":
                    dmg = int(hero.total_attack * 2.4) + random.randint(5, 12)
                    actual_dmg = monster.take_damage(dmg)
                    combat_log.append(f"A blast of roaring fire engulfed {monster.name} for {c_red(str(actual_dmg))} magical damage!")
                elif sk_type == "mage_heal":
                    healed = hero.heal(40)
                    combat_log.append(f"Arcane light bathed you, restoring {c_green(str(healed) + ' HP')}!")
                elif sk_type == "rogue_strike":
                    dmg = int(hero.total_attack * 2.2) + random.randint(4, 9)
                    actual_dmg = monster.take_damage(dmg)
                    combat_log.append(f"Stepping from the shadows, you dealt a lethal {c_yellow(str(actual_dmg) + ' Critical Damage')} to {monster.name}!")
                elif sk_type == "rogue_smoke":
                    dmg = hero.total_attack // 2
                    monster.take_damage(dmg)
                    smoke_active = True
                    combat_log.append(f"You shattered a smoke bomb! {monster.name} took {dmg} damage and is completely disoriented!")

                hero_acted = True
            else:
                continue

        elif cmd in ("h", "heal", "potion", "3"):
            if hero.health_potions <= 0:
                print(c_red("You have no Health Potions left!"))
                if not test_mode:
                    time.sleep(1)
                continue
            hero.health_potions -= 1
            recovered = hero.heal(45)
            combat_log.append(f"You drank a Health Potion and restored {c_green(str(recovered) + ' HP')}!")
            hero_acted = True

        elif cmd in ("m", "mana", "4"):
            if hero.mana_potions <= 0:
                print(c_red("You have no Mana Potions left!"))
                if not test_mode:
                    time.sleep(1)
                continue
            hero.mana_potions -= 1
            restored = hero.restore_mp(35)
            combat_log.append(f"You drank a Mana Potion and recovered {c_cyan(str(restored) + ' MP')}!")
            hero_acted = True

        elif cmd in ("d", "defend", "5"):
            defending = True
            hero.restore_mp(6)
            combat_log.append("You assumed a sturdy defensive stance (+50% Defense, +6 MP).")
            hero_acted = True

        elif cmd in ("f", "flee", "run", "6"):
            if monster.is_boss:
                print(c_red("You cannot flee from the Final Boss! Fight to the death!"))
                if not test_mode:
                    time.sleep(1)
                continue
            if random.random() < 0.70:
                print(c_green("\nYou successfully slipped away from combat!"))
                if not test_mode:
                    pause()
                return "fled"
            else:
                combat_log.append(f"Failed to flee! {monster.name} blocked your escape!")
                hero_acted = True
        else:
            print(c_red("Invalid combat command!"))
            if not test_mode:
                time.sleep(0.8)
            continue

        if not hero_acted:
            continue

        # Check if monster was defeated
        if not monster.is_alive():
            break

        # Monster's Turn
        if monster.stunned:
            combat_log.append(f"{monster.name} is stunned and could not act!")
            monster.stunned = False
        elif smoke_active:
            combat_log.append(f"{monster.name} swung wildly in the smoke and missed!")
            smoke_active = False
        else:
            # Check player dodge
            if random.random() < hero.dodge_rate:
                combat_log.append(f"You swiftly {c_cyan('DODGED')} {monster.name}'s attack!")
            else:
                # Monster attack logic
                mon_dmg = monster.attack + random.randint(-2, 3)
                # Check for special monster move
                if monster.special_move and random.random() < 0.35:
                    mon_dmg = int(mon_dmg * 1.4)
                    spec_name = monster.special_move
                    move_text = f"{monster.name} unleashed {c_red(spec_name)}!"
                else:
                    move_text = f"{monster.name} attacked you!"

                if defending:
                    mon_dmg = int(mon_dmg * 0.5)

                actual_mon_dmg = hero.take_damage(mon_dmg)
                combat_log.append(f"{move_text} You took {c_red(str(actual_mon_dmg))} damage!")

        # Turn maintenance
        if hero.hero_class == "Mage":
            hero.restore_mp(3)  # Passive mana trickle
        hero.turns_played += 1
        turn += 1

    # End of Combat resolution
    if not test_mode:
        clear_screen()
    if hero.is_alive():
        print(c_green("=" * 60))
        print(c_bold(c_green(f"  VICTORY! {monster.name} has been defeated!  ".center(60))))
        print(c_green("=" * 60))
        hero.monsters_slain += 1
        hero.gold += monster.gold_reward

        print(f"\n Spoils of Battle:")
        print(f"  * Earned: {c_yellow(str(monster.gold_reward) + ' Gold')}")
        print(f"  * Experience: {c_cyan('+' + str(monster.xp_reward) + ' XP')}")

        # Chance for potion drop
        if random.random() < 0.35:
            pot_type = "Health" if random.random() < 0.6 else "Mana"
            if pot_type == "Health":
                hero.health_potions += 1
            else:
                hero.mana_potions += 1
            print(f"  * Looted: {c_magenta('1x ' + pot_type + ' Potion')}")

        leveled = hero.gain_xp(monster.xp_reward)
        if leveled:
            print("\n" + c_yellow("*" * 60))
            print(c_bold(c_yellow(f"  * LEVEL UP! You reached Level {hero.level}! *  ".center(60))))
            print(c_yellow("  All HP & MP fully restored! Max stats increased!"))
            print(c_yellow("*" * 60))

        if monster.is_boss:
            hero.boss_slain = True

        if not test_mode:
            pause()
        return "won"
    else:
        print(c_red("=" * 60))
        print(c_bold(c_red(f"  DEFEAT... You fell in battle against {monster.name}.  ".center(60))))
        print(c_red("=" * 60))
        if not test_mode:
            pause()
        return "lost"


# ============================================================================
# INTERACTIONS: SHOP, SHRINE, TREASURE
# ============================================================================

def visit_shop(hero):
    """Interactive merchant shop with upgrades and consumables."""
    while True:
        clear_screen()
        print(c_yellow("=" * 60))
        print(c_bold("  GRISWOLD'S TRAVELING DUNGEON EMPORIUM ($)"))
        print(c_yellow("=" * 60))
        print(" 'Welcome, adventurer! Spend your gold wisely... it might")
        print("  be the only thing between you and an early grave!'")
        print("-" * 60)
        print(f" Your Gold: {c_yellow(str(hero.gold))} G   |   HP: {hero.hp}/{hero.max_hp}   |   MP: {hero.mp}/{hero.max_mp}")
        print("-" * 60)
        print(f" [1] Health Potion (+45 HP)             -  {c_yellow('20 G')} (Owned: {hero.health_potions})")
        print(f" [2] Mana Potion (+35 MP)               -  {c_yellow('15 G')} (Owned: {hero.mana_potions})")
        print(f" [3] Sharpening Stone (+2 Base Attack)  -  {c_yellow('45 G')}")
        print(f" [4] Steel Plate Inlay (+2 Defense)     -  {c_yellow('40 G')}")
        print(f" [5] Elixir of Life (+20 Max HP & Full) -  {c_yellow('65 G')}")
        print(" [0] Exit Shop")
        print("-" * 60)

        choice = input("Enter selection (0-5): ").strip()
        if choice == "1":
            if hero.gold >= 20:
                hero.gold -= 20
                hero.health_potions += 1
                print(c_green("Bought 1 Health Potion!"))
            else:
                print(c_red("Not enough gold!"))
            time.sleep(0.8)
        elif choice == "2":
            if hero.gold >= 15:
                hero.gold -= 15
                hero.mana_potions += 1
                print(c_green("Bought 1 Mana Potion!"))
            else:
                print(c_red("Not enough gold!"))
            time.sleep(0.8)
        elif choice == "3":
            if hero.gold >= 45:
                hero.gold -= 45
                hero.base_attack += 2
                print(c_green("Your blade gleams with newfound sharpness! (+2 Attack)"))
            else:
                print(c_red("Not enough gold!"))
            time.sleep(0.8)
        elif choice == "4":
            if hero.gold >= 40:
                hero.gold -= 40
                hero.defense += 2
                print(c_green("Your armor is reinforced! (+2 Defense)"))
            else:
                print(c_red("Not enough gold!"))
            time.sleep(0.8)
        elif choice == "5":
            if hero.gold >= 65:
                hero.gold -= 65
                hero.max_hp += 20
                hero.hp = hero.max_hp
                print(c_green("The elixir surges through your veins! (+20 Max HP)"))
            else:
                print(c_red("Not enough gold!"))
            time.sleep(0.8)
        elif choice in ("0", "exit", "q"):
            print("Griswold waves: 'Stay alive down there!'")
            time.sleep(0.6)
            break


def visit_shrine(hero, room):
    """Ancient Shrine with risk/reward decisions."""
    clear_screen()
    print(c_blue("=" * 60))
    print(c_bold("  * THE ANCIENT RUNIC SHRINE *"))
    print(c_blue("=" * 60))

    if room.cleared:
        print("\nThe shrine is silent. Its ancient magic has already been invoked.")
        pause()
        return

    print("\nA mysterious crystalline altar hums with forgotten primordial energy.")
    print("Runes carved into the stone offer boons to those who dare commune.")
    print("-" * 60)
    print(" [1] Kneel and Pray (Chance for full healing and mana restoration)")
    print(" [2] Offer 25 Gold (Receive a sacred blessing of strength)")
    print(" [3] Touch the Dark Core (High risk: Powerful artifact or curse)")
    print(" [0] Step away respectfully")
    print("-" * 60)

    choice = input("Your choice: ").strip()
    if choice == "1":
        if random.random() < 0.75:
            hero.hp = hero.max_hp
            hero.mp = hero.max_mp
            print(c_green("\nA warm soothing light washes over you. HP and MP fully restored!"))
        else:
            dmg = random.randint(8, 15)
            hero.take_damage(dmg)
            print(c_red(f"\nThe ancient spirits were disturbed! You took {dmg} psychic backlash!"))
        room.cleared = True
    elif choice == "2":
        if hero.gold >= 25:
            hero.gold -= 25
            hero.base_attack += 2
            hero.crit_rate += 0.05
            print(c_yellow("\nThe gods accept your tribute! Your strikes gain holy fury (+2 Attack, +5% Crit)!"))
            room.cleared = True
        else:
            print(c_red("\nYou lack the gold to make an offering."))
    elif choice == "3":
        roll = random.random()
        if roll < 0.50:
            hero.weapon_bonus += 5
            hero.weapon_name = "Abyssal " + hero.weapon_name
            print(c_magenta(f"\nThe dark core infuses your weapon! Gained {hero.weapon_name} (+5 Bonus Attack)!"))
        else:
            curse_dmg = random.randint(15, 25)
            hero.take_damage(curse_dmg)
            print(c_red(f"\nThe core erupts with void energy! You suffer {curse_dmg} damage!"))
        room.cleared = True
    else:
        print("\nYou leave the shrine undisturbed.")

    pause()


def open_chest(hero, room, test_mode=False):
    """Handle discovering a treasure chest."""
    clear_screen(test_mode=test_mode)
    print(c_yellow("=" * 60))
    print(c_bold("  [★] TREASURE CHEST DISCOVERED! [★]"))
    print(c_yellow("=" * 60))

    gold = room.treasure_gold
    hero.gold += gold
    hero.chests_opened += 1
    print(f"\nYou carefully unlatch the heavy iron chest...")
    print(f"Inside, you find {c_yellow(str(gold) + ' gleaming Gold Coins')}!")

    if room.treasure_item == "potion":
        pot = "Health" if random.random() < 0.65 else "Mana"
        if pot == "Health":
            hero.health_potions += 1
        else:
            hero.mana_potions += 1
        print(f"Also tucked in velvet: {c_cyan('1x ' + pot + ' Potion')}!")

    room.cleared = True
    pause(test_mode=test_mode)


# ============================================================================
# MAIN GAME LOOP & NAVIGATION
# ============================================================================

def character_creation():
    """Prompt player for character name and class."""
    clear_screen()
    print(c_magenta("=" * 62))
    print(c_bold(c_yellow("    [⚔]  DUNGEON CRAWLER RPG: THE CRYPT OF MALAKOR  [⚔]    ".center(62))))
    print(c_magenta("=" * 62))
    print(" Deep beneath the kingdom lies the Crypt of Malakor, a forgotten")
    print(" dungeon crawling with dark monstrosities. Three floors await.")
    print(" Slay the creatures, equip relics, and defeat the Void Dragon!")
    print("-" * 62)

    while True:
        name = input("Enter your hero's name: ").strip()
        if name:
            break
        print("Please enter a valid name.")

    print("\nChoose your Hero Class:")
    print(f" [1] {c_bold('Warrior')} : High HP & Armor. Shield Bash and Whirlwind attacks.")
    print(f" [2] {c_bold('Mage')}    : High Mana & Spells. Devastating Fireball and Arcane Healing.")
    print(f" [3] {c_bold('Rogue')}   : High Criticals & Evasion. Shadow Strike and Smoke Bombs.")

    while True:
        cls_choice = input("\nSelect class (1-3): ").strip()
        if cls_choice == "1" or cls_choice.lower() == "warrior":
            return Hero(name, "Warrior")
        elif cls_choice == "2" or cls_choice.lower() == "mage":
            return Hero(name, "Mage")
        elif cls_choice == "3" or cls_choice.lower() == "rogue":
            return Hero(name, "Rogue")
        print("Invalid choice. Please enter 1, 2, or 3.")


def play_dungeon_game():
    """Run a full game session."""
    setup_terminal()
    hero = character_creation()
    current_floor_idx = 1
    max_floors = 3

    floor = DungeonFloor(current_floor_idx)
    player_r, player_c = floor.start_pos

    while hero.is_alive() and not hero.boss_slain:
        clear_screen()

        # Render Header & Map
        floor.render_map(player_r, player_c)
        print("-" * 60)

        # Quick Hero Status Line
        hp_bar = make_bar(hero.hp, hero.max_hp, length=10, fill_color=c_green)
        mp_bar = make_bar(hero.mp, hero.max_mp, length=6, fill_color=c_cyan)
        print(f" {c_bold(hero.name)} (Lvl {hero.level} {hero.hero_class}) | Gold: {c_yellow(str(hero.gold))} G | HP: {hp_bar} | MP: {mp_bar}")
        print(f" Potions: {c_green(str(hero.health_potions))} Health [H], {c_cyan(str(hero.mana_potions))} Mana [M] | Weapon: {hero.weapon_name} (+{hero.weapon_bonus})")
        print("-" * 60)

        # Movement & Commands Prompt
        print(" Move: [W] North  [S] South  [A] West  [D] East")
        print(" Actions: [I] Character Sheet  [H] Use HP Pot  [M] Use MP Pot  [Q] Quit")
        cmd = input(c_bold("\nAction: ")).strip().lower()

        # Handle Commands
        if cmd in ("q", "quit"):
            confirm = input("Are you sure you want to abandon the dungeon? (y/n): ").strip().lower()
            if confirm in ("y", "yes"):
                print("You retreated from the darkness. Better luck next time!")
                break
            continue

        if cmd in ("i", "inv", "sheet", "c"):
            hero.show_sheet()
            continue

        if cmd in ("h", "heal"):
            if hero.health_potions > 0:
                hero.health_potions -= 1
                healed = hero.heal(45)
                print(c_green(f"Used Health Potion! Restored {healed} HP."))
            else:
                print(c_red("No Health Potions remaining!"))
            time.sleep(0.8)
            continue

        if cmd in ("m", "mana"):
            if hero.mana_potions > 0:
                hero.mana_potions -= 1
                restored = hero.restore_mp(35)
                print(c_cyan(f"Used Mana Potion! Restored {restored} MP."))
            else:
                print(c_red("No Mana Potions remaining!"))
            time.sleep(0.8)
            continue

        # Directions
        move_map = {
            "w": (-1, 0), "n": (-1, 0), "up": (-1, 0),
            "s": (1, 0), "down": (1, 0),
            "a": (0, -1), "west": (0, -1), "left": (0, -1),
            "d": (0, 1), "east": (0, 1), "right": (0, 1),
        }

        if cmd not in move_map:
            print(c_red("Invalid command! Use W/A/S/D to move or H/M/I for actions."))
            time.sleep(0.8)
            continue

        dr, dc = move_map[cmd]
        new_r, new_c = player_r + dr, player_c + dc

        if not (0 <= new_r < floor.size and 0 <= new_c < floor.size):
            print(c_red("A solid dungeon wall blocks your passage!"))
            time.sleep(0.8)
            continue

        # Valid Move
        player_r, player_c = new_r, new_c
        room = floor.grid[player_r][player_c]
        room.visited = True
        hero.turns_played += 1

        # Check Room Type
        if room.room_type == "monster" and not room.cleared:
            res = execute_combat(hero, room.monster)
            if res == "won":
                room.cleared = True
            elif res == "fled":
                # Step back to previous room
                player_r, player_c = player_r - dr, player_c - dc
            elif res == "lost":
                break

        elif room.room_type == "boss" and not room.cleared:
            res = execute_combat(hero, room.monster)
            if res == "won":
                room.cleared = True
                break
            else:
                break

        elif room.room_type == "treasure" and not room.cleared:
            open_chest(hero, room)

        elif room.room_type == "shop":
            visit_shop(hero)

        elif room.room_type == "shrine" and not room.cleared:
            visit_shrine(hero, room)

        elif room.room_type == "stairs":
            clear_screen()
            print(c_magenta("=" * 60))
            print(c_bold("  [>] DESCENDING TO THE NEXT FLOOR [>]"))
            print(c_magenta("=" * 60))
            print("\nYou found the stone staircase leading into deeper darkness.")
            descend = input("Descend deeper into the dungeon? (y/n): ").strip().lower()
            if descend in ("y", "yes", ""):
                current_floor_idx += 1
                if current_floor_idx <= max_floors:
                    print(c_yellow(f"\nSteeling your courage, you descend to Floor {current_floor_idx}..."))
                    pause()
                    floor = DungeonFloor(current_floor_idx)
                    player_r, player_c = floor.start_pos
                else:
                    break

    # Game Over Summary
    render_game_over(hero)


def render_game_over(hero):
    """Display final victory or defeat screen with statistics."""
    clear_screen()
    if hero.boss_slain:
        print(c_yellow("=" * 64))
        print(c_bold(c_yellow("""
        [★] [★] [★]   VICTORY HAS BEEN WON!   [★] [★] [★]
       ______                               _             
      |  ___ \                             | |            
      | | _/ /_ __ __ ___   _____ _ __     | |            
      |  __/| '__/ _` \ \ / / _ \ '__|    | |            
      | |   | | | (_| |\ V /  __/ |       |_|            
      |_|   |_|  \__,_| \_/ \___|_|       (_)            
""")))
        print(c_yellow("=" * 64))
        print(c_green(f"\n Congratulations {c_bold(hero.name)}! You vanquished Malakor the Void Dragon"))
        print(c_green(" and banished the darkness from the ancient kingdom!\n"))
        title = "LEGENDARY DUNGEON CONQUEROR"
    else:
        print(c_red("=" * 64))
        print(c_bold(c_red("""
              [+] [+] [+]   YOUR ADVENTURE ENDS HERE   [+] [+] [+]
               _______                  ____                 
              / ____(_)___ _____ _____ / __ \_   _____  _____
             / /_  / / __ `/ __ `/ __ / / / / | / / _ \/ ___/
            / __/ / / /_/ / /_/ / /_// /_/ /| |/ /  __/ /    
           /_/   /_/\__,_/\__,_/\__, /\____/ |___/\___/_/     
                               /____/                         
""")))
        print(c_red("=" * 64))
        print(c_red(f"\n Alas, {hero.name} the {hero.hero_class} perished within the dark depths."))
        print(c_red(" Your bones join those of countless explorers before you...\n"))
        title = "VALIANT FALLEN HERO"

    print("-" * 64)
    print(c_bold(f" FINAL TITLE: {c_yellow(title)}"))
    print("-" * 64)
    print(f" Hero Class      : {hero.hero_class}")
    print(f" Final Level     : {hero.level}")
    print(f" Monsters Slain  : {hero.monsters_slain}")
    print(f" Gold Collected  : {hero.gold} G")
    print(f" Chests Looted   : {hero.chests_opened}")
    print(f" Turns Survived  : {hero.turns_played}")
    print("-" * 64)
    pause("Press Enter to return to the main menu...")


# ============================================================================
# MAIN MENU ENTRY POINT & SELF-TEST
# ============================================================================

def show_instructions():
    """Print game rules and mechanics."""
    clear_screen()
    print(c_cyan("=" * 60))
    print(c_bold("  HOW TO PLAY: DUNGEON CRAWLER RPG"))
    print(c_cyan("=" * 60))
    print("""
 OBJECTIVE:
   Explore 3 procedurally generated dungeon floors. Slay monsters,
   open treasure chests, visit the wandering merchant, unlock
   ancient shrines, and defeat the Void Dragon on Floor 3!

 CONTROLS:
   Movement : [W] North, [S] South, [A] West, [D] East
   Actions  : [I] View Character Sheet & Stats
              [H] Quick Drink Health Potion
              [M] Quick Drink Mana Potion
              [Q] Abandon Game / Quit

 MAP SYMBOLS:
   [P]  Player current location
   [M]  Hostile monster encounter
   [T]  Hidden treasure chest
   [$]  Griswold's traveling merchant shop
   [*]  Ancient mysterious shrine
   [>]  Stairway to the next floor
   [?]  Unexplored fog of war
   [.]  Cleared and safe room

 COMBAT TACTICS:
   - Use Attack for reliable damage with a chance to critical hit.
   - Utilize class skills (Shield Bash, Fireball, Shadow Strike).
   - Defend to reduce incoming damage by 50% and recharge mana.
   - Save Health and Mana potions for deadly encounters!
""")
    pause()


def run_self_tests():
    """Run an automated self-test of all game components."""
    print("Running Dungeon Crawler automated self-tests...")

    # 1. Test Hero creation for all 3 classes
    for cls in ("Warrior", "Mage", "Rogue"):
        h = Hero("Tester", cls)
        assert h.is_alive()
        assert h.hp == h.max_hp
        assert h.total_attack > 0
        assert h.total_defense > 0
        assert len(h.skills) >= 2
    print(" [PASS] 1. Hero classes initialized properly.")

    # 2. Test Monster creation across all floors
    for floor in (1, 2, 3):
        m = create_monster(floor)
        assert m.is_alive()
        assert m.attack > 0
        assert m.xp_reward > 0
    boss = create_boss()
    assert boss.is_boss is True
    assert boss.hp > 200
    print(" [PASS] 2. Monster and Boss generation valid.")

    # 3. Test Dungeon Floors generation
    for floor_num in (1, 2, 3):
        df = DungeonFloor(floor_num, size=4)
        assert len(df.grid) == 4
        assert len(df.grid[0]) == 4
        types = [df.grid[r][c].room_type for r in range(4) for c in range(4)]
        assert "shop" in types
        assert "shrine" in types
        if floor_num == 3:
            assert "boss" in types
        else:
            assert "stairs" in types
    print(" [PASS] 3. Procedural dungeon layout generated correctly.")

    # 4. Test Map Rendering without errors
    df = DungeonFloor(1, size=4)
    df.render_map(0, 0)
    print(" [PASS] 4. Mini-map rendered without exceptions.")

    # 5. Test XP, leveling, damage mitigation, and healing
    h = Hero("Arthur", "Warrior")
    assert h.level == 1
    took = h.take_damage(20)
    assert took > 0
    assert h.hp < h.max_hp
    healed = h.heal(50)
    assert healed > 0
    assert h.hp <= h.max_hp
    leveled = h.gain_xp(60)
    assert leveled is True
    assert h.level == 2
    print(" [PASS] 5. Combat mechanics, stats, and leveling validated.")

    # 6. Test Combat Simulation
    h = Hero("Galahad", "Warrior")
    h.weapon_bonus = 50  # Overpowered for fast test
    m = Monster("Dummy", 20, 5, 0, 50, 20)
    res = execute_combat(h, m, test_mode=True)
    assert res == "won"
    assert h.monsters_slain == 1
    print(" [PASS] 6. Combat engine completed successfully.")

    # 7. Test Shrine and Treasure logic
    h = Hero("Robin", "Rogue")
    r = Room(0, 0, "treasure")
    r.treasure_gold = 50
    open_chest(h, r, test_mode=True)
    assert h.gold == 80
    assert r.cleared is True
    print(" [PASS] 7. Treasure chest logic verified.")

    # 8. Test Glyph resolution
    g = get_glyphs()
    assert "player" in g
    assert "fill" in g
    print(" [PASS] 8. Terminal glyphs resolved properly.")

    print("\n" + c_green("ALL 8 SELF-TESTS PASSED SUCCESSFULLY!"))


def main():
    """Primary application loop."""
    setup_terminal()

    if "--test" in sys.argv:
        run_self_tests()
        return

    while True:
        clear_screen()
        print(c_magenta("=" * 54))
        print(c_bold(c_yellow("   [⚔]  DUNGEON CRAWLER: THE CRYPT OF MALAKOR  [⚔]   ".center(54))))
        print(c_magenta("=" * 54))
        print("  1. Start New Adventure")
        print("  2. How to Play & Game Guide")
        print("  3. Exit Game")
        print("-" * 54)

        choice = input("Enter choice (1-3): ").strip()
        if choice == "1":
            play_dungeon_game()
        elif choice == "2":
            show_instructions()
        elif choice == "3":
            print("\nMay glory follow you wherever you travel. Farewell!\n")
            break
        else:
            print(c_red("Invalid selection. Please choose 1, 2, or 3."))
            time.sleep(0.8)


if __name__ == "__main__":
    main()
