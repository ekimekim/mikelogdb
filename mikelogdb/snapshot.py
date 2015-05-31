
from copy import deepcopy

from util import EMPTY, json_load, json_dump, json_dump_pretty
from transaction import Transaction


class Snapshot(object):
	"""Represents a coalesced version of the database's state.
	Snapshots in general should be immutable. Exercise caution handing the data
	to users which might modify it. Note that all copies are deep copies for this reason."""

	def __init__(self, transaction=None, data=None):
		"""data is initial state. transaction may be None to represent no starting point; the first
		transaction applied MUST be tid 0. Otherwise transaction is the most recently applied transaction."""
		self.transaction = transaction
		if data is None:
			self.data = {}
		else:
			self.data = deepcopy(data)

	@property
	def tid(self):
		"""The tid we are up to."""
		return self.transaction.tid if self.transaction is not None else None

	def copy(self):
		return Snapshot(self.transaction, self.data)

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
			if transaction.parent != self.transaction.hash:
				raise ValueError("Hash mismatch - tried to apply {!r}, snapshot expected {!r}".format(
				                 transaction.parent, self.transaction.hash))

		result = Snapshot(transaction, self.data)

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
			except TypeError as e:
				raise ValueError("Error applying transaction {!r}: TypeError while changing key {}[{}]: {}".format(
				                 transaction, prefix_str(), key, e))

		return result

	def to_data(self):
		return dict(transaction=self.transaction.to_data(), data=self.data)

	def json(self):
		return json_dump(self.to_data())

	@classmethod
	def from_str(cls, s):
		data = json_load(s)
		t = Transaction(**data['transaction'])
		return cls(t, data['data'])

	def __repr__(self):
		return "<{} of {!r}>".format(type(self).__name__, self.transaction)

	def __str__(self):
		return json_dump_pretty(self.to_data())

	def commit(self, initial, parent=None):
		"""Helper method that creates a transaction going from given initial snapshot to this snapshot,
		and returns (transaction, new_snapshot) where new_snapshot correctly records transaction
		as the most recent transaction."""
		t = self.diff(initial, parent)
		s = Snapshot(t, self.data)
		return t, s

	def diff(self, initial, parent=None):
		"""Take the diff from initial snapshot to this snapshot, and return it as a transaction.
		If not given, parent defaults to self.transaction"""
		actions = self._diff(initial.data, self.data)
		return Transaction(self.transaction, actions)

	def _diff(self, a, b, prefix=()):
		"""Returns changes (prefix + path, old, new) from a to b.
		Note that if a == b then we return [], and if a and b are incompatible we return
		[(prefix, a, b)]"""
		results = []
		if isinstance(a, list) and isinstance(b, list):
			for n, (old, new) in enumerate(zip(a, b)):
				path = prefix + (n,)
				results += self._diff(old, new, prefix=path)
		elif isinstance(a, dict) and isinstance(b, dict):
			for key in set(a)| set(b):
				old = a.get(key, EMPTY)
				new = b.get(key, EMPTY)
				assert (a, b) != (EMPTY, EMPTY), "Key in neither dict, or EMPTY present in dict"
				path = prefix + (key,)
				results += self._diff(old, new, prefix=path)
		else:
			results = [(prefix, a, b)]
		return results
