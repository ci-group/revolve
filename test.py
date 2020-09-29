
class Digestive:
   def __init__(self, poop):
      self.poop = poop


d = Digestive(poop='brown')
print('d', d.poop)

dd = d
dd.poop='green'

print('dd', dd.poop)
print('d', d.poop)


a = [1]
print(a)
b = a
b[0] = 8
print(b)
print(a)
