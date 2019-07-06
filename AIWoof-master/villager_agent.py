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
        self.id = base_info["agentIdx"]
        self.base_info = base_info
        self.game_setting = game_setting

        self.game_history = {} # stores each sentence stated from each day
        self.player_map = {}   # a map with the status and other info for each player
        self.target_list = []  # a queue storing possible targets to act against
        self.current_target = None
        
        '''
        The info table stores the information we have about each player,
        along with it's provenance - the columns are the sources of information (other players)
        and the lines are the players - the sum of each line is a score - positive for villager, negative for werewolf.
        '''
        num_players = game_setting["playerNum"]
        
        self.info_table = np.zeros([num_players,num_players])

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

    def pickTarget(self):
        print("Executing pickTarget...")
        
        # we use a copy so that if the value of some player changes we still have the information
        table = np.copy(self.info_table)

        #if i have someone on my black list, choose him as target
        living_wws = [w for w in self.black_list if self.base_info["statusMap"][str(w)] == "ALIVE"]
        if len(living_wws) > 0:
            self.setTarget(living_wws[0])
            return
        else:
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
            self.setTarget(np.argmin(np.sum(table, axis=1)) + 1)



    def dayStart(self):
        print("Executing dayStart...")

        #TODO - add here what happens at first day - werewolf and seer

        self.pickTarget()

    def talk(self):
        print("Executing talk...")
        
        '''
        if self.player_map[self.current_target]["revenge"] is False: 
            print("Voting on random target")
        else:
            print("Voting for revenge!")
        '''
            
        # Talking against a target has 3 steps: (0) first estimate,
        # then (1) state your vote, then (>2) start requesting other 
        # agents to vote against the current target
        if self.player_map[self.current_target]["targetStatus"] == 0:     
            talk = cb.estimate(self.current_target, "WEREWOLF")
        elif self.player_map[self.current_target]["targetStatus"] == 1:
            talk = cb.vote(self.current_target)
        else:
            talk = cb.request(cb.vote(self.current_target))
            
        self.player_map[self.current_target]["targetStatus"] += 1
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
        print("Executing vote...")
        if self.current_target != None:
            selected = self.current_target
            print("Voting on current target: "+str(selected))
        else:
            selected = randomPlayerId(self.base_info)
            print("Voting on random agent: "+str(selected))
        return selected

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
        print("Executing divine randomly...")
        return randomPlayerId(self.base_info)

    def guard(self):
        print("Executing guard randomly...")
        return randomPlayerId(self.base_info)
    
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
        for row in diff_data.itertuples():

            #MEIR - not sure we need these 6 rows, since we integrate the information without using game_history
            current_day = getattr(row, "day")
            if current_day not in self.game_history:
                self.game_history[current_day] = {}

            current_turn = getattr(row, "turn")
            if current_turn not in self.game_history[current_day]:
                self.game_history[current_day][current_turn] = {}

            agent = getattr(row, "agent")
            text = getattr(row, "text")

                        #if it's our talking, we don't need it
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

            print("text is ", text)
            print(match, "FFFFF")
            
            target_role = match.group("role") if "role" in match.groupdict() else None
            target = match.group("target")
            target_id = int(re.match(RE_AGENT_GROUP, target).group("id")) - 1
            
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
                    #TODO = verify if we set target
                    self.setTarget(agent)
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
                    #TODO = verify if we set target
                    self.setTarget(agent)
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
                    #TODO = verify if we set target
                    self.setTarget(agent)
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
                    
            '''
            # if anyone votes, estimates, or divines on our agent
            # we set this person as a target
            if "{:02d}".format(self.id) in text:
                if "ESTIMATE" in text or "VOTE" in text or ("DIVINED" in text and "WEREWOLF" in text):
                    
                    # if we are pursuing revenge against someone already  
                    # add this new agent to the target list
                    if self.player_map[self.current_target]["revenge"] == True:
                        self.target_list.append(agent)
                    # otherwise, set this new agent as the current target
                    else:
                        self.setTarget(agent, True)
            '''
                        
    def setTarget(self, id):
        self.current_target = id
        self.player_map[id]["targetStatus"] = 0

        # Set someone as black for the first time
        if id not in self.black_list:
            self.black_list.append(id)

            #if we chose someone as target, it means all his info is wrong, and therefore multiplied by -1
            # DAN: Note, we can't do this once, we have to do this multiplier every time the agent accceses the info_table values
            #       so what this function should do isn't to multiply the values, it's to set a "multiply by -1" flag
            #self.info_table[:,id] *= -1

            # if i am certain the target is werewolf, make all those in conflict with him villagers
            for pair in self.conflict_list:
                if id in pair:
                    for player in pair:
                        if player != id:
                            self.white_list.append(player)
                        

##        self.player_map[id]["revenge"] = black_list


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
    aiwolfpy.connect_parse(SampleAgent("omgyousuck"))
