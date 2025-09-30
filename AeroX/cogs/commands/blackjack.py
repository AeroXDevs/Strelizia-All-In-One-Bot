import discord 
from discord .ext import commands 
from discord .ui import View ,Button 
import os 
import random 
import asyncio 
from typing import List ,Tuple ,Union 
from PIL import Image 
from utils .Tools import *

CARDS_PATH ='data/cards/'

class Card :
    suits =["clubs","diamonds","hearts","spades"]

    def __init__ (self ,suit :str ,value :int ,down =False ):
        self .suit =suit 
        self .value =value 
        self .down =down 
        self .symbol =self .name [0 ].upper ()

    @property 
    def name (self )->str :
        if self .value <=10 :
            return str (self .value )
        else :
            return {
            11 :'jack',
            12 :'queen',
            13 :'king',
            14 :'ace',
            }[self .value ]

    @property 
    def image (self ):
        return (
        f"{self.symbol if self.name != '10' else '10'}" f"{self.suit[0].upper()}.png"if not self .down else "red_back.png"
        )

    def flip (self ):
        self .down =not self .down 
        return self 

    def __str__ (self )->str :
        return f'{self.name.title()} of {self.suit.title()}'

    def __repr__ (self )->str :
        return str (self )


class BlackjackView (View ):
    def __init__ (self ,player ,dealer ,deck ,bet_amount ,author ):
        super ().__init__ (timeout =300 )
        self .player =player 
        self .dealer =dealer 
        self .deck =deck 
        self .bet_amount =bet_amount 
        self .author =author 
        self .game_over =False 

    @discord .ui .button (label ="Hit",style =discord .ButtonStyle .success ,emoji ="🃏")
    async def hit_button (self ,interaction :discord .Interaction ,button :Button ):
        if interaction .user !=self .author :
            await interaction .response .send_message ("This isn't your game!",ephemeral =True )
            return 

        if self .game_over :
            await interaction .response .send_message ("Game is already over!",ephemeral =True )
            return 


        card =self .deck .pop ()
        self .player .append (card )

        player_total =Blackjack .calc_hand (self .player )


        if player_total >21 :
            self .game_over =True 
            embed =self .create_game_embed ("Player Busted!",
            f"Your total: {player_total}\nYou went over 21! You lose ${self.bet_amount}",
            discord .Color .red ())
            for item in self .children :
                item .disabled =True 
            await interaction .response .edit_message (embed =embed ,view =self )
            return 


        embed =self .create_game_embed ("Blackjack Game",
        f"Your total: {player_total}\nChoose your next action:",
        discord .Color .blue ())
        await interaction .response .edit_message (embed =embed ,view =self )

    @discord .ui .button (label ="Stand",style =discord .ButtonStyle .danger ,emoji ="✋")
    async def stand_button (self ,interaction :discord .Interaction ,button :Button ):
        if interaction .user !=self .author :
            await interaction .response .send_message ("This isn't your game!",ephemeral =True )
            return 

        if self .game_over :
            await interaction .response .send_message ("Game is already over!",ephemeral =True )
            return 


        for card in self .dealer :
            card .down =False 


        while Blackjack .calc_hand (self .dealer )<17 :
            card =self .deck .pop ()
            self .dealer .append (card )

        player_total =Blackjack .calc_hand (self .player )
        dealer_total =Blackjack .calc_hand (self .dealer )


        result =self .determine_winner (player_total ,dealer_total )

        self .game_over =True 
        for item in self .children :
            item .disabled =True 

        await interaction .response .edit_message (embed =result ["embed"],view =self )

    def create_game_embed (self ,title ,description ,color ):
        embed =discord .Embed (title =title ,description =description ,color =color )


        player_cards =", ".join ([str (card )for card in self .player ])
        player_total =Blackjack .calc_hand (self .player )
        embed .add_field (
        name =f"Your Hand ({player_total})",
        value =player_cards ,
        inline =False 
        )


        if self .game_over :
            dealer_cards =", ".join ([str (card )for card in self .dealer ])
            dealer_total =Blackjack .calc_hand (self .dealer )
            embed .add_field (
            name =f"Dealer's Hand ({dealer_total})",
            value =dealer_cards ,
            inline =False 
            )
        else :

            visible_cards =[self .dealer [0 ]]+["Hidden Card"]+[str (card )for card in self .dealer [2 :]]
            embed .add_field (
            name ="Dealer's Hand",
            value =", ".join (map (str ,visible_cards )),
            inline =False 
            )

        embed .add_field (name ="Bet Amount",value =f"${self.bet_amount}",inline =True )
        return embed 

    def determine_winner (self ,player_total ,dealer_total ):
        if dealer_total >21 :
            return {
            "embed":self .create_game_embed ("You Win!",
            f"Dealer busted with {dealer_total}! You win ${self.bet_amount}",
            discord .Color .green ())
            }
        elif player_total >dealer_total :
            return {
            "embed":self .create_game_embed ("You Win!",
            f"Your {player_total} beats dealer's {dealer_total}! You win ${self.bet_amount}",
            discord .Color .green ())
            }
        elif dealer_total >player_total :
            return {
            "embed":self .create_game_embed ("You Lose!",
            f"Dealer's {dealer_total} beats your {player_total}! You lose ${self.bet_amount}",
            discord .Color .red ())
            }
        else :
            return {
            "embed":self .create_game_embed ("Push!",
            f"Both have {player_total}! It's a tie. Bet returned.",
            discord .Color .yellow ())
            }

class Blackjack (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .active_games =set ()

    @staticmethod 
    def create_deck ():
        """Creates a standard 52-card deck"""
        deck =[]
        suits =["clubs","diamonds","hearts","spades"]
        for suit in suits :
            for value in range (2 ,15 ):
                deck .append (Card (suit ,value ))
        random .shuffle (deck )
        return deck 

    @staticmethod 
    def hand_to_images (hand :List [Card ])->List [Image .Image ]:
        return [Image .open (os .path .join (CARDS_PATH ,card .image ))for card in hand ]

    @staticmethod 
    def center (*hands :Tuple [Image .Image ])->Image .Image :
        bg :Image .Image =Image .open (os .path .join (CARDS_PATH ,'table.png'))
        bg_center_x =bg .size [0 ]//2 
        bg_center_y =bg .size [1 ]//2 

        img_w =hands [0 ][0 ].size [0 ]
        img_h =hands [0 ][0 ].size [1 ]

        start_y =bg_center_y -(((len (hands )*img_h )+((len (hands )-1 )*15 ))//2 )

        for hand in hands :
            start_x =bg_center_x -(((len (hand )*img_w )+((len (hand )-1 )*10 ))//2 )
            for card in hand :
                bg .alpha_composite (card ,(start_x ,start_y ))
                start_x +=img_w +10 
            start_y +=img_h +15 

        return bg 

    def output (self ,name ,*hands :Tuple [List [Card ]])->None :
        self .center (*map (self .hand_to_images ,hands )).save (f'data/{name}.png')

    @staticmethod 
    def calc_hand (hand :List [Card ])->int :
        non_aces =[c for c in hand if c .symbol !='A']
        aces =[c for c in hand if c .symbol =='A']
        total_sum =0 
        for card in non_aces :
            if not card .down :
                if card .symbol in 'JQK':
                    total_sum +=10 
                else :
                    total_sum +=card .value 
        for card in aces :
            if not card .down :
                if total_sum <=10 :
                    total_sum +=11 
                else :
                    total_sum +=1 
        return total_sum 

    @commands .hybrid_command (name ="blackjack",aliases =["bj"],help ="Play a game of Blackjack against the dealer")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,10 ,commands .BucketType .user )
    async def blackjack_game (self ,ctx ,bet :int =10 ):
        """
        Play Blackjack against the dealer
        
        Parameters:
        bet: Amount to bet (default: 10)
        """


        if ctx .author .id in self .active_games :
            await ctx .send (embed =discord .Embed (
            description ="You're already in a blackjack game! Finish it first.",
            color =0x000000 
            ))
            return 


        if bet <1 :
            await ctx .send (embed =discord .Embed (
            description ="Bet amount must be at least $1",
            color =0x000000 
            ))
            return 

        if bet >1000 :
            await ctx .send (embed =discord .Embed (
            description ="Maximum bet is $1000",
            color =0x000000 
            ))
            return 


        self .active_games .add (ctx .author .id )

        try :

            deck =self .create_deck ()


            player_hand =[deck .pop (),deck .pop ()]
            dealer_hand =[deck .pop (),deck .pop ()]


            dealer_hand [1 ].down =True 


            player_total =self .calc_hand (player_hand )
            dealer_total =self .calc_hand ([dealer_hand [0 ]])

            if player_total ==21 :

                dealer_hand [1 ].down =False 
                dealer_total =self .calc_hand (dealer_hand )

                if dealer_total ==21 :

                    embed =discord .Embed (
                    title ="Push! Both have Blackjack!",
                    description =f"Both you and the dealer have Blackjack! Your bet of ${bet} is returned.",
                    color =0xFFFF00 
                    )
                else :

                    winnings =int (bet *1.5 )
                    embed =discord .Embed (
                    title ="Blackjack! You Win!",
                    description =f"You got Blackjack! You win ${winnings}",
                    color =0x00FF00 
                    )

                embed .add_field (name ="Your Hand",value =f"{player_hand[0]}, {player_hand[1]} (21)",inline =False )
                embed .add_field (name ="Dealer's Hand",value =f"{dealer_hand[0]}, {dealer_hand[1]} ({dealer_total})",inline =False )

                self .active_games .remove (ctx .author .id )
                await ctx .send (embed =embed )
                return 


            view =BlackjackView (player_hand ,dealer_hand ,deck ,bet ,ctx .author )


            embed =view .create_game_embed ("Blackjack Game",
            f"Your total: {player_total}\nChoose your action:",
            discord .Color .blue ())


            await ctx .send (embed =embed ,view =view )


            await view .wait ()

        except Exception as e :
            await ctx .send (embed =discord .Embed (
            description =f"An error occurred: {str(e)}",
            color =0x000000 
            ))
        finally :

            self .active_games .discard (ctx .author .id )


"""
@Author: Aegis
    + Discord: Solcodez
    + Community: https://discord.strelix.xyz (AeroX Development)
    + for any queries reach out support or DM me.
"""
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
