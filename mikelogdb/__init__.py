
"""
WARNING: This is strictly a *toy* implementation. Far better versions of this exact concept
have already been written by people who are much better at writing such things than me.
Use them. Don't use this.

Implementation overview

The database is a JSON store, its top level is a JSON object.
The current state is associated with a monotonic counter, let's call this the transaction_id.
Every update increments the counter.
Every update is stored as a transaction, consisting of:
	current transaction id
	list of actions:
		key changed
		old value
		new value
The purpose of being able to do multiple actions in one record is to guarentee atomicity.
The database is stored on-disk as a list of transactions in a file, called the "transaction_file".
The format of this file is of JSON objects seperated by newlines. The encoded JSON must not
contain a newline within its encoded representation.
For performance, further files may be provided called "snapshots". They represent the database contents
at a specified transation_id, allowing most of a large transation log to be skipped. In fact, the older
transactions could even be omitted entirely, though this is not reccomended.

The database is designed to be replicated, and to be able to send and receive transactions.
Note however that it is not designed for full distributed use, as care must be taken that every update operate
on top of the latest transaction. Some simple conflict resolution is available by marking objects with
merge strategies, allowing simple CRDTs - see merge.py

It is up to the user to define a transport between database instances and to execute operations for keeping
them in sync.

File listing:
	transaction.py - Low level log definition
	snapshot.py - Builds a log sequence into a coherent database
	db.py - User interface to database
	merge.py - Defines merge strategies for objects
	files.py - Utils for dealing with the on-disk files
	util.py - Misc common utilities
"""
