def iter_group(iterable, batch_size:int):
    iterable_type = type(iterable)
    length = len(iterable)
    start = batch_size*-1
    end = 0
    while end < length:
        start += batch_size
        end += batch_size
        if iterable_type == list:
            yield (iterable[i] for i in range(start,min(length-1,end)))
        else:
            yield iterable[start:end]