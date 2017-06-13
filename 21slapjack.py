import random
import time
import timeout


class NeutralState:
    NORMAL = 0
    DANGER = 1
    BUST = 2
    FATAL = 3

class NeutralDecision:
    PASS = 0
    TWO_D_SIX = 1
    FOUR_D_SIX = 2

class DefenseDecision:
    NOTHING = 0
    BLOCK = 1
    BURST = 2

class Game:
    name = "21 Smackjack"

    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.turn = 1
        self._p_cur = None # Current player
        self._p_opp = None # Opposite player

    def start(self):
        self.p_cur = self.find_first_to_play()

        while True:
            self.log("-- Rebel {} --".format(self.turn))
            self.print_hp()

            state1 = self.neutral_phase(self.p_cur)
            danger = NeutralState.DANGER in state1
            if NeutralState.BUST in state1:
                self.attack_phase(self.p_opp, self.p_cur, False)
            else:
                state2 = self.neutral_phase(self.p_opp, last_roll = state1[1])
                fatal = NeutralState.FATAL in state1 + state2
                if NeutralState.BUST in state2 or state1[1] > state2[1]:
                    # First player has better roll
                    self.log("{} has the better roll.".format(self.p_cur.name))
                    self.attack_phase(self.p_cur, self.p_opp, fatal)
                elif state1[1] < state2[1]:
                    # Opposing player has better roll
                    self.log("{} has the better roll.".format(self.p_opp.name))
                    self.attack_phase(self.p_opp, self.p_cur, fatal or danger)
                else:
                    # Same roll
                    self.log("Both players have the same roll.")
                    fatal = True
                    roll_cur, roll_opp = None, None
                    while roll_cur is None or roll_cur == roll_opp:
                        self.log("3, 2, 1... Danger!")
                        roll_cur = Dice.rollstr("2d6")
                        self.log("{} rolled a {:d}!"
                            .format(self.p_cur.name, roll_cur))
                        roll_opp = Dice.rollstr("2d6")
                        self.log("{} rolled a {:d}!"
                            .format(self.p_opp.name, roll_opp))
                    if roll_cur > roll_opp:
                        self.attack_phase(self.p_cur, self.p_opp, fatal)
                    else:
                        self.attack_phase(self.p_opp, self.p_cur, fatal)

            winner = self.get_winner()
            if winner is not None:
                self.log("{} won with {:d} hp in {:d} turns!"
                    .format(winner.name, winner.hp, self.turn))
                return winner

            self.turn += 1
            self.p_cur = self.p_opp # Swap players

    def neutral_phase(self, player, last_roll = None):
        self.log("- Neutral phase: {} rolls.".format(player.name))
        roll = Dice.rollstr("4d6")
        self.log("{} rolled {:d}.".format(player.name, roll))
        roll_chk = self.check_21(player, roll)
        if roll_chk:
            return roll_chk
        else:
            if last_roll and roll > last_roll:
                # No decision needed, your roll's already better than
                # that of the first player, so hold.
                return (NeutralState.DANGER, roll)

            if isinstance(player, CPUPlayer): player.assist(roll, last_roll)
            decision = player.neutral_decide()
            if decision == NeutralDecision.PASS:
                # Pass
                self.log("{} decided to pass. (Danger!)".format(player.name))
                return (NeutralState.DANGER, roll)
            elif decision == NeutralDecision.TWO_D_SIX:
                # Do the third roll
                self.log("{} decided to roll once more.".format(player.name))
                roll2 = Dice.rollstr("2d6")
                roll += roll2
                self.log("{} rolled {:d} => {:d}".format(player.name, roll2, roll))
                roll_chk = self.check_21(player, roll)
                if roll_chk: return roll_chk
            elif decision == NeutralDecision.FOUR_D_SIX:
                # Do a 4d6
                self.log("{} decided to double or nothing!".format(player.name))
                roll2 = Dice.rollstr("4d6")
                roll += roll2
                self.log("{} rolled {:d} => {:d}".format(player.name, roll2, roll))
                roll_chk = self.check_21(player, roll)
                if roll_chk: return roll_chk
            else:
                raise ValueError("Invalid decision")
        return (NeutralState.NORMAL, roll)

    def check_21(self, player, roll):
        if roll > 21:
            self.log("{} busted!".format(player.name))
            return (NeutralState.BUST,)
        elif roll == 21:
            self.log("A fatal hit!")
            return (NeutralState.FATAL, roll)

    def attack_phase(self, player, opponent, fatal):
        self.log("- Attack phase: {} attacks!".format(player.name))
        faces = 6
        while faces > 1:
            damage = Dice.roll(1, faces)
            if fatal:
                self.log("(Fatal: +6 damage)")
                damage += 6
                fatal = False
            self.log("{} rolled 1d{:d}: {:d} damage dealt!".format(player.name, faces, damage))
            opponent.hp -= damage
            if damage % 2 == 0:
                self.log("Combo!")
                decision = opponent.defense_decide()
                if decision == DefenseDecision.BLOCK:
                    self.log("{} decided to block the damage."
                        .format(opponent.name))
                    block = Dice.roll(1, faces)
                    self.log("{} rolled {:d}.".format(opponent.name, block))
                    if block == damage:
                        self.log("{} successfully blocked the damage!"
                            .format(opponent.name))
                        self.dead_angle_attack(player, damage)
                        break
                    else:
                        self.log("{} couldn't break out of it!"
                            .format(opponent.name))
                elif opponent.burst and decision == DefenseDecision.BURST:
                    self.log("{} burst!".format(opponent.name))
                    opponent.burst = False
                    break
                faces -= 1
            else:
                break

    def dead_angle_attack(self, target, damage):
        self.log("{} was hit by a dead-angle attack!".format(target.name))
        old_hp = target.hp
        target.hp = max(target.hp - damage, 1)
        self.log("{:d} damage taken!".format(old_hp - target.hp))

    def find_first_to_play(self):
        self.log("Determining who is first to play...")
        while True:
            roll_p1 = Dice.rollstr("2d6")
            roll_p2 = Dice.rollstr("2d6")
            self.log("{} rolled {:d}".format(self.p1.name, roll_p1))
            self.log("{} rolled {:d}".format(self.p2.name, roll_p2))

            if roll_p1 > roll_p2:
                self.log("{} will play first.".format(self.p1.name))
                return self.p1
            elif roll_p1 < roll_p2:
                self.log("{} will play first.".format(self.p2.name))
                return self.p2
            else:
                pass # Keep rolling

    @property
    def p_cur(self):
        """Return the current player."""
        return self._p_cur

    @property
    def p_opp(self):
        """Return the opposing player."""
        return self._p_opp

    @p_cur.setter
    def p_cur(self, player):
        """Set the current player and the opposing player."""
        if not isinstance(player, Player):
            raise TypeError("Expected type Player, but got {} instead!".format(type(player)))
        self._p_cur = player
        self._p_opp = self.p2 if self._p_cur == self.p1 else self.p1

    def print_hp(self):
        hp_align = max(len(self.p1.name), len(self.p2.name))
        self.log("{name:<{width}}: {hp:2d} hp"
            .format(name = self.p1.name, width = hp_align, hp = self.p1.hp)
        )
        self.log("{name:<{width}}: {hp:2d} hp"
            .format(name = self.p2.name, width = hp_align, hp = self.p2.hp)
        )

    def get_winner(self):
        if self.p1.hp <= 0:
            return self.p2
        elif self.p2.hp <= 0:
            return self.p1
        else:
            return None

    def log(self, msg):
        #time.sleep(1)
        print(msg)

class Dice:

    def rollstr(fmt):
        """Convenience function.
        Example: '2d4', 'd20', ...
        """
        try:
            num_dice = int(fmt[:fmt.index('d')])
            num_faces = int(fmt[fmt.index('d')+1:])
            return Dice.roll(num_dice, num_faces)
        except ValueError as e:
            raise ValueError("Invalid roll format.") from e

    def roll(num_dice, num_faces):
        return sum([random.randint(1, num_faces) for x in range(num_dice)])

class Player:

    def __init__(self, name = "Player"):
        self.hp = 25
        self.name = name
        self.burst = True

    def neutral_decide(self):
        pass

    def defense_decide(self):
        pass

class HumanPlayer(Player):

    def __init__(self, name):
        super().__init__(name)

    def neutral_decide(self):
        choice = None
        while True:
            try:
                choice = int(input("Pass (1), roll once (2), or double or nothing (3)? "))
                if   choice == 1: return NeutralDecision.PASS
                elif choice == 2: return NeutralDecision.TWO_D_SIX
                elif choice == 3: return NeutralDecision.FOUR_D_SIX
                else:             print("Invalid choice.")
            except ValueError:
                print("Invalid choice.")

    def defense_decide(self):
        choice = None
        while True:
            try:
                choice = int(timeout.input_with_timeout(
                    "Press 1 to block" \
                    + (" and 2 to burst" if self.burst else "") \
                    + "... ", 3
                ))
                if choice == 1:
                    return DefenseDecision.BLOCK
                elif choice == 2 and self.burst:
                    return DefenseDecision.BURST
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Invalid choice.")
            except timeout.TimeoutExpired:
                return DefenseDecision.NOTHING

class CPUPlayer(Player):

    def __init__(self, name):
        super().__init__(name)
        self.ctx = {
            'cur_roll': 0,
            'opp_roll': 0
        }
        self.threshold_neutral_4d6 = 8
        self.threshold_neutral_2d6 = 14
        self.threshold_hp_burst    = 6

    def assist(self, cur_roll, opp_roll):
        """Give the CPU a context to make decisions out of."""
        self.ctx['cur_roll'] = cur_roll
        self.ctx['opp_roll'] = opp_roll

    def neutral_decide(self):
        cur_roll, opp_roll = self.ctx['cur_roll'], self.ctx['opp_roll']
        if opp_roll is not None: # CPU is rolling second.
            # Prioritize beating other opponent.
            if cur_roll > opp_roll:
                return NeutralDecision.PASS
            elif cur_roll < self.threshold_neutral_4d6:
                return NeutralDecision.FOUR_D_SIX
            elif cur_roll == opp_roll:
                return NeutralDecision.PASS
            else:
                return NeutralDecision.TWO_D_SIX
        else:
            if cur_roll < self.threshold_neutral_4d6:
                return NeutralDecision.FOUR_D_SIX
            elif cur_roll < self.threshold_neutral_2d6:
                return NeutralDecision.TWO_D_SIX
            else:
                return NeutralDecision.PASS

    def defense_decide(self):
        if self.hp < self.threshold_hp_burst and self.burst:
            return DefenseDecision.BURST
        else:
            return DefenseDecision.BLOCK

def start_cli():
    print("{} Simulator".format(Game.name))

    choice = None
    choices = {
        1: ("CPU vs. CPU",
            lambda: Game(CPUPlayer("CPU1"), CPUPlayer("CPU2"))),
        2: ("Player vs. CPU",
            lambda: Game(HumanPlayer(ask_name(1)), CPUPlayer("CPU"))),
        3: ("Player vs. Player",
            lambda: Game(HumanPlayer(ask_name(1)), HumanPlayer(ask_name(2))))
    }

    for c in choices.keys():
        print("{:2d}. {}".format(c, choices[c][0]))
    while True:
        try:
            choice = int(input("{}? ".format(list(choices.keys()))))
        except ValueError:
            print("The choice was not a number. Try again.")
        except KeyboardInterrupt:
            print("Quitting!")
            return
        if choice not in choices:
            print("Invalid choice. Try again.")
        else:
            break

    print("Selected {}.".format(choice))

    game = choices[choice][1]()
    game.start()

def ask_name(player_number = None):
    if player_number is None:
        prompt = "Player's name: "
    else:
        prompt = "Player {}'s name: ".format(player_number)

    return input(prompt)

if __name__ == "__main__":
    start_cli()