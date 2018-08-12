import sys
import math
import random

# DEFINITIONS:
# locations
locationPlayerHand = 0
locationPlayerSide = 1
locationOpponentSide = -1

def errorSide(text):
    print(text, file=sys.stderr)

# Behaviour: 
#TargetCurve  0,1,2,3,4,5,6,7+
targetCurve = [0,2,8,6,4,2,2,3]
targetRemovalNum = 3



class Side(object):
    def __init__(self, creatures):
        self.creatures = creatures
        self.sumAttack = self.calcSumAttack()
        self.guards = self.listGuards()

    def calcSumAttack(self):
        sum = 0
        for creature in self.creatures:
            if creature.canAttack:
                sum += creature.attack
        return sum

    def refreshSide(self):
        list = []
        for creature in self.creatures:
            if creature.canAttack and creature.defense > 0:
                list.append(creature)
        self.creatures = list
        self.guards = self.listGuards()
        self.sumAttack = self.calcSumAttack()

    def listGuards(self):
        guards = []
        for creature in self.creatures:
            if 'G' in creature.abilities:
                guards.append(creature)
        guards.sort(key=lambda x: x.defenseValue, reverse=True)
        return guards

    def addCreature(self, creature):
        self.creatures.append(creature)
        self.refreshSide()
        self.sumAttack = self.calcSumAttack()

class Card:

    currentCurve = targetCurve
    currentNumberOfRemovals = targetRemovalNum

    def __init__(self, card_number, instance_id, location, card_type, cost, attack, defense, abilities, my_health_change, opponent_health_change, card_draw):
        self.card_number = int(card_number)
        self.instance_id = int(instance_id)
        self.location = int(location)
        self.card_type = int(card_type)
        self.cost = int(cost)
        self.attack = int(attack)
        self.defense = int(defense)
        self.abilities = abilities
        self.my_health_change = int(my_health_change)
        self.opponent_health_change = int(opponent_health_change)
        self.card_draw = int(card_draw)

        self.canAttack = 1
        self.relativeAttack = self.attack
        self.relativeDefense = self.defense
        self.value = 0

        # Value calculation:
        if 'W' in self.abilities:
            self.relativeAttack = self.attack * 2
            self.relativeDefense = self.defense * 2

        # Positive
        self.attackValue = (self.relativeAttack / self.cost) if cost is not "0" else (self.relativeAttack + 1)
        self.defenseValue = (self.relativeDefense / self.cost) if cost is not "0" else (self.relativeDefense + 1)
        self.costEfficiency = (self.attackValue + self.defenseValue) * 2

        # Low hp tax
        self.lowHPTax = self.attack - self.defense if self.cost + 2 > self.defense else 0

        # manacurve
        self.onCurve = 0
        # 0-6
        if self.cost < 7:   
            if self.currentCurve[self.cost] <= 0:  
                self.onCurve = -5
        # 7-12
        else:
            if self.currentCurve[7] <= 0:  
                self.onCurve = -5


        # Types
        if self.card_type is 0:  # Creatures
            if 'C' not in self.abilities:
                self.value += self.costEfficiency - self.lowHPTax
            else:
                self.value += self.costEfficiency + 0.5

            if 'L' in abilities:
                self.value += 2

            if 'G' in abilities:
                self.value += 0.2

            if self.attack == 0:  # 0/x/x
                self.value = - 10

        elif self.card_type is 1:  # Green
            if self.defense + self.attack > 0:
                self.value += self.relativeAttack
            else:
                self.value = -5
        elif self.card_type is 2: # Red
            if self.currentNumberOfRemovals > 0: 
                if self.card_number == 151: # Decimate (Destroy any creature for 5):
                    self.value = 10
                elif self.card_number == 148: # Helm Crusher (Remove everything, 2 damage, for 2):
                    self.value = 10
                else:
                    self.value = 4
            else:
               self.value = 4 + currentNumberOfRemovals

        else:  # self.card_type is 3 # Blue
            self.value -= 5  # TODO items

        self.value += self.card_draw

        self.value += self.onCurve

        

def fight_part(attacker, defender):
    if 'W' in defender.abilities:
        defender.abilities = defender.abilities.replace("W", "")
    elif 'L' in attacker.abilities:
        defender.defense = 0
    else:
        defender.defense -= attacker.attack


def fight_test(attacker, defender):
    if 'W' in defender.abilities:
         return 0
    elif 'L' in attacker.abilities:
        return 1
    elif defender.defense <= attacker.attack:
        return 1
    else:
        return 0


def fight(one, two):
    fight_part(one, two)
    fight_part(two, one)

def tryGoodTrade(target, attackers):
    possibleTrades = []
    for attacker in attackers:
        if not fight_test(target, attacker) and attacker.canAttack and fight_test(attacker, target):
            possibleTrades.append(attacker)
    return possibleTrades

def tryPerfectTrade(target, attackers):
    possibleTrades = []
    for attacker in attackers:
        if not fight_test(target, attacker) and attacker.canAttack and fight_test(attacker, target) and attacker.cost <= target.cost:
            possibleTrades.append(attacker)
    return possibleTrades


def tryAcceptableTrade(target, attackers):
    possibleTrades = []
    for attacker in attackers:
        if attacker.canAttack and fight_test(attacker, target):
            possibleTrades.append(attacker)
    return possibleTrades


def tryAcceptableUpTrade(target, attackers):
    possibleTrades = []
    for attacker in attackers:
        if attacker.canAttack and fight_test(attacker, target) and attacker.cost < target.cost:
            possibleTrades.append(attacker)
    return possibleTrades

def useItemOnCreature(item, creature):
    if item.card_type is 1 or 2:
        creature.attack += item.attack
        creature.defense += item.defense
        playerSide.refreshSide()
    if item.card_type is 1:
        for ability in item.abilities:
            if ability not in creature.abilities:
                creature.abilities += ability
    if item.card_type is 2:
        tempabilities = []
        for ability in creature.abilities:
            if ability not in item.abilities:
                tempabilities += ability
        creature.abilities = tempabilities


# Game loop
turn = 0

while True:

    # Global Data

    playerSide = Side([])
    opponentSide = Side([])

    playerHand = []
    draftSelection = []

    attackOrders = ""
    summonOrders = ""

    player_health, player_mana, player_deck, player_rune = [
        int(j) for j in input().split()]
    opponent_health, opponent_mana, opponent_deck, opponent_rune = [
        int(j) for j in input().split()]

    opponent_hand = int(input())
    card_count = int(input())
    for i in range(card_count):

        card_number, instance_id, location, card_type, cost, attack, defense, abilities, my_health_change, opponent_health_change, card_draw = input().split()
        newCard = Card(card_number, instance_id, location, card_type, cost, attack,
                       defense, abilities, my_health_change, opponent_health_change, card_draw)

        if (newCard.location == locationPlayerHand) and (turn >= 30):
            playerHand.append(newCard)
        elif newCard.location == locationPlayerSide:
            playerSide.addCreature(newCard)
        elif newCard.location == locationOpponentSide:
            opponentSide.addCreature(newCard)
        else:
            draftSelection.append(newCard)

    if turn < 30:  # Draft
        valuesay = ""
        for i in range(len(draftSelection)):

            valuesay += str("%.2f" % draftSelection[i].value) + ":"
            #valuesay += str("%.2f" % draftSelection[i].onCurve ) + " "
            #valuesay += str(draftSelection[0].curveBarriernumbers)

            selected = max(draftSelection, key=lambda c: c.value)
        if draftSelection[0] == selected:
            print("PICK 0 " + valuesay)
        elif draftSelection[1] == selected:
            print("PICK 1 " + valuesay)
        elif draftSelection[2] == selected:
            print("PICK 2 " + valuesay)
        
        # Curve
        if selected.cost < 7:
            selected.currentCurve[selected.cost] -= 1             
        else: 
            selected.currentCurve[7] -= 1
        if selected.card_type == 2:
            selected.currentNumberOfRemovals -= 1
        
    else:  # Battle

        playerHand.sort(key=lambda x: x.relativeAttack, reverse=True)
        opponentSide.creatures.sort(key=lambda x: x.attackValue, reverse=True)

        currentMana = player_mana
        nexAttack = 0

        # Cast
        for i in playerHand:
            if i.cost <= currentMana and i.card_type is 2:
                for creature in opponentSide.creatures:
                    if creature.defense + i.defense <= 0 and i.cost <= creature.cost:
                        if "W" not in creature.abilities or "W" in i.abilities:
                            summonOrders += "USE " + \
                                str(i.instance_id) + " " + \
                                str(creature.instance_id) + " ; "
                            currentMana -= i.cost
                            useItemOnCreature(i, creature)
                            opponentSide.refreshSide()
                            break
        
        for i in playerHand:
            if i.cost <= currentMana and i.card_type is 1:
                for creature in playerSide.creatures:
                    if creature.canAttack:
                        summonOrders += "USE " + \
                            str(i.instance_id) + " " + \
                            str(creature.instance_id) + " ; "
                        currentMana -= i.cost
                        useItemOnCreature(i, creature)
                        playerSide.refreshSide()
                        break

        for i in playerHand:
            if i.cost <= currentMana and i.card_type is 0:
                summonOrders += "SUMMON " + str(i.instance_id) + ";"
                currentMana -= i.cost
                if 'C' not in i.abilities:
                    i.canAttack = 0
                    nexAttack += i.attack
                playerSide.addCreature(i)
                
        for i in playerHand:
            if i.cost <= currentMana and i.card_type is 2 and opponentSide.creatures:
                creature = opponentSide.creatures[0]
                summonOrders += "USE " + \
                    str(i.instance_id) + " " + \
                    str(creature.instance_id) + " ; "
                currentMana -= i.cost
                useItemOnCreature(i, creature)
                opponentSide.refreshSide()

        # Attack
        # Deal with the Defenders. Me no like defenders.
        
        while len(opponentSide.guards) > 0 and playerSide.sumAttack:
            
            for guard in opponentSide.guards:
                if 'W' in guard.abilities:
                    creature = min(playerSide.creatures, key=lambda x: x.attack)
                    fight(creature, guard)
                    creature.canAttack = 0
                    attackOrders += "ATTACK " + \
                        str(creature.instance_id) + " " + \
                        str(guard.instance_id) + " meh, ward; "
                    playerSide.refreshSide()
                    opponentSide.refreshSide()

            
            for guard in opponentSide.guards:
                traders = tryAcceptableUpTrade(guard, playerSide.creatures)
                traders.sort(key=lambda x: x.cost)
                if traders:
                    trader = traders[0]
                    fight(trader, guard)
                    trader.canAttack = 0
                    attackOrders += "ATTACK " + \
                        str(trader.instance_id) + " " + \
                        str(guard.instance_id) + " That's fair, right? ; " 
                    playerSide.refreshSide()
                    opponentSide.refreshSide()

            for guard in opponentSide.guards:
                traders = tryGoodTrade(guard, playerSide.creatures)
                traders.sort(key=lambda x: x.attack)
                if traders:
                    trader = traders[0]
                    fight(trader, guard)
                    trader.canAttack = 0
                    attackOrders += "ATTACK " + \
                        str(trader.instance_id) + " " + \
                        str(guard.instance_id) + " LITTLE GUARD DIES ; "
                    playerSide.refreshSide()
                    opponentSide.refreshSide()

            for guard in opponentSide.guards:
                traders = tryAcceptableTrade(guard, playerSide.creatures)
                traders.sort(key=lambda x: x.attackValue)
                if traders:
                    trader = traders[0]
                    fight(trader, guard)
                    trader.canAttack = 0
                    attackOrders += "ATTACK " + \
                        str(trader.instance_id) + " " + \
                        str(guard.instance_id) + " ACCEPTABLE LOSS ; "
                    playerSide.refreshSide()
                    opponentSide.refreshSide()

            playerSide.creatures.sort(key=lambda x: x.attackValue)
            for creature in playerSide.creatures:
                for guard in opponentSide.guards:
                    if creature.canAttack:
                        attackOrders += "ATTACK " + \
                            str(creature.instance_id) + " " + \
                            str(guard.instance_id) + " ME NO LIKE U ; "
                        fight(creature, guard)
                        creature.canAttack = 0
                        playerSide.refreshSide()
                        opponentSide.refreshSide()

            # EMERGENCY FIX but works, delete if better guard trade. (playerSide.sumAttack)
            playerSide.sumAttack = 0

        playerSide.refreshSide()
        opponentSide.refreshSide()
        
        errorSide(str(playerSide.sumAttack) + "-" + str(opponent_health))
        if playerSide.sumAttack >= opponent_health:  # Lethal. Let's win
            for creature in playerSide.creatures:
                attackOrders += "ATTACK " + \
                    str(creature.instance_id) + " " + "-1 YEEEAAARGH; "
                creature.canAttack = 0
                playerSide.refreshSide()

        playerSide.creatures.sort(key=lambda x: x.attack)
        opponentSide.creatures.sort(key=lambda x: x.attack, reverse=True)
        if playerSide.sumAttack*2 < opponent_health:
            for creature in opponentSide.creatures:
                traders = tryGoodTrade(creature, playerSide.creatures)
                if traders:
                    trader = traders[0]
                    fight(trader, creature)
                    trader.canAttack = 0
                    attackOrders += "ATTACK " + \
                        str(trader.instance_id) + " " + \
                        str(creature.instance_id)  + " " +str(len(traders)) + " ACCEPTABLE; "
                    playerSide.refreshSide()
                    opponentSide.refreshSide()

        if playerSide.sumAttack + nexAttack <= opponentSide.sumAttack:
            for creature in opponentSide.creatures:
                traders = tryAcceptableUpTrade(creature, playerSide.creatures)
                if traders:
                    trader = traders[0]
                    fight(trader, creature)
                    trader.canAttack = 0
                    attackOrders += "ATTACK " + \
                        str(trader.instance_id) + " " + \
                        str(creature.instance_id) + " What was it?; "
                    playerSide.refreshSide()
                    opponentSide.refreshSide()
        
        opponentSide.creatures.sort(key=lambda x: x.attackValue, reverse=True)       
        while opponentSide.sumAttack >= player_health and playerSide.creatures:  # Lethal. Let's not lose
            creature = playerSide.creatures[0]
            target = opponentSide.creatures[0]
            fight(creature, target)
            attackOrders += "ATTACK " + \
                str(creature.instance_id) + " " + str(target.instance_id) + " " + str(opponentSide.sumAttack) + " ; "
            creature.canAttack = 0
            playerSide.refreshSide()
            opponentSide.refreshSide()

        for creature in playerSide.creatures:
            if creature.canAttack:
                # HEDGEHOGHEDGEHOGHEDGEHOG (1/1 lethal)
                if creature.card_number == 48 and opponentSide.creatures:
                    attackOrders += "ATTACK " + str(creature.instance_id) + " " + str(
                        max(opponentSide.creatures, key=lambda c: c.attack).instance_id) + " ZUP BIGGUY; "
                else:
                    attackOrders += "ATTACK " + \
                        str(creature.instance_id) + " " + "-1 FACE; "

        if (attackOrders == "") and (summonOrders == ""):
            print("PASS;")
        else:
            print(summonOrders + attackOrders)

        # Summoning Sickness ends, next round.
        for i in playerSide.creatures:
            i.canAttack = 1
        for i in opponentSide.creatures:  # This line is useless
            i.canAttack = 1

    turn = turn + 1

    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)

# TODO dont let them draw extra cards. (do not hit rune on equal board)
# TODO better LETHAL detecion (if I can win next round, ignore everything?)
