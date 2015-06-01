
import hashlib

from util import LogDBException, json_load, json_dump, json_dump_pretty


class InvalidTransaction(LogDBException):
	pass


class Transaction(object):
	"""A transaction records a change in state.
	It has a monotonic transaction id, as well as the hash of its parent transaction.
	It, in turn, has a hash of its contents that can be used to refer to it.
	"""
	def __init__(self, parent, actions, tid=None, hash=None):
		"""Parent may be hash as b64 string, a Transaction object, or None.
		If parent is a Transaction, tid may be omitted. Only tid 0 may have parent None.
		hash should always be None - it is there to validate stored hash when restoring from json.
		Actons should be tuples (path, old, new)
		path should be a list of key lookups to reach value being modified.
		For example, an action that represents:
			root['foo']['bar'] = ["a"]
			root['foo']['bar'][0] = "b"
		would be given as:
			(('foo', 'bar', 0), "a", "b")
		To record creation or deletion (old value or new does not exist), use util.EMPTY.
		"""
		self.parent = parent
		self.actions = actions

		expected_tid = tid # by default, no check
		if isinstance(parent, Transaction):
			self.parent = parent.hash
			expected_tid = parent.tid + 1
		elif parent is None:
			expected_tid = 0

		if tid is None:
			tid = expected_tid
		if tid != expected_tid:
			raise InvalidTransaction("Expected tid {}, but given tid {}".format(parent.tid, tid))
		self.tid = tid

		if hash is not None and hash != self.hash:
			raise InvalidTransaction("Expected hash {}, but given {}".format(self.hash, hash))

	@classmethod
	def from_str(cls, s):
		"""Create from json string"""
		s = json_load(s)
		return cls(**s)

	def _data_without_hash(self):
		return dict(tid=self.tid, parent=self.parent, actions=self.actions)

	@property
	def hash(self):
		"""Note that returned value is a b64-encoded string"""
		data = self._data_without_hash()
		return hashlib.sha256(json_dump(data, sort_keys=True)).digest().encode('base64').strip()

	def to_data(self):
		data = self._data_without_hash()
		data['hash'] = self.hash
		return data

	def json(self):
		return json_dump(self.to_data())

	def __repr__(self):
		return "<{} {} ({})>".format(type(self).__name__, self.tid, self.hash[:8])

	def __str__(self):
		return json_dump_pretty(self.to_data())
