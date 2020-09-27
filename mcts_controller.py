import json
import sys
import math
import random
from time import sleep
from copy import copy, deepcopy

class Action:
    def __init__(self, knight_id, mov):

        self.knight_id = knight_id                              #id del caballo a mover
        self.mov = mov                                          #movimiento del caballo

class State:  

    def __init__(self, board, aliados, enemigos, accion):
        
        self.board = deepcopy(board)                            #diccionario ids
        self.aliados = aliados                                  #diccionario de aliados
        self.enemigos = enemigos                                #diccionario de enemigos                                   
        self.accion = accion                                    #última acción que dio origen al estado actual
        self.final_state = False
        #movimientos del caballo
        #self.delta = [[1, -2], [2, -1], [2, 1], [1, 2], [-1, 2], [-2, 1], [-2, -1], [-1, -2]]
        self.delta = [[1, 2], [2, 1], [2, -1], [1, -2], [-1, -2], [-2, -1], [-2, 1], [-1, 2]]

    def jugadas_posibles(self, s, coord):

        moves = []                                              #lista de movimientos
        new = [0, 0]
        for x in range(len(self.delta)):                        #recorre el número de movimientos posibles segun el delta
            new[0] = coord[0] + self.delta[x][0]                #crea tupla de la posición más el delta[x]
            new[1] = coord[1] + self.delta[x][1] 
            if self.comprueba(s, coord, x):                     #pregunta si la jugada es válida
                moves.append(x)                                 #si es válida, la agrega a la lista
        return moves

    def comprueba(self, s, coord, mov):

        new = [0, 0]
        new[0] = coord[0] + self.delta[mov][0]                  #crea tupla de posición más el delta[mov]
        new[1] = coord[1] + self.delta[mov][1]
        comp1 = all(a < b for a, b in zip(new, (8, 8)))         #compara que tanto i comno j sean menores que 8 (dentro del tablero)
        comp2 = all(a >= b for a, b in zip(new, (0, 0)))        #compara que tanto i como j sean mayores o iguales a cero
        if comp1 and comp2:                                     #si está dentro del tablero
            for x in s.aliados:                                 #recorre lista de caballos aliados
                if x == new:                                    #si encuentra un caballo con la misma posición
                    return False                                #la jugada es inválida
            return True                                         #si pasa todas las pruebas la jugada es válida
        else:
            return False                                        #si está fuera del tablero, la jugada es inválida

    def transition(self, s, a):

        coord = self.delta[a.mov]
        x = coord[0]
        y = coord[1]
        knight = a.knight_id

        caballo = 0
        for filas in s.board:                                           #removiendo caballo de posición antigua en el tablero
            for cols in filas:
                caballo = cols
                if caballo == knight:
                    caballo = "null"
                    break

        enemy_coord = []
        for enemy in s.enemigos:                                        #comprobando si elimina algún caballo enemigo, enemy = knight_id del enemigo
            enemy_coord = s.enemigos[enemy]
            if enemy_coord[0] == x and enemy_coord[1] == y:
                self.rem_knight(s, x, y, enemy)                         #eliminando caballo enemigo
                self.add_knight(s, x, y, a.knight_id)                   #colocando el caballo aliado en la nueva posición                         
                if not s.enemigos:                                      #si la lista de enemigos está vacía, res = false
                    final = State(s.board, s.aliados, s.enemigos, a)    #si la lista de enemigos está vacía, se ganó el juego y se llegó a un estado final
                    final.final_state = True
                    return final
                return State(s.board, s.aliados, s.enemigos, a)         #se retorna el nuevo estado  
        self.add_knight(s, x, y, a.knight_id)                           #en caso de que no haya algún enemigo en la nueva posición
        return State(s.board, s.aliados, s.enemigos, a)

    def add_knight(self, s, x, y, knight_id):

        row = s.board[x]
        row[y] = knight_id
        s.aliados[knight_id] = [x, y]                           #actualizando diccionario de aliados
        return

    def rem_knight(self, s, x, y, knight_id):                   #solo se usa cuando se elimina caballo enemigo

        row = s.board[x]
        row[y] = "null"
        del s.enemigos[knight_id]
        return



class Node:

    def __init__(self, state, simulations, reward, parent, children):
        self.state = state			                            #estado del nodo
        self.simulaciones = 1                                   #número de simulaciones
        self.reward = reward		                            #valor de recompensa del nodo
        self.parent = parent		                            #referencia al padre
        self.children = children		                        #arreglo de hijos
        self.c = 1/(pow(2, 1/2))

    def get_actions(self, s : State):

        actions = []                                                    #lista de acciones
        moves = []
        m = []
        for knight_id in s.aliados:                                     #recorriendo lista de mis caballos
            
            moves = s.jugadas_posibles(s, s.aliados[knight_id])         #obteniendo lista de jugadas posibles de cada caballo
            for i in range(len(moves)):                                 #recorriendo lista de jugadas posibles
                m = moves[i]                                            #obteniendo cada movimiento [i, j]
                a = Action(knight_id, m)                                #creando acción con el caballo y movimiento correspondientes
                actions.append(a)                                       #añadiendo la accion a la lista
        return actions

    def expand(self, nodo):

        s = nodo.state
        actions = self.get_actions(s)
        a = random.choice(actions)
        new_s = nodo.state.transition(s, a)
        nuevo_nodo = Node(new_s, 1, nodo.reward, nodo, [])
        nodo.children.append(nuevo_nodo)
        return nodo

    def best_child(self, nodo, c):

        mayor = 0
        cons = 0
        index_mayor = 0

        for i in range(len(nodo.children)):
            sim = nodo.children[i].simulaciones
            sim_padre = nodo.simulaciones
            x_m = nodo.children[i].reward / sim
            cons = ( 2*math.log(sim_padre) )/( sim )
            uct = x_m + ( 2 * c * ( pow(cons, 1/2) ) )
            if uct > mayor:
                mayor = uct
                index_mayor = i  
        return nodo.children[index_mayor]

    def get_reward(self, nodo):

        res = self.is_final_state(nodo)
        if res:
            return 1
        return 0

    def is_final_state(self, nodo):

        s = nodo.state
        return s.final_state

    def default_policy(self, nodo, limit_expand):
	    
        res = self.is_final_state(nodo)
        s = nodo.state
        limit_expand_count = 0
        while not res or limit_expand_count <= limit_expand:
            nodo.simulaciones += 1
            limit_expand_count += 1
            actions = self.get_actions(s)
            a = random.choice(actions)
            s = s.transition(s, a)
        return reward(s)

    def tree_policy(self, nodo, limit_expand):

        res = self.is_final_state(nodo)
        s = nodo.state
        actions = self.get_actions(s)
        res = bool(actions)
        limit_expand_count = 0
        while not res or limit_expand_count <= limit_expand:
            if res:
                return self.expand(nodo)
            nodo = self.best_child(nodo, self.c)
        return nodo

    def backup(self, nodo, delta):

        while nodo != None:
            nodo.simulaciones += 1
            nodo.reward += get_reward(nodo)
            nodo = nodo.parent

    def montecarlo(self, s):
    
        padre = Node(s, 0, 0, None, [])
        n = self.tree_policy(padre, 32)
        while not padre.is_final_state:
            reward = self.default_policy(n.state, 32)
            self.backup(n, reward)
            n = self.tree_policy(padre, 32)
        prodigo = self.best_child(n, self.c)
        return prodigo


def controlador(my_knights):

    board = list(state["ids"])

    aliados = state["my_knights_dict"]

    enemigos = state["enemy_knights_dict"]

    s = State(board, aliados, enemigos, None)

    zero = Node(s, 1, 0, None, [])
    nodo_mcts = zero.montecarlo(s)
    caballo = nodo_mcts.state.accion.knight_id
    mov = nodo_mcts.state.accion.mov
    
    result = {
        "knight_id": caballo,
        "knight_movement": mov
    }

    print(json.dumps(result))


if __name__ == "__main__":

    state_json = sys.argv[1]

    state_json = state_json.replace(r'\"', '"')

    state = json.loads(state_json)

    my_knights = list(state["my_knights_dict"].keys())
    
    controlador(my_knights)