'''
	Generates neural net training data by solving random poker situations.
'''

from ..Settings.arguments import arguments
from ..Settings.game_settings import game_settings
from ..DataGeneration.random_card_generator import card_generator
from ..Settings.constants import constants
from ..DataGeneration.range_generator import RangeGenerator
from ..Nn.bucketer import Bucketer
from ..Nn.bucket_conversion import BucketConversion
from ..TerminalEquity.terminal_equity import TerminalEquity
from ..Lookahead.lookahead import Lookahead
from ..Lookahead.resolving import Resolving

class DataGeneration():
	def __init__(self):
		pass

	def generate_data(self, train_data_count, valid_data_count):
		''' Generates training and validation files by sampling random poker
			situations and solving them.
			Makes two calls to @{generate_data_file}. The files are saved to
			@{arguments.data_path}, respectively appended with `valid` and `train`.
		@param: train_data_count the number of training examples to generate
		@param: valid_data_count the number of validation examples to generate
		'''
		pass
		# valid data generation
		# train data generation


	def generate_data_file(self, data_count, file_name):
		''' Generates data files containing examples of random poker situations with
			counterfactual values from an associated solution.
			Each poker situation is randomly generated using @{range_generator} and
			@{random_card_generator}. For description of neural net input and target
			type, see @{net_builder}.
		@param: data_count the number of examples to generate
		@param: file_name the prefix of the files where the data is saved (appended
				with `.inputs`, `.targets`, and `.mask`).
		'''
		pass
		# generating ranges
		# generating pot sizes between ante and stack - 0.1
		# pot features are pot sizes normalized between (ante/stack,1)
		# translating ranges to features
		# computaton of values using re-solving
		# translating values to nn targets
		# computing a mask of possible buckets




data_generation = DataGeneration()
