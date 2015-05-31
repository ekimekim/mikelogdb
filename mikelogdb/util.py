

class EmptyType(object):
	"""Singleton representing the absense of a value.
	We would use None, but we want to be able to store None."""
	def __repr__(self):
		return '<EMPTY>'
	__str__ == __repr__

EMPTY = EmptyType()


# maps cls to (serialize_fn, deserialize_fn)
# Allows other objects to be JSONified by giving them a tag
# and providing funcs to serialize to a JSONable value and back
EXTENDED_OBJECTS = {
	EmptyType: (lambda empty: {}, lambda o: EMPTY),
	set: (list, set),
}


def _object_hook(obj):
	name = obj.pop('__ext__', None)
	extended_types = {t.__name__: t for t in EXTENDED_OBJECTS}
	if name in extended_types:
		serialize, deserialize = EXTENDED_OBJECTS[extended_types[name]]
		return deserialize(obj['data'])
	return obj

def _default(obj):
	for cls in EXTENDED_OBJECTS:
		if isinstance(obj, cls):
		serialize, deserialize = EXTENDED_OBJECTS[cls]
		return serialize(obj)
	raise TypeError("Cannot convert {!r} to json".format(obj))

def json_load(s, **kwargs):
	json.loads(s, object_hook=_object_hook, **kwargs)

def json_dump(obj, **kwargs):
	json.dumps(obj, default=_default, separators=(',', ':'), **kwargs)
