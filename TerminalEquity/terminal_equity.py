'''
	Evaluates player equities at terminal nodes of the game's public tree.
'''
import os
import numpy as np

from Game.Evaluation.evaluator import evaluator
from Settings.game_settings import game_settings
from Settings.arguments import arguments
from Settings.constants import constants
from Game.card_tools import card_tools
from tools import tools

class TerminalEquity():
	def __init__(self):
		# init call and fold matrices
		self.equity_matrix = None # [I,I] can be named as call matrix
		self.fold_matrix = None # [I,I]
		# load preflop matrix
		self._pf_equity = np.load('TerminalEquity/pf_equity.npy')
		# load card blocking matrix from disk if exists
		if os.path.exists('TerminalEquity/block_matrix.npy'):
			self._block_matrix2 = np.load('TerminalEquity/block_matrix.npy')
		else:
			self._create_block_matrix()


	def _create_block_matrix(self):
		HC, CC = game_settings.hand_count, game_settings.card_count
		self._block_matrix = np.ones([HC,HC], dtype=bool)
		for p1_card1 in range(CC):
			for p1_card2 in range(p1_card1+1, CC):
				p1_idx = card_tools.get_hole_index([p1_card1, p1_card2])
				for p2_card1 in range(CC):
					for p2_card2 in range(p2_card1+1, CC):
						p2_idx = card_tools.get_hole_index([p2_card1, p2_card2])
						if p1_card1 == p2_card1 or p1_card1 == p2_card2 or \
						   p1_card2 == p2_card1 or p1_card2 == p2_card2:
						   self._block_matrix[p1_idx, p2_idx] = 0
						   self._block_matrix[p2_idx, p1_idx] = 0


	def set_last_round_call_matrix(self, call_matrix, board_cards):
		''' Constructs the matrix that turns player ranges into showdown equity.
			Gives the matrix `A` such that for player ranges `x` and `y`, `x'Ay`
			is the equity for the first player when no player folds.
		@param: board_cards a non-empty vector of board cards
		@param: call_matrix a tensor where the computed matrix is stored
		'''
		HC = game_settings.hand_count
		if board_cards.ndim != 0:
			assert(board_cards.shape[0] == 1 or board_cards.shape[0] == 2 or board_cards.shape[0] == 5) # Only Leduc, extended Leduc, and Texas Holdem are supported
		strength = evaluator.batch_eval_fast(board_cards)
		# handling hand stregths (winning probs)
		strength_view_1 = strength.reshape([HC,1]) # * np.ones_like(call_matrix)
		strength_view_2 = strength.reshape([1,HC]) # * np.ones_like(call_matrix)

		call_matrix[:,:]  = (strength_view_1 > strength_view_2).astype(int)
		call_matrix[:,:] -= (strength_view_1 < strength_view_2).astype(int)


	def set_inner_call_matrix(self, call_matrix, next_round_boards, street):
		''' Constructs the matrix that turns player ranges into showdown equity.
			Gives the matrix `A` such that for player ranges `x` and `y`, `x'Ay`
			is the equity for the first player when no player folds.
		@param next_round_boards [b,5] a non-empty vector of board cards
		@param call_matrix a tensor where the computed matrix is stored
		'''
		HC, num_boards = game_settings.hand_count, next_round_boards.shape[0]
		BCC, CC = game_settings.board_card_count, game_settings.card_count
		if next_round_boards.ndim != 0:
			assert(next_round_boards.shape[1] == 0 or next_round_boards.shape[1] == 2 or next_round_boards.shape[1] == 5) # Only Leduc, extended Leduc, and Texas Holdem are supported
		strength = evaluator.batch_eval_fast(next_round_boards) # [b,I]
		# handling hand stregths (winning probs)
		strength_view_1 = strength.reshape([num_boards,HC,1]) * np.ones([num_boards, HC, HC], dtype=strength.dtype)
		strength_view_2 = strength.reshape([num_boards,1,HC]) * np.ones_like(strength_view_1)
		possible_mask = (strength < 0).astype(int)

		matrix_mem = (strength_view_1 > strength_view_2).astype(int)
		matrix_mem *= possible_mask.reshape([num_boards,1,HC]) # * np.ones([num_boards,HC,HC], dtype=possible_mask.dtype)
		matrix_mem *= possible_mask.reshape([num_boards,HC,1]) # * np.ones([num_boards,HC,HC], dtype=possible_mask.dtype)
		call_matrix[:,:] = np.sum(matrix_mem, axis=0)

		matrix_mem = (strength_view_1 < strength_view_2).astype(int)
		matrix_mem *= possible_mask.reshape([num_boards,1,HC]) # * np.ones([num_boards,HC,HC], dtype=possible_mask.dtype)
		matrix_mem *= possible_mask.reshape([num_boards,HC,1]) # * np.ones([num_boards,HC,HC], dtype=possible_mask.dtype)
		call_matrix[:,:] = call_matrix - np.sum(matrix_mem, axis=0)
		# normalize sum
		num_cards_on_board = BCC[street-1]
		num_cards_in_hand = game_settings.hand_card_count
		num_players = constants.players_count
		cards_to_come = BCC[-1] - num_cards_on_board
		cards_left = CC - (num_cards_in_hand * num_players + num_cards_on_board)
		num_possible_hands = tools.choose(cards_left, cards_to_come)
		call_matrix[:,:] = call_matrix / num_possible_hands



	def _handle_blocking_cards(self, equity_matrix, board):
		''' Zeroes entries in an equity matrix that correspond to invalid hands.
			 A hand is invalid if it shares any cards with the board.
		@param: equity_matrix the matrix to modify
		@param: board a possibly empty vector of board cards
		'''
		HC, CC = game_settings.hand_count, game_settings.card_count
		possible_hand_indexes = card_tools.get_possible_hand_indexes(board)
		equity_matrix[:,:] *= possible_hand_indexes.reshape([1,HC])
		equity_matrix[:,:] *= possible_hand_indexes.reshape([HC,1])
		equity_matrix[:,:] *= self._block_matrix


	def get_hand_strengths(self):
		HC = game_settings.hand_count
		return np.dot(np.ones([1,HC]), self.equity_matrix)


	def set_board(self, board):
		''' Sets the board cards for the evaluator and creates its internal data
			structures.
		@param: board a possibly empty vector of board cards
		'''
		self.board, street, HC = board, card_tools.board_to_street(board), game_settings.hand_count
		# set call matrix
		if street == 1:
			self.equity_matrix = self._pf_equity.copy()
		elif street == constants.streets_count:
			self.equity_matrix = np.zeros([HC,HC], dtype=arguments.dtype)
			self.set_last_round_call_matrix(self.equity_matrix, board)
			self._handle_blocking_cards(self.equity_matrix, board)
		elif street == 2 or street == 3:
			self.equity_matrix = np.zeros([HC,HC], dtype=arguments.dtype)
			next_round_boards = card_tools.get_last_round_boards(board)
			self.set_inner_call_matrix(self.equity_matrix, next_round_boards, street)
			self._handle_blocking_cards(self.equity_matrix, board)
		else:
			assert(False) # bad street/board
		# set fold matrix
		self.fold_matrix = np.ones([HC,HC], dtype=arguments.dtype)
		# setting cards that block each other to zero
		self._handle_blocking_cards(self.fold_matrix, board)




	def call_value(self, ranges, result):
		''' Computes (a batch of) counterfactual values that a player achieves
			at a terminal node where no player has folded.
		@{set_board} must be called before this function.
		@param: ranges a batch of opponent ranges in an (N,K) tensor, where
				N is the batch size and K is the range size
		@param: result a (N,K) tensor in which to save the cfvs
		'''
		result[ : , : ] = np.dot(ranges, self.equity_matrix)


	def fold_value(self, ranges, result):
		''' Computes (a batch of) counterfactual values that a player achieves
			at a terminal node where a player has folded.
		@{set_board} must be called before this function.
		@param: ranges a batch of opponent ranges in an (N,K) tensor, where
				N is the batch size and K is the range size
		@param: result A (N,K) tensor in which to save the cfvs. Positive cfvs
				are returned, and must be negated if the player in question folded.
		'''
		result[ : , : ] = np.dot(ranges, self.fold_matrix)


	def get_call_matrix(self):
		''' Returns the matrix which gives showdown equity for any ranges.
		@{set_board} must be called before this function.
		@return For nodes in the last betting round, the matrix `A` such that for
				player ranges `x` and `y`, `x'Ay` is the equity for the first
				player when no player folds. For nodes in the first betting round,
				the weighted average of all such possible matrices.
		'''
		return self.equity_matrix


	def tree_node_call_value(self, ranges, result): # ? - ar reikia
		''' Computes the counterfactual values that both players achieve at a
			terminal node where no player has folded.
		@{set_board} must be called before this function.
		@param: ranges a (2,K) tensor containing ranges for each player
				(where K is the range size)
		@param: result a (2,K) tensor in which to store the cfvs for each player
		'''
		assert(ranges.ndim == 2 and result.ndim == 2)
		self.call_value(ranges[0].reshape([1,-1]), result[1].reshape([1,-1]))
		self.call_value(ranges[1].reshape([1,-1]), result[0].reshape([1,-1]))


	def tree_node_fold_value(self, ranges, result, folding_player): # ? - ar reikia
		''' Computes the counterfactual values that both players achieve at a
			terminal node where either player has folded.
		@{set_board} must be called before this function.
		@param: ranges a (2,K) tensor containing ranges for each player
				(where K is the range size)
		@param: result a (2,K) tensor in which to store the cfvs for each player
		@param: folding_player which player folded
		'''
		assert(ranges.ndim == 2 and result.ndim == 2)
		self.fold_value(ranges[0].reshape([1,-1]), result[1].reshape([1,-1])) # np?
		self.fold_value(ranges[1].reshape([1,-1]), result[0].reshape([1,-1]))
		result[folding_player] *= -1




#
