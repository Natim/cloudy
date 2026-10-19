"""
Pure computing functions (that's sigmas and loops).
"""

from datetime import datetime


def printtree(d, indent=0):
    for key, value in d.items():
        print("\t" * indent + str(key))
        if isinstance(value, dict):
            printtree(value, indent + 1)
        else:
            print("\t" * (indent + 1) + str(value))


def traversal(original_object, path):
    """
    This function grab the attribute at the given path starting from the
    original object.

    >>> class A:
    ...     item1 = "hello"
    >>> class B:
    ...     item2 = A()
    >>> traversal(B(), 'item2.item1')
    "hello"
    """

    base = original_object
    chunks = path.split(".")

    for chunk in chunks:
        base = getattr(base, chunk)
    return base


def compute_totals(logbook, time_slice=None, filters={}, groupby=None):
    """
    Compute totals of a logbook and store them in database. Of course, the

    :param logbook: must comply with the specifications:
        https://github.com/coulix/cloudy/wiki/Stats
    :param time_slice: must be a couple of two datetime. Please note that we
    strip the hour / minutes / seconds in order to avoid fake duplicates.

    TODO I'm pretty sure that this function should be rewrite using objects
    for rules and functional recursive programming patterns.
    """

    def sum_dicts(source, target):
        """
        This function "sums" two dictionaries: it adds every leaf and automatically
        add the missing ones.

        >>> d1 = {'A': 0, 'C': 4, 'B': {'S': 7, 'R': 3}}
        >>> d2 = {'A': 8, 'D': 0, 'B': {'S': 4, 'F': 2}}
        >>> sum_dicts(d1, d2)
        {'A': 8, 'C': 4, 'B': {'S': 11, 'R': 3, 'F': 2}, 'D': 0}
        """

        if target.__class__ == dict:
            for key, value in target.items():
                if key not in source.keys():
                    source[key] = value
                else:
                    source[key] = sum_dicts(source[key], value)
            return source
        else:
            return source + target

    # Clean the time_slice
    part_one = None
    part_two = None

    if not time_slice[0] == None:
        part_one = datetime.fromordinal(time_slice[0].toordinal())
    if not time_slice[1] == None:
        part_two = datetime.fromordinal(time_slice[1].toordinal())

    time_slice = (part_one, part_two)

    # Get ready with the ruleset
    ruleset = logbook.totals_rules()
    keys = [rule[0] for rule in ruleset]
    results = dict.fromkeys(keys)

    # Grabs the logs corresponding to that logbook
    logs = logbook.active_logs(time_slice, filters)

    # Let's build a complete dict representing the results which will be filled
    # when bulk processing the log entries.

    tree = dict.fromkeys(keys)

    for rule in ruleset:
        tree[rule[0]] = {"__sum__": 0}
        if len(rule) > 2:
            if not groupby == None:
                for groupby in rule[2]:
                    tree[rule[0]][groupby] = {"__sum__": 0}

    # Let's construct an alternate ruleset in order to cache the totals
    # / fields reference type

    fields_related_computations = {}
    final_add = []

    for rule in ruleset:
        # Already computed totals to add at the end of the current computation.
        to_add = []
        fields_refs = []

        # We are going to prefilter data types
        for data_name in rule[1]:
            if data_name in keys:
                # This is a total
                if results[data_name] == None:
                    raise Exception(
                        "Bad ruleset order (%s depends on %s which has not been processed yet.)"
                        % (rule[0], data_name)
                    )
                to_add.append(data_name)
            else:
                # This is a reference to a log item
                if data_name not in fields_related_computations.keys():
                    fields_related_computations[data_name] = [rule[0]]
                else:
                    fields_related_computations[data_name].append(rule[0])

        final_add.append((rule[0], to_add))
        results[rule[0]] = 0

    # Fill everything with zeros
    for key in results.keys():
        results[key] = 0

    # Now that we have our rules, we can batch process log entries
    for log in logs:
        for field, totals in fields_related_computations.items():
            # We grab the value in the log entry
            data = traversal(log, field)

            # For each total field
            for total in totals:
                # For each groupby key in that total
                # pprint(tree[total])
                for groupby in tree[total].keys():
                    # Get the value of the groupby for the actual log entry
                    # using the traversal.

                    if groupby == "__sum__":
                        continue

                    groupby_value = traversal(log, groupby)

                    # We need to create it if it does not exist.
                    exists = tree[total][groupby].get(groupby_value, None)
                    if exists == None:
                        tree[total][groupby][groupby_value] = 0

                    # Finally add the data
                    tree[total][groupby][groupby_value] += data

                tree[total]["__sum__"] += data

    # Now that we proceeded each logs we add the final data
    for element in final_add:
        for item in element[1]:
            tree[element[0]] = sum_dicts(tree[element[0]], tree[item])

    # FIXME I am here for debugging.
    # printtree(tree)

    # Mongodb does not support tuple keys (despite the fact the field name is
    # DictField.. doh) so lets convert it to a string.
    time_slice_string = time_slice_to_string(time_slice)

    # Append the filters to generate a unique key

    unique_key = gen_key(time_slice, filters)

    # Let us save our hard work
    # FIXME no need because we don't cache. *sigh*
    # logbook._totals[unique_key] = tree
    # logbook.save()

    return {unique_key: tree}
    # return logbook._totals


def dict_to_string(dictionary):
    """
    Create a nice string representation for the given dictionary.

    >>> md = {'a': 4, 'b': 'foo', 'c': 'sample'}
    >>> dict_to_string(md)
    "a=4&b=foo&c=sample"
    """
    string = ""
    for key, value in dictionary.items():
        string = f"{string}&{key}={value}"
    return string


def time_slice_to_string(time_slice):
    """
    This function transforms a time slice (ie a couple of datetime objects) to a
    clean string representation.
    We use it in order to store time_slices as keys in the database.
    """

    if time_slice == None or (time_slice[0] == None and time_slice[1]):
        return "None"

    return "%s;%s" % tuple(map(lambda x: "None" if x == None else x.strftime("%Y/%m/%d"), time_slice))


def gen_key(time_slice, filters):
    return f"{time_slice_to_string(time_slice)}{dict_to_string(filters)}"
