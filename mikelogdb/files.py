


class TransactionsFile(file):
	def __iter__(self):
		"""Yield Transaction objects instead of lines"""
		while True:
			t = self.read_transaction()
			if not t:
				return
			yield t

	def read_transaction(self):
		line = self.readline()
		if not line.endswith('\n'):
			return # EOF reached
		return Transaction.from_str(line.strip())
