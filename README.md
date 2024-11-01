# air_game

## play description

It's an air dogfight game.
Just like some battleship games, the game require two players to envolve.
Before the game start, each one will have a gameboard on the left of the window. you may meet some obstacles and you should place three planes which can rotate at your will on it. Of course, **NO PLANES CAN BE OVERLAPPED NOR HIT OBSTACLES**. Then, you press "confirm planes" to start battle. 
During battle, you may hit 1 block of your opponent per turn. If you hit your opponent's plane except the **HEAD**. There will be a blue cell displayed on your right playboard. If you hit nothing, there will be a red cell and black if there's nothing. If your opponent hits your plane, you will see one part of your plane turn green.
If you (or your opponent) hit all 3 planes' heads of your opponent. You will win the game.

## HOW TO PLAY

If you want to play the game.You must install python.
Following packages are required:

```text
tkinter
```
and you should change the host ip at line 94 if you want to join one's game on LAN.

If you are host, just run 

```bash
python ./new_air.py

```
and enter y to be a host.(on port 12345, make sure your firewall allows your connection and you may not use a proxy)

If you want to join game, just run the same command and enter n to search one's host game.

