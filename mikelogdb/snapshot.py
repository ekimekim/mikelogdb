
from copy import deepcopy

from util import EMPTY, json_dump, json_dump_pretty


class Snapshot(object):
	"""Represents a coalesced version of the database's state.
	Snapshots in general should be immutable. Exercise caution handing the data
	to users which might modify it. Note that all copies are deep copies for this reason."""

	def __init__(self, tid=None, data=None):
		"""data is initial state. tid may be None to represent no starting point; the first
		transaction applied MUST be tid 0."""
		self.tid = tid
		if data is None:
			self.data = {}
		else:
			self.data = deepcopy(data)

	def copy(self):
		return Snapshot(self.tid, self.data)

	def apply(self, transaction):
		"""Apply the transaction to this snapshot, returning a new snapshot."""
		if self.tid is None:
			if transaction.tid != 0:
				raise ValueError("Attempted to apply tid {} to an uninitialized snapshot".format(
				                 transaction.tid))
		else:
			if transaction.tid != self.tid + 1:
				raise ValueError("Attempted to apply tid {} to a snapshot at tid {}".format(
				                 transaction.tid, self.tid))

		result = Snapshot(transaction.tid, self.data)

		for path, old, new in transaction.actions:
			path, path_end = path[:-1], path[-1]
			prefix = ()
			prefix_str = lambda: ''.join('[{!r}]'.format(part) for part in prefix)
			data = result.data
			try:
				for part in path:
					key = part
					data = data[key]
					prefix += part,
				key = path_end
				if old is not EMPTY and data[key] != old:
					raise ValueError("Error applying transaction {!r}: expected root{}[{}] == {!r}, got {!r}".format(
					                 transaction, prefix_str(), key, old, data[key]))
				if new is not EMPTY:
					data[key] = new
				elif old is not EMPTY:
					del data[key]
			except (KeyError, IndexError):
				raise ValueError("Error applying transaction {!r}: root{} has no key {}".format(
				                 transaction, prefix_str(), key))

		return result	

	def json(self):
		return json_dump(self.data)

	def __repr__(self):
		return "<{} tid={}>".format(type(self).__name__, self.tid)

	def __str__(self):
		return json_dump_pretty(self.data)
