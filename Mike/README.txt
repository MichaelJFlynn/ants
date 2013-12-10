Hi Andrea,

I have created 3 generations of bots, each of increasing complexity,
MikeBotv1.py, MikeBotv2.py, and MikeBot.py. The first ignores enemies,
collects food and rushes the enemy base, the second collects food and
clumps to fight the enemy, the third uses minimax to fight. MikeBot.py
is the main bot and will have the most comments. To run a match use
(in the console):

./v1vsv2.sh

to run a match of MikeBotv1 vs MikeBotv2,

./v2vsv3.sh

to run a match of MikeBotv2 vs MikeBot, or

./v1vsv3.sh

to run a match of MikeBotv1 vs MikeBot.

You might have to chmod these shell scripts to be able to run them.
