#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division

# Sample python-based agent for AIWolf
# Implement simple heuristics when playing the WEREWOLF role
# For other roles, just play randomly
# Based on https://github.com/k-harada/AIWolfPy
# Developed for aiwolf 0.4.12 (2018/06/16)
# Author: ehauckdo

import time
import aiwolfpy
import aiwolfpy.contentbuilder as cb

import random
import optparse
import numpy as np
import sys
import re

from utility import *
from parsing import *

class SampleAgent(object):

    def __init__(self, agent_name):
        self.myname = agent_name

    def initialize(self, base_info, diff_data, game_setting):
        self.id = base_info["agentIdx"] - 1
        self.base_info = base_info
        self.game_setting = game_setting

        self.game_history = {} # stores each sentence stated from each day
        self.player_map = {}   # a map with the status and other info for each player
        self.target_list = []  # a queue storing possible targets to act against
        self.current_target = None
        
        self.divine_map = {}
        
        '''
        The info table stores the information we have about each player,
        along with it's provenance - the columns are the sources of information (other players)
        and the lines are the players - the sum of each line is a score - positive for villager, negative for werewolf.
        '''
        num_players = game_setting["playerNum"]
        self.num_players = num_players
        
        self.my_role = base_info["myRole"]
        
        self.info_table = np.zeros([num_players,num_players])

        # table of true role for werewoolf :  villager = +100 , wol = -100
        self.true_table_role = np.zeros(num_players)
        for i in range(len(base_info["roleMap"])):
            role_map_idx = str(i+1)
            if role_map_idx in base_info:
                if base_info["roleMap"][role_map_idx] == "WEREWOLF":
                    self.true_table_role[i] = -100
            else:
                self.true_table_role[i] = 100
        
        #number of werewolves
        self.ww_number = game_setting["roleNumMap"]["WEREWOLF"]

        #conflict_list for pairs of players of which one is certainly a werewolf.
        self.conflict_list = []
        self.white_list = []
        self.black_list = []

        #ids of seer, medium, and bodyguard, None if unknown
        self.seer_id = None if base_info["myRole"] != "SEER" else self.id
        self.medium_id = None if base_info["myRole"] != "MEDIUM" else self.id
        self.bg_id = None if base_info["myRole"] != "BODYGUARD" else self.id

        # MEIR - these constants will be multiplied with the 'value' of information
        # if one is suspect of being WEREWOLF, we treat his info less,
        #if one is believed to be SEER or MEDIUM, his word is worth more
        #if one is believed to be BODYGUARD, his word is worth more - since he proved it
        self.seer_value = 2
        self.medium_value = 2
        self.bg_value = 5
        self.suspect_value = 0.2

        #MEIR - this variable will be used to test the claim of bodyguard
        self.no_dead = False

        if self.seer_id:
            self.villager_list = []

        printGameSetting(game_setting)
        self.updatePlayerMap(base_info)

    def getName(self):
        return self.myname

    def update(self, base_info, diff_data, request):
        print("Executing update...")

        #check whether someone died
        living = len([v for v in self.base_info["statusMap"] if v == "ALIVE"])
        new_living = len([v for v in base_info["statusMap"] if v == "ALIVE"])
        
        self.base_info = base_info



        if living == new_living:
            self.no_dead = True
        else:
            self.no_dead = False
        
        printBaseInfo(base_info)
        printDiffData(diff_data)
        
        self.updateGameHistory(diff_data)
        self.updatePlayerMap(base_info)
        self.pickTarget()


    #picks a target based on black list and the table heuristics
    def pickTarget(self):
        print("Executing pickTarget...")
        
        if self.my_role == "WEREWOLF":
            self.setTarget(self.minimal_score(isWerewolf=True))
        else:
            #if i have someone on my black list, choose him as target
            living_wws = [w for w in self.black_list if self.base_info["statusMap"][str(w+1)] == "ALIVE"]
            if len(living_wws) > 0:
                self.setTarget(living_wws[0])
            else:
                self.setTarget(self.minimal_score())
                

    def minimal_score(self, isSeer=False, isWerewolf=False):

        # we use a copy so that if the value of some player changes we still have the information
        table = np.copy(self.info_table)
        
        if isWerewolf:
            wolfscore = np.zeros(self.num_players)
            #calculate the difference between estimation of a player and the reality 
            for i in range(self.num_players):
                if self.true_table_role[i] == -100:
                    continue
                else:
                    for j in range(self.num_players):
                        wolfscore[i] += np.abs(self.true_table_role[j] - table[j][i])
            
            
            return np.argmin(wolfscore) + 1
        
        #all the members in conflict are suspect to be werewolves
        suspects_list = set([y for x in self.conflict_list for y in x])
                            
        #give the columns weights based on the identity of players (seer/medium/suspected as werewolf...)
        for i in range(table.shape[1]):
            if i == self.seer_id:
                table[:,i] = self.seer_value * table[:,i]
            if i == self.medium_id:
                table[:,i] = self.medium_value * table[:,i]
            if i == self.bg_id:
                table[:,i] = self.bg_value * table[:,i]
            if i in self.black_list:
                table[:,i] = -1 * table[:,i]
                continue
            if i in suspects_list:
                table[:,i] = self.suspect_value * table[:,i]

        #pick as target the player with lowest score
        scores = np.sum(table, axis=1)

        #those in white_list are considered as probably villagers
        for i in self.white_list:
            scores[i] += 3

        #if we are seer, we check for the player of which we have the least info
        if isSeer:
            scores = np.absolute(scores)

        # avoid voting for myself
        scores[self.id - 1] = np.max(scores) + 1

        return np.argmin(scores) + 1


    def dayStart(self):
        print("Executing dayStart...")

        #TODO - add here what happens at first day - werewolf and seer
        self.pickTarget()

    def talk(self):
        print("Executing talk...")

        #TODO - maybe talk of villagers?
        
        if self.my_role == "WEREWOLF":
            #with proba , estimate our target as wolf ,with proba q comingout target as wolf, 1-p-q skip talking 
            p = np.random.uniform()
            if p < .35:     
                talk = cb.estimate(self.current_target, "WEREWOLF")
            #if we're sure - comingout
            elif p > .6:
                talk = cb.comingout(self.current_target, "WEREWOLF")
            else: #skip
                talk = cb.skip()
            return talk

        #if i am seer and i know most of werewolves - tell the world i know the werewolves as seer
        if self.seer_id == self.id:
            werewolves = [x for x in self.divine_map if self.divine_map[x] == "WEREWOLF"]

            #if we know more than half of the werewolves, reveal one of them
            if len(werewolves) >= 0.5 * self.ww_number:
                living_ww = [x for x in werewolves if self.base_info["statusMap"][str(x+1)] == "ALIVE"]
                if len(living_ww) > 0:
                    return cb.divined(random.choice(living_ww, "WEREWOLF"))

        #if we're not sure our target is a werewolf - estimate
        if not self.current_target in self.black_list:     
            talk = cb.estimate(self.current_target, "WEREWOLF")
        #if we're sure - comingout
        else:
            talk = cb.comingout(self.current_target, "WEREWOLF")

        return talk

    def whisper(self):
        print("Executing whisper...")
            
        if self.current_target != None:
            selected = self.current_target
            print("Whispering request against current target: "+str(selected))
        else:
            selected = randomPlayerId(self.base_info)
            print("Whispering request against random agent: "+str(selected))
        return cb.request(cb.attack(selected))

    def vote(self):
        return self.current_target

    def attack(self):
        print("Executing attack...")
        if self.current_target != None:
            selected = self.current_target
            print("Attacking current target: "+str(selected))
        else:
            selected = randomPlayerId(self.base_info)
            print("Attacking random agent: "+str(selected))
        return selected
        
    def divine(self):
        print("Executing divine...")

        target = self.minimal_score(isSeer=True)
        return target

    def guard(self):
        print("Executing guard randomly...")

        # if there's an uncontested seer, protect him
        if self.seer_id not in [None, -1]:
            return self.seer_id

        # if there's an uncontested medium, protect him
        if self.medium_id not in [None, -1]:
            return self.medium_id

        #TODO - maybe add some heuristic for villagers...
        
        #protect myself
        return self.id
    
    def finish(self):
        print("Executing finish...")

    def updatePlayerMap(self, base_info):
        for key, value in base_info["statusMap"].items():
            agent_id = int(key)
            if agent_id is not self.id:
                if agent_id not in self.player_map:
                    self.player_map[agent_id] = {}
                    self.player_map[agent_id]["targetStatus"] = 0
                    self.player_map[agent_id]["revenge"] = False
                self.player_map[agent_id]["status"] = value
                self.player_map[agent_id]["whispered"] = False

    def updateGameHistory(self, diff_data):
        '''
        if a player changes his mind about someone during talk, we need to know that.
        Therefore, we scan the talks in reversed order, and keep only the last opinion
        '''
        checked_pairs = []
        for row in reversed(list(diff_data.itertuples())):
            agent = getattr(row, "agent") - 1
            text = getattr(row, "text")
            talk_type = getattr(row, "type")
            
            if talk_type == "divine":
                match = re.match(RE_DIVINED, text)
                
                target_role = match.group("species")
                target = match.group("target")
                target_id = int(re.match(RE_AGENT_GROUP, target).group("id")) - 1

                self.divine_map[target_id] = target_role
                
                if target_role == "VILLAGER":
                    self.white_list.append(target_id)
                else:
                    self.black_list.append(target_id)
                continue

            #if it's our talking, we don't need to analyze it
            if agent == self.id:
                continue

            target = None
            target_role = None
            
            #find the target of sentence
            if "ESTIMATE" in text:
                match = re.match(RE_ESTIMATE, text[text.index("ESTIMATE"):])
            elif "VOTE" in text:
                match = re.match(RE_VOTE, text[text.index("VOTE"):])
            elif "COMINGOUT" in text:
                match = re.match(RE_COMINGOUT, text[text.index("COMINGOUT"):])
            elif "DIVINED" in text:
                match = re.match(RE_DIVINED, text[text.index("DIVINED"):])
            elif "IDENTIFIED" in text:
                match = re.match(RE_IDENTIFIED, text[text.index("IDENTIFIED"):])
            elif "GUARDED" in text:
                match = re.match(RE_GUARDED, text[text.index("GUARDED"):])
            else:
                continue

            target_role = match.group("role") if "role" in match.groupdict() else None
            target = match.group("target")
            target_id = int(re.match(RE_AGENT_GROUP, target).group("id")) - 1

            #if we already saw the last things the agent had to say about the target,
            # no need to read previous talks
            if [agent, target_id] in checked_pairs:
                continue
            #if this is the 'last word' of the agent about the target, keep processing it
            else:
                checked_pairs.append([agent, target_id])

            if target != "ANY":
                # this variable says whether we are unjustly targeted
                if "ESTIMATE" in text or "DIVINED" in text:
                    # Check if we're being accused of a role we are not
                    lie = (target_id == self.id and self.base_info["myRole"] != target_role)
                elif "VOTE" in text or "COMINGOUT" in text:
                    # Check if we're being voted
                    lie = target_id == self.id
                        
            #we give 0.5 point for estimates - positive for "villager", negative for "werewolf"
            if "ESTIMATE" in text and not lie:
                #add to score of the target the value we accord to seer
                self.info_table[target_id][agent] += 0.5 if target_role == "VILLAGER" else -0.5

            #we give 1 point for votes - positive for "villager", negative for "werewolf"
            elif ("VOTE" in text or "COMINGOUT" in text) and not lie:
                #add to score of the target the value we accord to seer
                self.info_table[target_id][agent] += 1 if target_role == "VILLAGER" else -1
            
            
            elif "DIVINED" in text:
                '''
                Someone is pretending to be seer:
                * if he tells about us wrong information, we know him for a werewolf
                * if we are the seer, we know him for a werewolf
                * if no conflict occurs, we believe him
                * if another one says he is seer, put the two of them in conflict list and believe none
                '''
                #if i am the seer and not the talker, or if he lies about me, kill him!
                if self.seer_id == self.id or lie:
                    if self.seer_id == agent:
                        self.seer_id = None
                        self.seer_value = 2
                    self.black_list.append(agent)
                #if there's already a seer, and the current one contests him, put them in conflict
                elif self.seer_id != agent and self.seer_id != None:
                    self.conflict_list.append([self.seer_id, agent])
                    self.seer_value = 1
                    self.seer_id = -1
                else:
                    if self.seer_id == None:
                        self.seer_id = agent

                #add to score of the target the value we accord to seer
                self.info_table[target_id][agent] += 1 if target_role == "VILLAGER" else -1


            # medium works like seer approximately
            elif "IDENTIFIED" in text:
                if self.medium_id == self.id:
                    self.black_list.append(agent)
                elif self.medium_id != agent and self.medium_id != None:
                    self.conflict_list.append([self.medium_id, agent])
                    self.medium_value = 1
                    self.medium_id = -1
                else:
                    if self.medium_id == None:
                        self.medium_id = agent

                #add to score of the target the value we accord to seer
                self.info_table[target_id][agent] += 1 if target_role == "VILLAGER" else -1

            # bodyguard works like seer approximately
            elif "GUARDED" in text:
                if self.bg_id == self.id:
                    self.black_list.append(agent)
                #if there are no dead
                elif self.no_dead:
                    #bodyguard contested    
                    if self.bg_id != agent and self.bg_id != None:
                        self.conflict_list.append([self.bg_id, agent])
                        self.bg_value = 1
                        self.bg_id = -1
                    #bodyguard not contested
                    else:
                        self.bg_id = agent if self.bg_id == None else self.bg_id
                #there were dead during night
                else:
                    pass
                self.info_table[target_id][agent] += 1
            
        self.updateConflicts()

    #find conflicts that can be resolved and erase them
    def updateConflicts(self):
        #identify all those in conflict with werewolves as villagers
        for ww in self.black_list:
            for pair in self.conflict_list:
                if ww in pair:
                    for player in pair:
                        if player != ww:
                            self.white_list.append(player)
                self.conflict_list.remove(pair)        
            
            
                               
    def setTarget(self, id):
        self.current_target = id

def parseArgs(args):
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage=usage) 

    # need this to ensure -h (for hostname) can be used as an option 
    # in optparse before passing the arguments to aiwolfpy
    parser.set_conflict_handler("resolve")

    parser.add_option('-h', action="store", type="string", dest="hostname",
        help="IP address of the AIWolf server", default=None)
    parser.add_option('-p', action="store", type="int", dest="port", 
        help="Port to connect in the server", default=None)
    parser.add_option('-r', action="store", type="string", dest="port", 
        help="Role request to the server", default=-1)
    
    (opt, args) = parser.parse_args()
    if opt.hostname == None or opt.port == -1:
        parser.print_help()
        sys.exit()

if __name__ == '__main__':    
    parseArgs(sys.argv[1:])
    aiwolfpy.connect_parse(SampleAgent("loupgarou"))
